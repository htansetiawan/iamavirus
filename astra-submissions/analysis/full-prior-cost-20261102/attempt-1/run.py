#!/usr/bin/env python3
"""Isolated exactness/cost test before enabling the full prior on large beliefs."""
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/full-prior-cost-20261102'
BUILD = HERE / 'build'
BASE = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base'
CAP_SOURCE = HERE.parent / 'belief-cap-stage-20261102'
CAP = ROOT / 'astra-submissions/analysis/belief-cap-stage-20261102'
MIST = ROOT.parent / 'fowsearch-c'
REPLAY = ROOT / 'data/raw/games/9ospae7x/replay.json'
sys.path.insert(0, str(ROOT))
from learning.compare_archives import kill_tree

ARMS = ('original', 'fast', 'sparse')


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, obj): p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
def unique(p, obj):
    with p.open('x') as f: json.dump(obj, f, indent=2, allow_nan=False); f.write('\n')


def env(mode='ordinary'):
    e = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_', 'OMP_', 'OPENBLAS_', 'MKL_'))}
    e.update(MIST_THREADS='2', MIST_MODEL_TEMP='2', MIST_MODEL_FULL_BELOW='10000' if mode == 'ordinary' else '1000000000',
             MIST_HISTORY_TABLE=str(BASE / 'data/history.bin'), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return e


def limits(): resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))


