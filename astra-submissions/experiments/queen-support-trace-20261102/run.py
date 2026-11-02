#!/usr/bin/env python3
"""Trace two selected belief failures with the immutable engine's log-only hook."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/queen-support-trace-20261102'
BASE = HERE.parent / 'queen-terminal-backport-20261102/build-r2/base'
PANEL = ROOT / 'astra-submissions/analysis/queen-screen-20261101'
sys.path.insert(0, str(ROOT))
from learning.compare_archives import kill_tree


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def prepare():
    OUT.mkdir(exist_ok=False)
    cases = [c for c in json.loads((PANEL / 'plan.json').read_text())['cases']
             if c['name'] in ('9ospae7x-52', 'ncejetlc-48')]
    assert len(cases) == 2
    source = (BASE / 'src/main.c').read_text()
    # Read-only source review: the env value is referenced only at its binding
    # and the log-only truth_report call, never by belief updates or search.
    references = [s.strip() for s in source.splitlines() if 'truth_seq' in s]
    assert references == [
        'const char *truth_seq = getenv("MIST_TRUTH_SEQ");',
        'if (truth_seq && views > 1) truth_report(&b, truth_seq, views - 1);']
    assert sha(BASE / 'mist') == '14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    dependencies = {str(p): sha(p) for p in [Path(__file__), BASE / 'mist',
        BASE / 'src/main.c', BASE / 'bin/stockfish', BASE / 'data/history.bin',
        ROOT / 'learning/compare_archives.py', PANEL / 'plan.json']}
    for c in cases:
        feed = PANEL / (c['name'] + '.input.txt')
        replay = ROOT / 'data/raw/games' / c['game'] / 'replay.json'
        assert sha(feed) == c['input_sha256'] and sha(replay) == c['replay_sha256']
        dependencies[str(feed)] = sha(feed)
        dependencies[str(replay)] = sha(replay)
    plan = dict(created=datetime.now(timezone.utc).isoformat(), cases=cases,
        dependencies=dependencies, arms=['control', 'truth_log'], seed=2221102,
        cores='2,3', seconds=2.5, timeout_seconds=120, calls=4,
        diagnostic_truth_input=True, truth_policy_input=False,
        source_references=references,
        questions=['First view where true placement is absent in this new diagnostic run',
                   'Whether support returns later',
                   'Rounded probability/rank trajectory in the uncapped 11-world example'],
        limitations='Known true boards are supplied only to the existing read-only stderr hook. This is an offline oracle diagnostic, never an eligible policy or strength test. The hook costs time and wall-clock thinning can change the run; no claim to reproduce the exact original first-loss update. Placement match omits castling/EP/history and reports only the first matching entry. Probabilities are rounded to five decimals. End-of-update logs cannot distinguish expansion capping from filtering inside that update.',
        stopping='Four first attempts, rotating arm order. Stop on technical failure; no retries, engine/model changes, promotion or full games. Launch only after phase 221 releases cores 2,3.')
    save(OUT / 'plan.json', plan)
    print(json.dumps({'calls': 4, 'plan_sha256': sha(OUT / 'plan.json')}))


def run():
    plan = json.loads((OUT / 'plan.json').read_text())
    for p, h in plan['dependencies'].items():
        assert sha(Path(p)) == h, p
    state = dict(started=datetime.now(timezone.utc).isoformat(), status='running',
                 completed=0, pid=os.getpid())
    with (OUT / 'execution.json').open('x') as f:
        json.dump(state, f)
    try:
        with (OUT / 'receipts.jsonl').open('x') as sink:
            for number, c in enumerate(plan['cases']):
                replay = json.loads((ROOT / 'data/raw/games' / c['game'] / 'replay.json').read_text())
                arms = plan['arms'][number:] + plan['arms'][:number]
                for arm in arms:
                    env = {k: v for k, v in os.environ.items()
                           if not k.startswith(('MIST_', 'ASTRA_', 'FOW_', 'OMP_', 'MKL_', 'OPENBLAS_'))}
                    env.update(MIST_FORCE_MOVES=','.join(c['forced']), MIST_TIMING='1',
                        MIST_MAX_SECONDS=str(plan['seconds']), FOW_SEED=str(plan['seed']),
                        MIST_STOCKFISH=str(BASE / 'bin/stockfish'), MIST_HISTORY_TABLE=str(BASE / 'data/history.bin'),
                        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
                    if arm == 'truth_log':
                        env['MIST_TRUTH_SEQ'] = ','.join(f['board'] for f in replay['frames'][:c['ply'] + 1])
                    started = time.monotonic()
                    p = subprocess.Popen(['taskset', '-c', plan['cores'], str(BASE / 'mist')],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, env=env, start_new_session=True)
                    error = None
                    try:
                        stdout, stderr = p.communicate((PANEL / (c['name'] + '.input.txt')).read_text(), timeout=plan['timeout_seconds'])
                    except subprocess.TimeoutExpired:
                        kill_tree(p.pid)
                        stdout, stderr = p.communicate()
                        error = 'timeout'
                    for suffix, text in [('stdout', stdout), ('stderr', stderr)]:
                        with (OUT / f"{c['name']}-{arm}.{suffix}").open('x') as f:
                            f.write(text)
                    lines = stdout.splitlines()
                    moves = [s[5:] for s in lines if s.startswith('move ')]
                    valid = bool(lines) and lines[0] == 'ready' and len(lines) == len(moves) + 1 and moves[:-1] == c['forced'] and len(moves) == len(c['forced']) + 1
                    row = dict(name=c['name'], arm=arm, returncode=p.returncode,
                        error=error, protocol_valid=valid, move=moves[-1] if moves else None,
                        elapsed=time.monotonic() - started,
                        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
                        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
                    sink.write(json.dumps(row) + '\n'); sink.flush()
                    state['completed'] += 1; save(OUT / 'execution.json', state)
                    print(json.dumps(row), flush=True)
                    assert valid and not error and p.returncode == 0, row
        state['status'] = 'complete'
    except BaseException:
        state['status'] = 'failed'
        raise
    finally:
        state['ended'] = datetime.now(timezone.utc).isoformat()
        save(OUT / 'execution.json', state)


def summarize():
    assert json.loads((OUT / 'execution.json').read_text())['status'] == 'complete'
    plan = json.loads((OUT / 'plan.json').read_text())
    receipts = [json.loads(s) for s in (OUT / 'receipts.jsonl').read_text().splitlines()]
    assert len(receipts) == 4
    results = []
    for c in plan['cases']:
        text = (OUT / (c['name'] + '-truth_log.stderr')).read_text()
        trace = []
        for line in text.splitlines():
            match = re.fullmatch(r'mist: truth v=(\d+) \|P\|=(\d+)(\(capped\))? (LOST|share=([\d.]+) rank=(\d+))', line)
            if match:
                trace.append(dict(ply=int(match[1]), worlds=int(match[2]), capped=bool(match[3]),
                    present=match[4] != 'LOST', rounded_share=float(match[5]) if match[5] else None,
                    rank=int(match[6]) if match[6] else None))
        assert [r['ply'] for r in trace] == list(range(1, c['ply'] + 1))
        first = next((r['ply'] for r in trace if not r['present']), None)
        changes = [r for i, r in enumerate(trace) if i == 0 or r['present'] != trace[i-1]['present']]
        arm_rows = [r for r in receipts if r['name'] == c['name']]
        for r in arm_rows:
            assert sha(OUT / f"{c['name']}-{r['arm']}.stderr") == r['stderr_sha256']
        results.append(dict(name=c['name'], first_absent_ply=first, support_transitions=changes,
            final=trace[-1], trace=trace, arms=arm_rows,
            thinning_lines=[s for s in text.splitlines() if 'P thinned' in s]))
    save(OUT / 'summary.json', dict(cases=results, scope=plan['limitations']))
    print(json.dumps([{k: v for k, v in r.items() if k != 'trace'} for r in results], indent=2))


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'run', 'summarize')
    globals()[sys.argv[1]]()
