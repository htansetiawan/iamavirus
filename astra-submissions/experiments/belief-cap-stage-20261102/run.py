#!/usr/bin/env python3
"""Capture a timed belief update once per attempt; replay its exact state offline."""
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
OUT = ROOT / 'astra-submissions/analysis/belief-cap-stage-20261102'
BUILD = HERE / 'build'
BASE = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base'
REPLAY = ROOT / 'data/raw/games/9ospae7x/replay.json'
sys.path[:0] = [str(ROOT), str(ROOT / 'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol
from learning.compare_archives import kill_tree


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def compile_logged(name, command, cwd):
    r = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=60)
    (OUT / (name + '.log')).write_text(r.stdout + r.stderr)
    r.check_returncode()


def prepare():
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    # Only read the existing unmodified v37 extraction; all edits are local.
    capture = BUILD / 'capture'; capture.mkdir()
    shutil.copytree(BASE / 'src', capture / 'src')
    shutil.copy2(BASE / 'build.sh', capture / 'build.sh')
    compile_logged('original-build', ['bash', 'build.sh'], capture)
    assert sha(capture / 'mist') == sha(BASE / 'mist') == '14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    before = (capture / 'src/main.c').read_text()
    first, rest = before.split('\n', 1)
    assert first.startswith('#define _POSIX_C_SOURCE ')
    after = first + '\n#include "snapshot.h"\n' + rest
    changes = [
        ('                    const size_t afford =', '                    snapshot_at(&b, views - 1, "pre_clock");\n                    const size_t afford ='),
        ('                    const size_t parents = b.count;', '                    snapshot_at(&b, views - 1, "pre_expand");\n                    const size_t parents = b.count;'),
        ('                    belief_after_opponent(&b, view);', '                    belief_after_opponent(&b, view);\n                    snapshot_at(&b, views - 1, "post_expand");')]
    for old, new in changes:
        assert after.count(old) == 1
        after = after.replace(old, new)
    (capture / 'src/main.c').write_text(after)
    shutil.copy2(HERE / 'snapshot.h', capture / 'src/snapshot.h')
    (OUT / 'capture.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), 'a/src/main.c', 'b/src/main.c')))
    compile_logged('capture-build', ['bash', 'build.sh'], capture)

    observer = BUILD / 'observer'; shutil.copytree(BASE / 'src', observer)
    before = (observer / 'belief.c').read_text()
    needle = 'typedef struct { uint64_t key; uint32_t parent; Move move; float logw; } Candidate;'
    assert before.count(needle) == 1
    after = '#include <assert.h>\n' + before.replace(needle, needle + '\n' + (HERE / 'observer.inc').read_text())
    needle = '    /* past the cap: weighted sampling without replacement (exponential keys) */'
    assert after.count(needle) == 1
    after = after.replace(needle, '    astra_stage_candidates(b, cand, m, NULL, m, "before_cap");\n' + needle)
    needle = '    /* pass 2: rebuild the kept positions with their histories */'
    assert after.count(needle) == 1
    after = after.replace(needle, '    astra_stage_candidates(b, cand, m, chosen, keep, "after_cap");\n' + needle)
    (observer / 'belief.c').write_text(after)
    (OUT / 'observer.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), 'a/src/belief.c', 'b/src/belief.c')))
    for name, directory in [('reference', BASE / 'src'), ('observer', observer)]:
        command = ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L', '-I', str(directory), '-I', str(HERE)]
        if name == 'observer': command.append('-DASTRA_STAGE')
        command += [str(HERE / 'audit.c'), *[str(directory / f) for f in ['board.c', 'belief.c', 'movemodel.c']], '-lm', '-o', str(BUILD / name / 'audit') if name == 'observer' else str(BUILD / 'audit-reference')]
        compile_logged(name + '-build', command, ROOT)
    fixture = BUILD / 'fixture'; fixture.mkdir()
    compile_logged('fixture-build', ['gcc', '-std=c11', '-O2', '-pthread', '-D_POSIX_C_SOURCE=199309L',
        '-I', str(BASE / 'src'), '-I', str(HERE), str(HERE / 'fixture.c'),
        *[str(BASE / 'src' / f) for f in ['board.c', 'belief.c', 'movemodel.c']],
        '-lm', '-o', str(fixture / 'make')], ROOT)
    native = OUT / 'native'; native.mkdir()
    facts = json.loads(call('fixture', [fixture / 'make', fixture], clean_env(), native))
    checks = []
    for kind in ['full', 'capped']:
        for arm, binary in [('reference', BUILD / 'audit-reference'), ('observer', observer / 'audit')]:
            target = fixture / (kind + '-' + arm + '.txt')
            stdout = call(kind + '-' + arm, [binary, fixture / (kind + '.txt'), facts['view'],
                facts['parent'], facts['child'], target], clean_env(), native)
            if arm == 'observer':
                events = [json.loads(line) for line in stdout.splitlines()]
                pre = next(e for e in events if e['phase'] == 'before_cap')
                post = next(e for e in events if e['phase'] == 'after_cap')
                assert pre['truth_placements'] >= 1 and pre['count'] > 1
                assert post['count'] == (pre['count'] if kind == 'full' else 1)
                assert sha(target) == sha(fixture / (kind + '-reference.txt'))
                checks.append(dict(kind=kind, canonical_parity=True, events=events))
    save(OUT / 'native-checks.json', dict(facts=facts, checks=checks))
    replay = json.loads(REPLAY.read_text())
    feed, forced = protocol(replay, 28, 0)
    # End at the new observation, before sending its clock/requesting a move.
    lines = feed.splitlines()
    assert lines[-2] == replay['frames'][28]['white']
    feed = '\n'.join(lines[:-1]) + '\n'
    (OUT / 'input.txt').write_text(feed)
    dependencies = {str(p): sha(p) for p in [Path(__file__), HERE / 'snapshot.h', HERE / 'observer.inc', HERE / 'audit.c', HERE / 'fixture.c', OUT / 'native-checks.json',
        BASE / 'mist', BASE / 'bin/stockfish', BASE / 'data/history.bin', REPLAY,
        capture / 'mist', BUILD / 'audit-reference', observer / 'audit', OUT / 'input.txt',
        ROOT / 'learning/compare_archives.py']}
    for directory in (BASE / 'src', capture / 'src', observer):
        for p in sorted(directory.glob('*.[ch]')): dependencies[str(p)] = sha(p)
    plan = dict(created=datetime.now(timezone.utc).isoformat(), dependencies=dependencies,
        case='9ospae7x:28', attempts=3, seed=2231102, cores='2,3', seconds=2.5,
        forced=forced, input_sha256=sha(OUT / 'input.txt'), replay_sha256=sha(REPLAY),
        source_binary_parity=sha(BASE / 'mist'), capture_binary=sha(capture / 'mist'),
        capture_truth_input=False, offline_truth_labels=True, capture_timeout=120,
        offline_timeout=120, address_space_limit_bytes=3 * 1024**3,
        gate='Three first-attempt captures, regardless of observed support. No retries. Each stores pre-clock, pre-expansion and post-expansion belief state at ply28, then ends without a policy choice. Offline reference and observer must reproduce the captured post-expansion canonical bytes exactly. Otherwise stop on a diagnostic integrity failure. No parameter sweep, candidate change or promotion.',
        question='Does a true-placement candidate survive expansion/filtering but disappear at weighted capping? Distinguish from pre-clock or pre-expansion absence.',
        limitations='Selected single-game diagnostic. Recompiled capture and snapshot IO may alter timing relative to arena/222. Exact-state offline replay tests this captured update only. Truth labels match placement; metadata and representative histories are separately retained. Observers run only offline, outside timed engine. Source filtering and prior are unchanged.')
    save(OUT / 'plan.json', plan)
    print(json.dumps({'prepared': True, 'attempts': 3, 'plan_sha256': sha(OUT / 'plan.json')}))


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'OPENBLAS_', 'MKL_'))}
    env.update(MIST_THREADS='2', MIST_MAX_SECONDS='2.5', MIST_TIMING='1',
        MIST_HISTORY_TABLE=str(BASE / 'data/history.bin'), MIST_STOCKFISH=str(BASE / 'bin/stockfish'),
        FOW_SEED='2231102', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return env


def limit_memory():
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))


