"""Build only an isolated copy; full cost/posterior execution is separate."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/native-quiet-prior-20261110'
BUILD = HERE / 'build'
BASE = HERE.parent / 'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
OLD = HERE.parent / 'capture-fixed-prior-20261110'
MODEL = ROOT / 'astra-submissions/analysis/capture-fixed-prior-20261110/22-quadratic-model.json'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    confirmed = ROOT / 'astra-submissions/analysis/prospective-full-prior-20261110b'
    assert json.loads((confirmed / 'result.json').read_text())['decision'] == 'native_cost_and_posterior_design_allowed'
    assert json.loads((confirmed / 'independent-review.json').read_text())['passed']
    assert sha(MODEL) == '01fd1b947647a90695924b842b3a306eb40add8e0648c952ac93a976287cd62e'
    assert sha(BASE / 'mist') == '14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    shutil.copytree(BASE / 'src', BUILD / 'original')
    shutil.copytree(BASE / 'src', BUILD / 'adapter')
    model = json.loads(MODEL.read_text())
    def floats(values):
        return ','.join(float(v).hex() + 'f' for v in np.asarray(values, dtype=np.float32).flat)
    (BUILD / 'adapter/weights.h').write_text(
        '/* Fixed293 full quadratic, exact float32 hex literals. */\n'
        'static const float astra_fixed_linear[22]={' + floats(model['linear']) + '};\n'
        'static const float astra_fixed_quadratic[484]={' + floats(model['quadratic']) + '};\n')
    original_model = (BASE / 'src/movemodel.c').read_text()
    (BUILD / 'adapter/movemodel.c').write_text(original_model + '\n' + (HERE / 'model_append.c').read_text())
    assert (BUILD / 'adapter/movemodel.c').read_text().startswith(original_model)
    before = (BASE / 'src/belief.c').read_text(); after = before
    edits = [
        ('#include "movemodel.h"', '#include "movemodel.h"\n#include "native_head.h"'),
        ('static int settings_read = 0, model_on = 1, prune_capturable = 1;',
         'static int settings_read = 0, model_on = 1, prune_capturable = 1;\nstatic int astra_quiet_mode = 0;'),
        ('    const char *e;\n', '    const char *e;\n    if ((e = getenv("ASTRA_CAPTURE_FIXED"))) {\n        if (strcmp(e, "0") == 0) astra_quiet_mode = 0;\n        else if (strcmp(e, "1") == 0) astra_quiet_mode = 1;\n        else if (strcmp(e, "2") == 0) astra_quiet_mode = 2;\n        else { fprintf(stderr, "astra: invalid fixed-prior mode\\n"); exit(2); }\n    }\n'),
    ]
    for old, new in edits:
        assert after.count(old) == 1, old; after = after.replace(old, new)
    old = '''            move_logits(&p, &l, b->last_own, w->full, logit);
            float top = -INFINITY;
            for (int j = 0; j < l.count; ++j) if (logit[j] > top) top = logit[j];
            double z = 0;
            for (int j = 0; j < l.count; ++j) z += exp((double)(logit[j] - top));
            log_z = top + (float)log(z);'''
    new = '''            if (w->full && astra_quiet_mode) {
                /* Already normalized by the OLD global normalizer. Keeping
                 * log_z=0 preserves every capture entry before history/temp. */
                astra_full_logp(&p, &l, b->last_own, astra_quiet_mode == 2, logit);
            } else {
                move_logits(&p, &l, b->last_own, w->full, logit);
                float top = -INFINITY;
                for (int j = 0; j < l.count; ++j) if (logit[j] > top) top = logit[j];
                double z = 0;
                for (int j = 0; j < l.count; ++j) z += exp((double)(logit[j] - top));
                log_z = top + (float)log(z);
            }'''
    assert after.count(old) == 1; after = after.replace(old, new)
    (BUILD / 'adapter/belief.c').write_text(after)
    for name in ('belief.c', 'movemodel.c'):
        original = (BASE / 'src' / name).read_text(); modified = (BUILD / 'adapter' / name).read_text()
        (OUT / (name + '.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True), 'a/src/' + name, 'b/src/' + name)))
    flags = ['gcc', '-O2', '-std=c11', '-pthread', '-D_POSIX_C_SOURCE=199309L']
    commands = [flags + ['-shared', '-fPIC', '-I' + str(BUILD / 'adapter'), '-I' + str(HERE), '-I' + str(OLD),
                        str(HERE / 'bridge.c'), str(BUILD / 'adapter/board.c'), str(BUILD / 'adapter/movemodel.c'),
                        '-lm', '-o', str(BUILD / 'adapter.so')]]
    trace = HERE.parent / 'full-prior-posterior-20261102/trace.c'
    for arm in ('original', 'adapter'):
        src = BUILD / arm
        commands.append(flags + ['-I' + str(src), '-I' + str(HERE), '-I' + str(OLD), str(trace),
                                 *[str(src / name) for name in ('board.c', 'belief.c', 'movemodel.c')],
                                 '-lm', '-o', str(BUILD / ('trace-' + arm))])
    receipts = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        receipts.append(dict(command=command, code=result.returncode, stdout=result.stdout, stderr=result.stderr))
        assert result.returncode == 0, result.stderr
    dependencies = [*HERE.glob('*.[ch]'), Path(__file__), OLD / 'quiet.h', MODEL, trace,
                    BASE / 'data/history.bin', BASE / 'mist', confirmed / 'result.json', confirmed / 'independent-review.json']
    dependencies += list((BASE / 'src').glob('*.[ch]')) + list((BUILD / 'adapter').glob('*.[ch]'))
    dependencies += [BUILD / name for name in ('adapter.so', 'trace-original', 'trace-adapter')]
    save(OUT / 'build.json', dict(at=datetime.now(timezone.utc).isoformat(), passed=True, commands=receipts,
                                dependencies={str(path): sha(path) for path in dependencies},
                                scope='Native adapter construction only. No measured cost, posterior quality, playing candidate or live source change.'))
    print(json.dumps(dict(built=True, commands=len(commands), dependencies=len(dependencies))), flush=True)


if __name__ == '__main__': main()
