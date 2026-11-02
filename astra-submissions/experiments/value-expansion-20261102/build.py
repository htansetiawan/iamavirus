from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/value-expansion-20261102'


def replace(s, old, new, expected=1):
    assert s.count(old) == expected, (old[:80], s.count(old))
    return s.replace(old, new)


def main():
    base = HERE / 'build/base'
    candidate = HERE / 'build/candidate'
    archive = ROOT / 'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == '41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
    with zipfile.ZipFile(archive) as z:
        prefix = next(n[:-len('src/gtcfr.c')] for n in z.namelist() if n.endswith('src/gtcfr.c'))
        for info in z.infolist():
            if info.is_dir(): continue
            rel = info.filename[len(prefix):]
            if not (rel.startswith('src/') or rel in ('build.sh', 'run.sh', 'bin/stockfish', 'data/history.bin')): continue
            target = base / rel
            assert '..' not in Path(rel).parts and not Path(rel).is_absolute()
            payload = z.read(info)
            if target.exists(): assert target.read_bytes() == payload, target
            else:
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
            if rel == 'bin/stockfish': target.chmod(0o755)
    shutil.copytree(base, candidate, dirs_exist_ok=True)
    original = (base / 'src/gtcfr.c').read_text()
    assert original == (HERE / 'gtcfr.original.c').read_text()
    s = replace(original, '#include "gtcfr.h"', '#include "gtcfr.h"\n#include "expansion_values.h"\n#include <stdio.h>')
    s = replace(s, '    int cap_visits;', '''    int cap_visits;
    int value_expansion;
    ExpansionValues ev;
    ExpansionMoment *moments;
    uint64_t q_scored, q_fallback, q_visits;
    double q_seconds;''')
    s = replace(s, 'static unsigned long long next_random', '''static void refresh_expansion(Tree *t, const double *x) {
    if (!t->value_expansion) return;
    struct timespec start; clock_gettime(CLOCK_MONOTONIC, &start);
    expansion_values_refresh(&t->ev, &t->g, x);
    t->q_seconds += seconds_since(&start);
}

static unsigned long long next_random''')
    s = replace(s, '    memset(t->visits + old, 0, (t->cap_visits - old) * sizeof(int));', '''    memset(t->visits + old, 0, (t->cap_visits - old) * sizeof(int));
    if (t->value_expansion) {
        t->moments = realloc(t->moments, (size_t)t->cap_visits * sizeof(ExpansionMoment));
        if (!t->moments) abort();
        for (int a = old; a < t->cap_visits; ++a) expansion_moment_init(&t->moments[a]);
    }''')
    s = replace(s, '            if (n->player == explorer) {', '''            const int have_q = t->value_expansion &&
                expansion_values_available(&t->ev, n->infoset, o, n->count);
            if (n->player == explorer) {''')
    s = replace(s, '                    double best = -1;', '                    double best = -INFINITY;')
    s = replace(s, '                        const double score = xs[a] + sqrt((double)total + 1.0) / (1.0 + t->visits[o + a]);', '''                        const double score = have_q
                            ? expansion_score(t->ev.q[o + a], &t->moments[o + a], (uint64_t)total,
                                              (uint64_t)t->visits[o + a])
                            : xs[a] + sqrt((double)total + 1.0) / (1.0 + t->visits[o + a]);''')
    s = replace(s, '                    /* PUCT: current strategy as the prior, visit bonus */', '''                    /* Conditional value + variance bonus when available;
                     * original rule for a new or zero-CF-reach infoset. */
                    if (t->value_expansion) {
                        if (have_q) ++t->q_scored; else ++t->q_fallback;
                    }''')
    s = replace(s, '            t->visits[o + pick] += 1;', '''            /* Record this visit after selection: the score uses past visits.
             * One conditional value vector is shared by every history in I. */
            if (have_q) {
                for (int a = 0; a < n->count; ++a)
                    expansion_moment_add(&t->moments[o + a], t->ev.q[o + a]);
                ++t->q_visits;
            }
            t->visits[o + pick] += 1;''')
    s = replace(s, '    game_init(&t.g); t.us = b->us;', '''    t.value_expansion = getenv("MIST_EXPANSION_Q") && atoi(getenv("MIST_EXPANSION_Q")) != 0;
    game_init(&t.g); t.us = b->us;''')
    # Exactly the strategy refresh sites used by selection, excluding final
    # output-only current-strategy extraction after the last solver passes.
    s = replace(s, '        pcfr_current(&t.g, x);\n        int x_slots', '        pcfr_current(&t.g, x);\n        refresh_expansion(&t, x);\n        int x_slots')
    s = replace(s, '                pcfr_current(&t.g, x);\n                x_slots', '                pcfr_current(&t.g, x);\n                refresh_expansion(&t, x);\n                x_slots')
    s = replace(s, '        pcfr_current(&t.g, x);\n        const int x_slots', '        pcfr_current(&t.g, x);\n        refresh_expansion(&t, x);\n        const int x_slots')
    s = replace(s, '    free(t.leaves); free(t.leaf_of); free(t.keys); free(t.vals); free(t.visits);', '''    if (t.value_expansion)
        fprintf(stderr, "astra-expansion-q refreshes=%llu scored=%llu fallback=%llu visits=%llu recall_failures=%llu nodes_visited=%llu seconds=%.6f\\n",
                (unsigned long long)t.ev.refreshes, (unsigned long long)t.q_scored,
                (unsigned long long)t.q_fallback, (unsigned long long)t.q_visits,
                (unsigned long long)t.ev.recall_failures, (unsigned long long)t.ev.nodes, t.q_seconds);
    expansion_values_free(&t.ev); free(t.moments);
    free(t.leaves); free(t.leaf_of); free(t.keys); free(t.vals); free(t.visits);''')
    (candidate / 'src/gtcfr.c').write_text(s)
    for name in ('expansion_values.c', 'expansion_values.h'):
        shutil.copyfile(HERE / name, candidate / 'src' / name)
    (OUT / 'candidate.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), s.splitlines(True), fromfile='v37/src/gtcfr.c', tofile='candidate/src/gtcfr.c')))
    build_script = (base / 'build.sh').read_text()
    (candidate / 'build.sh').write_text(replace(build_script, 'src/gtcfr.c', 'src/gtcfr.c src/expansion_values.c'))
    for directory in (base, candidate):
        cmd = ['bash', 'build.sh']
        r = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=120)
        (OUT / f'build-{directory.name}.log').write_text(r.stdout + r.stderr)
        r.check_returncode()
    pins = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in (base, candidate) for p in [*sorted((directory / 'src').glob('*')), directory / 'mist'] if p.is_file()}
    (OUT / 'build-pins.json').write_text(json.dumps(pins, indent=2) + '\n')
    print(json.dumps({'source_files': len(pins), 'base': pins[str((base/'mist').relative_to(ROOT))], 'candidate': pins[str((candidate/'mist').relative_to(ROOT))]}))


if __name__ == '__main__': main()