def call(name, command, env, directory, feed=None, timeout=120):
    start = time.monotonic()
    p = subprocess.Popen(['taskset', '-c', '2,3', *map(str, command)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        start_new_session=True, preexec_fn=limit_memory)
    error = None
    try: stdout, stderr = p.communicate(feed, timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(p.pid); stdout, stderr = p.communicate(); error = 'timeout'
    for suffix, data in [('stdout', stdout), ('stderr', stderr)]:
        with (directory / (name + '.' + suffix)).open('x') as f: f.write(data)
    receipt = dict(name=name, returncode=p.returncode, error=error,
        elapsed=time.monotonic() - start,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
    with (directory / (name + '-receipt.json')).open('x') as f: json.dump(receipt, f, indent=2)
    assert p.returncode == 0 and not error, receipt
    return stdout


def run():
    plan = json.loads((OUT / 'plan.json').read_text())
    for p, h in plan['dependencies'].items(): assert sha(Path(p)) == h, p
    state = dict(started=datetime.now(timezone.utc).isoformat(), status='running', completed=0, pid=os.getpid())
    with (OUT / 'execution.json').open('x') as f: json.dump(state, f)
    replay = json.loads(REPLAY.read_text()); rows = []
    try:
        for attempt in range(plan['attempts']):
            directory = OUT / f'attempt-{attempt}'; directory.mkdir()
            raw = BUILD / f'attempt-{attempt}'; raw.mkdir()
            env = clean_env(); env.update(ASTRA_SNAPSHOT_DIR=str(raw), MIST_FORCE_MOVES=','.join(plan['forced']))
            stdout = call('capture', [BUILD / 'capture/mist'], env, directory, (OUT / 'input.txt').read_text())
            assert stdout.splitlines() == ['ready', *['move ' + m for m in plan['forced']]]
            for name in ['pre_clock', 'pre_expand', 'post_expand']: assert (raw / (name + '.txt')).is_file()
            parent_truth = replay['frames'][27]['board']; child_truth = replay['frames'][28]['board']; view = replay['frames'][28]['white']
            outputs = {}
            for arm, binary in [('reference', BUILD / 'audit-reference'), ('observer', BUILD / 'observer/audit')]:
                target = raw / (arm + '-post.txt')
                outputs[arm] = call(arm, [binary, raw / 'pre_expand.txt', view, parent_truth, child_truth, target], clean_env(), directory)
                assert sha(target) == sha(raw / 'post_expand.txt'), (attempt, arm, 'post-expansion parity')
            snapshots = {}
            for p in sorted(raw.glob('*.txt')):
                compressed = directory / (p.name + '.gz')
                with p.open('rb') as src, gzip.GzipFile(filename=str(compressed), mode='wb', compresslevel=1, mtime=0) as dst: shutil.copyfileobj(src, dst)
                snapshots[p.name] = dict(raw_sha256=sha(p), gzip_sha256=sha(compressed), raw_bytes=p.stat().st_size, gzip_bytes=compressed.stat().st_size)
            events = [json.loads(s) for s in outputs['observer'].splitlines()]
            record = dict(attempt=attempt, canonical_reference_parity=True, canonical_observer_parity=True,
                          events=events, snapshots=snapshots)
            save(directory / 'result.json', record); rows.append(record)
            state['completed'] += 1; save(OUT / 'execution.json', state)
            print(json.dumps({'attempt': attempt, 'parity': True, 'events': events}), flush=True)
        save(OUT / 'summary.json', dict(attempts=rows, scope=plan['limitations']))
        state['status'] = 'complete'
    except BaseException:
        state['status'] = 'failed'; raise
    finally:
        state['ended'] = datetime.now(timezone.utc).isoformat(); save(OUT / 'execution.json', state)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'run')
    globals()[sys.argv[1]]()
