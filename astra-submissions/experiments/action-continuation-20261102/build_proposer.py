"""Read-only root diagnostics on an isolated continuation-engine source copy."""
import difflib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from branch import HERE, ROOT, PRIOR, base

OUT = ROOT/'astra-submissions/analysis/action-continuation-20261102'

HELPER = r'''
/* Read-only diagnostics. Each subtree is visited once across root actions:
 * O(tree edges), not one complete game_value traversal per candidate. */
static double astra_subtree_value(const Game *g, int node, const double *x) {
    const GameNode *n = &g->nodes[node];
    if (n->type == NODE_TERMINAL) return n->value;
    double value = 0;
    for (int a = 0; a < n->count; ++a) {
        const double p = n->type == NODE_CHANCE ? g->prob[n->first+a] : x[g->is_offset[n->infoset]+a];
        if (p > 0) value += p * astra_subtree_value(g, g->child[n->first+a], x);
    }
    return value;
}
'''


def main():
    OUT.mkdir(exist_ok=True)
    dest = HERE/'build'; dest.mkdir(exist_ok=False)
    prior = json.loads((ROOT/'astra-submissions/analysis/private-continuation-20261102/build.json').read_text())
    for path, digest in prior['sources'].items():
        assert base.sha(PRIOR/'build'/path) == digest
    shutil.copytree(PRIOR/'build/src', dest/'src')
    gpath = dest/'src/gtcfr.c'; oldg = gpath.read_text()
    g = oldg.replace('#include <math.h>', '#include <stdio.h>\n#include <math.h>')
    needle = 'int gtcfr_decide(const Belief *b, const GtcfrParams *params, SearchResult *out) {'
    assert g.count(needle) == 1; g = g.replace(needle, HELPER+'\n'+needle)
    needle = '    out->iterations = iteration;'
    assert g.count(needle) == 1
    g = g.replace(needle, needle+r'''
    if (getenv("ASTRA_PROPOSAL")) {
        for (int a = 0; a < ours.count; ++a) {
            double q = 0;
            for (int k = 0; k < K; ++k) {
                const GameNode *n = &t.g.nodes[chance_kids[k]];
                q += chance_p[k] * astra_subtree_value(&t.g, t.g.child[n->first+a], x);
            }
            char move[6]; move_to_uci(ours.moves[a], move);
            fprintf(stderr, "astra-proposal: %s %.17g %.17g\n", move, x[o+a], q);
        }
        fprintf(stderr, "astra-proposal-value: %.17g\n", out->value);
    }
''')
    gpath.write_text(g)
    mpath = dest/'src/main.c'; oldm = mpath.read_text()
    needle = '        view_moves(view, us, front.castle, &allowed);'
    assert oldm.count(needle) == 1
    m = oldm.replace(needle, needle+r'''
        if (getenv("ASTRA_PROPOSAL") && !(forced && *forced)) {
            fprintf(stderr, "astra-view-legal:");
            for (int a = 0; a < allowed.count; ++a) {
                char move[6]; move_to_uci(allowed.moves[a], move);
                fprintf(stderr, " %s", move);
            }
            fprintf(stderr, "\n");
        }
''')
    mpath.write_text(m)
    patch = ''.join(difflib.unified_diff(oldg.splitlines(True),g.splitlines(True),fromfile='241/gtcfr.c',tofile='proposal/gtcfr.c'))
    patch += ''.join(difflib.unified_diff(oldm.splitlines(True),m.splitlines(True),fromfile='241/main.c',tofile='proposal/main.c'))
    (OUT/'proposal.patch').write_text(patch)
    names = ['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
    command = ['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',
               *[str(dest/f'src/{n}.c') for n in names],'-lm','-o',str(dest/'proposer')]
    p = subprocess.run(command, capture_output=True, text=True)
    (OUT/'build.stderr').write_text(p.stderr)
    assert p.returncode == 0, p.stderr
    report = dict(exit=p.returncode, command=command, proposal_binary_sha256=base.sha(dest/'proposer'),
                  continuation_binary_sha256=base.sha(PRIOR/'build/mist'),
                  sources={str(f.relative_to(dest)):base.sha(f) for f in (dest/'src').glob('*') if f.is_file()},
                  patch_sha256=base.sha(OUT/'proposal.patch'),
                  scope='Diagnostics only; continuation runs retain the original 241 binary.')
    with (OUT/'build.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({k:report[k] for k in ('exit','proposal_binary_sha256','continuation_binary_sha256')}))


if __name__ == '__main__':
    main()
