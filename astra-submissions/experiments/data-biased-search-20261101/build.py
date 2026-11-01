#!/usr/bin/env python3
"""Patch an immutable v37 copy; never touch Fable's core checkout."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent/'stable-mix-20261101/build/base'
ARCHIVE = ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
ARCHIVE_SHA = '41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace(s, a, b):
    assert s.count(a) == 1, (a[:100], s.count(a))
    return s.replace(a, b)


def main():
    assert sha(ARCHIVE) == ARCHIVE_SHA
    build = HERE/'build'; build.mkdir(exist_ok=False)
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in z.namelist():
            if name.startswith('src/') and not name.endswith('/'):
                assert '..' not in Path(name).parts
                p = build/name; p.parent.mkdir(exist_ok=True, parents=True)
                p.write_bytes(z.read(name))
        (build/'build.sh').write_bytes(z.read('build.sh'))
    for name in ('bin', 'data'):
        (build/name).symlink_to(BASE/name, target_is_directory=True)
    originals = {p.name: p.read_text() for p in (build/'src').glob('*') if p.suffix in ('.c', '.h')}
    s = originals['cfr.h']
    s = replace(s, '    int root;', '    double *confidence, *fixed_policy; int cap_fixed; /* optional per-infoset restriction */\n    int root;')
    s = replace(s, 'void game_finalize(Game *g);', 'void game_restrict(Game *g, int I, double confidence, const double *policy);\nvoid game_finalize(Game *g);')
    (build/'src/cfr.h').write_text(s)
    s = originals['cfr.c']
    s = replace(s, '#include <math.h>', '#include <assert.h>\n#include <math.h>')
    s = replace(s, '    free(g->pending);', '    free(g->pending); free(g->confidence); free(g->fixed_policy);')
    s = replace(s, '        g->is_offset = realloc(g->is_offset, g->cap_infosets * sizeof(int));',
                '        g->is_offset = realloc(g->is_offset, g->cap_infosets * sizeof(int));\n        g->confidence = realloc(g->confidence, g->cap_infosets * sizeof(double));')
    s = replace(s, '    g->is_player[g->n_infosets] = player;', '    g->confidence[g->n_infosets] = 0;\n    g->is_player[g->n_infosets] = player;')
    anchor = 'static void apply_pending(Game *g);'
    addition = '''void game_restrict(Game *g, int I, double confidence, const double *policy) {
    assert(I >= 0 && I < g->n_infosets && isfinite(confidence) && confidence >= 0 && confidence <= 1);
    const int n = g->is_actions[I], o = g->is_offset[I];
    double total = 0;
    for (int a = 0; a < n; ++a) { assert(isfinite(policy[a]) && policy[a] >= 0); total += policy[a]; }
    assert(fabs(total - 1) < 1e-9);
    if (o + n > g->cap_fixed) {
        int cap = g->cap_fixed ? g->cap_fixed : 64;
        while (cap < o + n) cap *= 2;
        g->fixed_policy = realloc(g->fixed_policy, cap * sizeof(double));
        memset(g->fixed_policy + g->cap_fixed, 0, (cap - g->cap_fixed) * sizeof(double));
        g->cap_fixed = cap;
    }
    memcpy(g->fixed_policy + o, policy, n * sizeof(double));
    g->confidence[I] = confidence;
}

'''
    s = replace(s, anchor, addition+anchor)
    anchor = '    for (int a = 0; a < n; ++a) x[a] = total > 0 ? x[a] / total : 1.0 / n;'
    s = replace(s, anchor, anchor+'\n    const double c = g->confidence[I];\n    if (c > 0) for (int a = 0; a < n; ++a) x[a] = (1-c)*x[a] + c*g->fixed_policy[o+a];')
    anchor = '        for (int a = 0; a < n; ++a) out[o + a] = total > 0 ? g->strategy_sum[o + a] / total : 1.0 / n;'
    s = replace(s, anchor, anchor+'\n        if (total == 0 && g->confidence[I] > 0)\n            for (int a = 0; a < n; ++a) out[o+a] = (1-g->confidence[I])/n + g->confidence[I]*g->fixed_policy[o+a];')
    # Restriction affects solver regrets only. Best-response diagnostics stay unrestricted.
    s = replace(s, 'const double *x, double *inst) {', 'const double *x, double *inst, int constrained) {')
    s = s.replace('reach_others * p, x, inst)', 'reach_others * p, x, inst, constrained)')
    s = s.replace('reach_others * pa, x, inst)', 'reach_others * pa, x, inst, constrained)')
    s = s.replace('reach_others, x, inst)', 'reach_others, x, inst, constrained)')
    s = replace(s, '    for (int a = 0; a < n->count; ++a) inst[o + a] += reach_others * (vals[a] - v);', '''    const double c = constrained ? g->confidence[I] : 0;
    if (c == 0) {
        for (int a = 0; a < n->count; ++a) inst[o + a] += reach_others * (vals[a] - v);
    } else if (c < 1) {
        double fixed_v = 0;
        for (int a = 0; a < n->count; ++a) fixed_v += g->fixed_policy[o+a] * vals[a];
        const double free_v = (v - c*fixed_v)/(1-c);
        for (int a = 0; a < n->count; ++a)
            inst[o+a] += reach_others * (1-c) * (vals[a] - free_v);
    }''')
    # Two callers: one is the iteration, one is the ordinary best response.
    call = 'traverse(g, g->root, player, 1.0, x, inst);'
    assert s.count(call) == 2
    s = s.replace(call, 'traverse(g, g->root, player, 1.0, x, inst, 1);', 1)
    s = s.replace(call, 'traverse(g, g->root, player, 1.0, x, inst, 0);', 1)
    (build/'src/cfr.c').write_text(s)
    p = build/'src/belief.h';s=p.read_text()
    s = replace(s, 'void belief_history_stats(', 'unsigned belief_history_counts(uint64_t h, const MoveList *l, unsigned *counts);\nvoid belief_history_stats(')
    p.write_text(s)
    p = build/'src/belief.c';p.write_text(p.read_text()+'''\n/* Read-only access for the isolated data-biased search experiment. */
unsigned belief_history_counts(uint64_t h, const MoveList *l, unsigned *counts) {
    read_settings();
    return history_counts(h, l, counts);
}
''')
    p=build/'src/gtcfr.c';s=p.read_text()
    s=replace(s, '/* Turns leaf `index` into a decision node of its side to move. */', '#include "dbr.h"\n\n/* Turns leaf `index` into a decision node of its side to move. */')
    s=replace(s, '    const int I = infoset_for(t, player, leaf.hist[player], count);',
              '    const int I = infoset_for(t, player, leaf.hist[player], count);\n    if (t->g.n_infosets > before) dbr_install(t, I, &leaf);')
    s=replace(s, '    free(x); free(idx); free(share); free(chance_kids); free(chance_p);',
              '    dbr_report(&t, x);\n    free(x); free(idx); free(share); free(chance_kids); free(chance_p);')
    p.write_text(s);shutil.copyfile(HERE/'dbr.h',build/'src/dbr.h')
    patch=[]
    for name,before in originals.items():
        after=(build/'src'/name).read_text()
        if before!=after:patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/'+name,tofile='b/src/'+name))
    (HERE/'patch.diff').write_text(''.join(patch))
    r=subprocess.run(['bash','build.sh'],cwd=build,capture_output=True,text=True)
    (HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    pins={'archive_sha256':ARCHIVE_SHA,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'build.py',HERE/'dbr.h',HERE/'patch.diff',*sorted((build/'src').glob('*'))]},
          'binary_sha256':sha(build/'mist'),'stockfish_sha256':sha(BASE/'bin/stockfish'),'history_sha256':sha(BASE/'data/history.bin')}
    (HERE/'provenance.json').write_text(json.dumps(pins,indent=2)+'\n')
    print(json.dumps({'binary':pins['binary_sha256'],'changed_files':len([x for x in patch if x.startswith('---')])}))


if __name__=='__main__': main()