def call(name, command, *, cwd=ROOT, environment=None, timeout=120, input_text=None):
    start = time.monotonic()
    p = subprocess.Popen(list(map(str, command)), cwd=cwd, env=environment or env(), text=True,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         preexec_fn=limits, start_new_session=True)
    error = None
    try: stdout, stderr = p.communicate(input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(p.pid); stdout, stderr = p.communicate(); error = 'timeout'
    for suffix, text in [('stdout', stdout), ('stderr', stderr)]:
        with (OUT / (name + '.' + suffix)).open('x') as f: f.write(text)
    receipt = dict(command=list(map(str, command)), returncode=p.returncode, error=error, elapsed=time.monotonic() - start,
                   stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(), stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
    unique(OUT / (name + '-receipt.json'), receipt)
    assert p.returncode == 0 and error is None, receipt
    return stdout


def prepare():
    os.sched_setaffinity(0, {2, 3}); BUILD.mkdir(exist_ok=False)
    assert sha(BASE / 'mist') == '14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    for arm in ARMS:
        (BUILD / arm).mkdir(); shutil.copytree(BASE / 'src', BUILD / arm / 'src')
    patches = []
    for commit, filename in [('14b22e9f190f063e88c1131e9a7ca51934088c17', 'board.c'), ('382cbd25201e48ba17c2c02ce7f9cf9ac0a0d957', 'belief.c')]:
        patch = subprocess.check_output(['git', '-C', str(MIST), 'diff', commit + '^', commit, '--', 'src/' + filename], text=True)
        assert patch.startswith('diff --git ')
        path = OUT / (commit[:7] + '.patch'); path.write_text(patch); patches.append(path)
        for arm in ('fast', 'sparse'):
            call('apply-' + arm + '-' + commit[:7], ['patch', '--batch', '--fuzz=0', '-p1'], cwd=BUILD / arm, input_text=patch)
    model = BUILD / 'sparse/src/movemodel.c'; before = model.read_text(); after = before
    declaration = 'static void move_features_needed(const Position *, Move, Move, int, int, float *);\n\n'
    needle = 'void move_logits(const Position *p,'; assert after.count(needle) == 1
    after = after.replace(needle, declaration + needle)
    needle = '        move_features(p, l->moves[i], previous, full, x);'; assert after.count(needle) == 1
    after = after.replace(needle, '        move_features_needed(p, l->moves[i], previous, full,\n            theta[MM_CHECK_UNSEEN] != 0 || theta[MM_THREAT_UNSEEN] != 0, x);')
    needle = 'void move_features(const Position *p, Move m, Move previous, int full, float out[MM_FEATURES]) {'
    assert after.count(needle) == 1
    after = after.replace(needle, 'static void move_features_needed(const Position *p, Move m, Move previous, int full, int hidden, float out[MM_FEATURES]) {')
    needle = '    {\n        /* what the victim sees after the move:'; assert after.count(needle) == 1
    after = after.replace(needle, '    if (hidden) {\n        /* what the victim sees after the move:')
    after += '\nvoid move_features(const Position *p, Move m, Move previous, int full, float out[MM_FEATURES]) {\n    move_features_needed(p, m, previous, full, 1, out);\n}\n'
    model.write_text(after)
    (OUT / 'zero-feature-scoring.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), 'a/src/movemodel.c', 'b/src/movemodel.c')))
    cap = json.loads((CAP / 'summary.json').read_text()); snapshots = []
    for attempt in cap['attempts']:
        i = attempt['attempt']; source = CAP / f'attempt-{i}/pre_expand.txt.gz'
        assert sha(source) == attempt['snapshots']['pre_expand.txt']['gzip_sha256']
        raw = BUILD / f'input-{i}.txt'; raw.write_bytes(gzip.decompress(source.read_bytes()))
        assert sha(raw) == attempt['snapshots']['pre_expand.txt']['raw_sha256']
        snapshots.append(dict(attempt=i, source=str(source), source_sha256=sha(source), path=str(raw), sha256=sha(raw),
                              ordinary_post_sha256=attempt['snapshots']['post_expand.txt']['raw_sha256']))
    flags = ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L']
    for arm in ARMS:
        src = BUILD / arm / 'src'
        call('build-' + arm, flags + ['-I', src, '-I', CAP_SOURCE, HERE / 'bench.c',
             *[src / n for n in ('board.c', 'belief.c', 'movemodel.c')], '-lm', '-o', BUILD / arm / 'bench'])
    # Original feature exporter compiled under distinct public symbols.
    call('reference-model-build', flags + ['-I', BASE / 'src', '-Dmove_logits=reference_move_logits',
        '-Dmove_features=reference_move_features', '-c', BASE / 'src/movemodel.c', '-o', BUILD / 'reference-model.o'])
    src = BUILD / 'sparse/src'
    call('model-parity-build', flags + ['-I', src, '-I', CAP_SOURCE, HERE / 'model_parity.c', BUILD / 'reference-model.o',
        *[src / n for n in ('board.c', 'belief.c', 'movemodel.c')], '-lm', '-o', BUILD / 'model-parity'])
    parity = json.loads(call('model-parity', [BUILD / 'model-parity', snapshots[0]['path']]))
    tests = BUILD / 'fast/tests'; tests.mkdir()
    for name in ('test_bb.c', 'ref_board.c', 'vectors.txt'):
        payload = subprocess.check_output(['git', '-C', str(MIST), 'show', '14b22e9:tests/' + name])
        (tests / name).write_bytes(payload)
    call('rules-build', flags + [tests / 'test_bb.c', tests / 'ref_board.c', BUILD / 'fast/src/board.c', '-o', BUILD / 'rules-parity'])
    rules = call('rules-parity', [BUILD / 'rules-parity', tests / 'vectors.txt'])
    assert 'mismatches 0' in rules
    unique(OUT / 'preflight.json', dict(model_parity=parity, rules=rules))
    jobs = []
    arms = [(a, m) for m in ('ordinary', 'full') for a in ARMS]
    for i in range(3):
        order = arms[i:] + arms[:i]
        for a, m in order: jobs.append(dict(attempt=i, arm=a, mode=m, name=f'state-{i}-{a}-{m}'))
    deps = [Path(__file__), HERE / 'bench.c', HERE / 'model_parity.c', HERE / 'README.md', CAP_SOURCE / 'snapshot.h',
            BASE / 'mist', BASE / 'data/history.bin', REPLAY, OUT / 'preflight.json', *patches,
            OUT / 'zero-feature-scoring.patch', ROOT / 'learning/compare_archives.py']
    for arm in ARMS: deps += list((BUILD / arm / 'src').glob('*.[ch]')) + [BUILD / arm / 'bench']
    deps += [Path(s['path']) for s in snapshots]
    plan = dict(created=now(), dependencies={str(p): sha(p) for p in deps}, jobs=jobs, snapshots=snapshots,
                gate=dict(median_sparse_full_over_original_ordinary_at_most=1.5, sparse_full_max_seconds=1.0, all_parity=True),
                threads=2, cores=[2, 3], child_wall_seconds=120, child_address_space_limit=3 * 1024**3,
                label_scope='Truth is read only after each timed update; one selected-game mechanism/cost test, not posterior calibration or strength.',
                before_any_run='Publish this plan and all patches/preflight evidence before the18 first-attempt calls.')
    unique(OUT / 'plan.json', plan)
    print(json.dumps(dict(preflight=parity, plan_sha256=sha(OUT / 'plan.json'), cells=len(jobs))), flush=True)


def run():
    plan = json.loads((OUT / 'plan.json').read_text()); os.sched_setaffinity(0, set(plan['cores']))
    for p, h in plan['dependencies'].items(): assert sha(Path(p)) == h, p
    state = dict(started=now(), pid=os.getpid(), status='running', completed=0, plan_sha256=sha(OUT / 'plan.json'))
    unique(OUT / 'execution.json', state); results = []
    frame = json.loads(REPLAY.read_text())['frames'][28]
    try:
        for job in plan['jobs']:
            target = BUILD / (job['name'] + '.txt'); assert not target.exists()
            source = plan['snapshots'][job['attempt']]
            output = call(job['name'], [BUILD / job['arm'] / 'bench', source['path'], frame['white'], frame['board'], target], environment=env(job['mode']))
            result = dict(**job, **json.loads(output), canonical_sha256=sha(target)); results.append(result)
            unique(OUT / (job['name'] + '-result.json'), result)
            if job['mode'] == 'ordinary': assert result['canonical_sha256'] == source['ordinary_post_sha256'], result
            peers = [r for r in results if r['attempt'] == job['attempt'] and r['mode'] == job['mode']]
            assert len({r['canonical_sha256'] for r in peers}) == 1, peers
            state['completed'] += 1; save(OUT / 'execution.json', state); print(json.dumps(result), flush=True)
        ratios = []
        for i in range(3):
            def pick(a, m): return next(r for r in results if r['attempt'] == i and r['arm'] == a and r['mode'] == m)
            ratios.append(pick('sparse', 'full')['update_seconds'] / pick('original', 'ordinary')['update_seconds'])
        median = sorted(ratios)[1]; maximum = max(r['update_seconds'] for r in results if r['arm'] == 'sparse' and r['mode'] == 'full')
        advance = median <= plan['gate']['median_sparse_full_over_original_ordinary_at_most'] and maximum <= plan['gate']['sparse_full_max_seconds']
        report = dict(results=results, paired_ratios=ratios, median_ratio=median, sparse_full_max_seconds=maximum,
                      all_canonical_parity=True, decision='broader_posterior_design_allowed' if advance else 'stop_unconditional_full_at_this_cost',
                      scope=plan['label_scope'])
        unique(OUT / 'result.json', report); state['status'] = 'complete'
    except BaseException as e: state.update(status='failed', error=f'{type(e).__name__}: {e}'); raise
    finally: state['ended'] = now(); save(OUT / 'execution.json', state)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'run')
    globals()[sys.argv[1]]()
