#!/usr/bin/env python3
"""Frozen, outcome-blind private-history diagnostic; never an Elo estimate."""
import argparse
from collections import Counter
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
OUT = ROOT/'astra-submissions/analysis/data-biased-search-20261101'
BASE = HERE.parent/'stable-mix-20261101/build/base'
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol, exchange_probe
from learning import ingest
from learning.compare_archives import kill_tree

OPPONENTS = ['Instructors', 'duck', 'HYPOTHERMIA', 'Strongly Invisible',
             'Decent Chess Bot', 'Mist Opportunities', 'Crimson Fog', 'Knight Vision']
ARMS = ['original', 'off', 'dbr']


def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def parse_moves(stdout):
    lines = stdout.splitlines()
    if not lines or lines[0] != 'ready': return None
    moves = []
    for line in lines[1:]:
        match = re.fullmatch(r'move ([a-h][1-8][a-h][1-8][qrbn]?)', line)
        if not match: return None
        moves.append(match[1])
    return moves


def freeze():
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'plan.json').exists()
    payload = (ROOT/'data/raw/accepted.jsonl').read_bytes()
    rows = {r['id']: r for r in map(json.loads, payload.splitlines())}
    excluded = set()
    for rel in ['frozen-tree-20261101/plan.json', 'frozen-tree-20261101/early/plan.json']:
        p = OUT.parent/rel
        if p.exists(): excluded.update(c['game'] for c in json.loads(p.read_text())['cases'])
    selected = []
    for side in ['white', 'black']:
        other = 'black' if side == 'white' else 'white'
        choices = [r for r in rows.values() if r['id'] not in excluded
                   and r.get(side) == 'IAmAVirus' and r.get(side+'Version') == 37
                   and r.get(other) in OPPONENTS and r['createdAt'].startswith('2026-11-01')]
        choices.sort(key=lambda r: sha(('dbr207:'+r['id']).encode()))
        assert len(choices) >= 4, (side, len(choices))
        selected.extend((r, side) for r in choices[:4])
    # IDs selected above without consulting outcomes, moves, or board states.
    cases = []; games = []
    for r, key in selected:
        side = ['white', 'black'].index(key); other = ['black', 'white'][side]
        raw = (ROOT/'data/raw/games'/r['id']/'replay.json').read_bytes()
        replay = json.loads(raw); states, errors = ingest.validate_replay(replay)
        assert not errors, (r['id'], errors)
        games.append(dict(game=r['id'], side=side, opponent=r[other], opponent_version=r[other+'Version'],
                          result=r['result'], frames=len(states), replay_sha256=sha(raw)))
        for ply in [side, side+8, side+16, side+24]:
            if ply >= len(states)-1: continue
            feed, forced = protocol(replay, ply, side)
            redacted = json.loads(raw)
            for i, frame in enumerate(redacted['frames']):
                frame['board'] = 'X'*64; frame[other] = 'X'*64
                if i == 0 or (i-1) % 2 != side or i > ply: frame['move'] = 'REDACTED'
            assert protocol(redacted, ply, side) == (feed, forced)
            name = f"{r['id']}-{ply}"
            (OUT/(name+'.input.txt')).write_text(feed)
            cases.append(dict(name=name, game=r['id'], ply=ply, side=side, opponent=r[other],
                              forced=forced, input_sha256=sha(feed.encode()), replay_sha256=sha(raw)))
    pins = json.loads((HERE/'provenance.json').read_text())
    binaries = {a: str((BASE if a == 'original' else HERE/'build')/'mist') for a in ARMS}
    assert sha(Path(binaries['dbr']).read_bytes()) == pins['binary_sha256']
    assert sha((BASE/'data/history.bin').read_bytes()) == pins['history_sha256']
    assert sha((BASE/'bin/stockfish').read_bytes()) == pins['stockfish_sha256']
    plan = dict(created_at=datetime.now(timezone.utc).isoformat(), games=games, cases=cases,
                accepted_sha256=sha(payload), excluded_games=sorted(excluded), pins=pins,
                binaries=binaries, binary_sha256={a: sha(Path(p).read_bytes()) for a, p in binaries.items()},
                runner_sha256=sha(Path(__file__).read_bytes()),
                arms=ARMS, seconds=2.5, seed=2071101, cores='0,1', confidence_max=.5,
                truth_to_engine=False, selection='Four hash-selected games per colour, no outcome filter; own turns 1,5,9,13 when recorded.',
                scope='History coverage and decision-mechanism development diagnostic, not playing strength.',
                decision='Any technical error stops. No full games without meaningful beyond-opening history coverage and decision differences; a separate frozen match plan is required. No tuning on these results.')
    with (OUT/'plan.json').open('x') as f: json.dump(plan, f, indent=2)
    print(json.dumps(dict(games=games, decisions=len(cases)), indent=2))


def recover():
    """Retain the one completed engine call; fix only its protocol decoding."""
    plan = json.loads((OUT/'plan.json').read_text())
    old = subprocess.check_output(['git', 'show', '588246b:astra-submissions/experiments/data-biased-search-20261101/run.py'])
    assert sha(old) == plan['runner_sha256']
    initial = list(map(json.loads, (OUT/'receipts.jsonl').read_text().splitlines()))
    assert len(initial) == 1
    row = dict(initial[0]); case = plan['cases'][0]
    assert row['name'] == case['name'] and row['arm'] == 'original' and row['returncode'] == 0 and row['error'] is None
    streams = {}
    for stream in ['stdout', 'stderr']:
        raw = (OUT/(row['name']+'-original.'+stream)).read_bytes()
        assert sha(raw) == row[stream+'_sha256']; streams[stream] = raw.decode()
    moves = parse_moves(streams['stdout'])
    assert moves is not None and len(moves) == len(case['forced'])+1 and moves[:-1] == case['forced']
    row.update(protocol_valid=True, move=moves[-1], recovery='Original engine exit0 retained; old parser omitted mandatory move prefix. No rerun.')
    assert parse_moves('ready\nmove e2e4\nmove e7e8q\n') == ['e2e4', 'e7e8q']
    for invalid in ['e2e4\n', 'ready\ne2e4\n', 'ready\nmove e7e8k\n', 'ready\nmove i2i4\n']:
        assert parse_moves(invalid) is None
    recovery = dict(original_plan_sha256=sha((OUT/'plan.json').read_bytes()),
                    original_receipts_sha256=sha((OUT/'receipts.jsonl').read_bytes()),
                    runner_sha256=sha(Path(__file__).read_bytes()), carried_receipt=row,
                    original_execution=json.loads((OUT/'execution.json').read_text()),
                    parser_tests='actual first receipt plus five valid/invalid fixtures pass',
                    reason='Protocol parser defect; preserve first attempt and continue 95 unstarted cells with identical experimental settings.')
    with (OUT/'recovery-plan.json').open('x') as f: json.dump(recovery, f, indent=2)
    print(json.dumps(recovery, indent=2))


def run():
    plan = json.loads((OUT/'plan.json').read_text())
    recovery = json.loads((OUT/'recovery-plan.json').read_text())
    assert sha(Path(__file__).read_bytes()) == recovery['runner_sha256']
    assert sha((OUT/'plan.json').read_bytes()) == recovery['original_plan_sha256']
    assert sha((OUT/'receipts.jsonl').read_bytes()) == recovery['original_receipts_sha256']
    for arm, binary in plan['binaries'].items():
        assert sha(Path(binary).read_bytes()) == plan['binary_sha256'][arm]
    assert sha((BASE/'data/history.bin').read_bytes()) == plan['pins']['history_sha256']
    assert sha((BASE/'bin/stockfish').read_bytes()) == plan['pins']['stockfish_sha256']
    state = dict(status='running', pid=os.getpid(), started_at=datetime.now(timezone.utc).isoformat(), completed=1, carried_first_cell=True)
    execution = OUT/'execution-recovered.json'
    with execution.open('x') as f: json.dump(state, f, indent=2)
    try:
        with (OUT/'receipts-recovered.jsonl').open('x') as sink:
            sink.write(json.dumps(recovery['carried_receipt'])+'\n'); sink.flush()
            for number, case in enumerate(plan['cases']):
                feed = (OUT/(case['name']+'.input.txt')).read_text()
                assert sha(feed.encode()) == case['input_sha256']
                order = ARMS[number % 3:]+ARMS[:number % 3]
                for arm in order:
                    if (case['name'], arm) == (recovery['carried_receipt']['name'], recovery['carried_receipt']['arm']): continue
                    env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
                    env.update(MIST_FORCE_MOVES=','.join(case['forced']), MIST_MAX_SECONDS=str(plan['seconds']),
                               FOW_SEED=str(plan['seed']), MIST_STOCKFISH=str(BASE/'bin/stockfish'),
                               MIST_HISTORY_TABLE=str(BASE/'data/history.bin'), OMP_NUM_THREADS='1')
                    if arm == 'dbr': env['ASTRA_DBR_MAX'] = str(plan['confidence_max'])
                    start = time.monotonic(); error = None
                    proc = subprocess.Popen(['taskset', '-c', plan['cores'], plan['binaries'][arm]],
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            text=True, env=env, start_new_session=True)
                    try: stdout, stderr = proc.communicate(feed, timeout=75)
                    except subprocess.TimeoutExpired:
                        kill_tree(proc.pid); stdout, stderr = proc.communicate(); error = '75s diagnostic timeout'
                    name = case['name']+'-'+arm
                    assert not (OUT/(name+'.stdout')).exists() and not (OUT/(name+'.stderr')).exists()
                    (OUT/(name+'.stdout')).write_text(stdout); (OUT/(name+'.stderr')).write_text(stderr)
                    moves = parse_moves(stdout)
                    valid = proc.returncode == 0 and moves is not None and len(moves) == len(case['forced'])+1 and moves[:-1] == case['forced']
                    matches = re.findall(r'astra_dbr: opponent_sets (\d+) constrained (\d+) first_reply_coverage ([\deE+.-]+) first_reply_confidence ([\deE+.-]+) expected_model_visits ([\deE+.-]+)', stderr)
                    coverage = dict(zip(['opponent_sets', 'constrained', 'first_reply_coverage', 'first_reply_confidence', 'expected_model_visits'],
                                        map(float, matches[-1]))) if matches else None
                    row = dict(name=case['name'], arm=arm, returncode=proc.returncode, error=error, protocol_valid=valid,
                               move=moves[-1] if valid else None, elapsed=time.monotonic()-start, coverage=coverage,
                               stdout_sha256=sha(stdout.encode()), stderr_sha256=sha(stderr.encode()))
                    sink.write(json.dumps(row)+'\n'); sink.flush()
                    state['completed'] += 1; dump(execution, state)
                    print(state['completed'], len(plan['cases'])*3, name, row['move'], round(row['elapsed'], 2), coverage, flush=True)
                    if not valid: raise RuntimeError(row)
        state['status'] = 'complete'
    except BaseException:
        state['status'] = 'failed'; raise
    finally:
        state['ended_at'] = datetime.now(timezone.utc).isoformat(); dump(execution, state)


def summarize():
    plan = json.loads((OUT/'plan.json').read_text())
    assert json.loads((OUT/'execution-recovered.json').read_text())['status'] == 'complete'
    receipts = list(map(json.loads, (OUT/'receipts-recovered.jsonl').read_text().splitlines()))
    assert len(receipts) == 3*len(plan['cases'])
    keyed = {(r['name'], r['arm']): r for r in receipts}; assert len(keyed) == len(receipts)
    labelled = []; cache = {}
    for case in plan['cases']:
        if case['game'] not in cache:
            raw = (ROOT/'data/raw/games'/case['game']/'replay.json').read_bytes()
            assert sha(raw) == case['replay_sha256']
            states, errors = ingest.validate_replay(json.loads(raw)); assert not errors
            cache[case['game']] = states
        state = cache[case['game']][case['ply']]
        row = dict(case=case['name'], ply=case['ply'], side=case['side'], opponent=case['opponent'], arms={})
        for arm in ARMS:
            r = keyed[case['name'], arm]; assert r['protocol_valid'] and r['returncode'] == 0
            for stream in ['stdout', 'stderr']:
                assert sha((OUT/(case['name']+'-'+arm+'.'+stream)).read_bytes()) == r[stream+'_sha256']
            label = exchange_probe(state, r['move']); assert label['legal']
            row['arms'][arm] = dict(move=r['move'], label=label, coverage=r['coverage'], elapsed=r['elapsed'])
        labelled.append(row)
    summaries = {}
    for arm in ARMS:
        arms = [r['arms'][arm] for r in labelled]
        summaries[arm] = dict(king_loss=sum(r['label']['fatal'] for r in arms),
                             exchange_loss_ge2=sum((r['label']['exchange_loss'] or 0) >= 2 for r in arms),
                             queen_loss_ge4=sum((r['label']['queen_exchange_loss'] or 0) >= 4 for r in arms))
    coverage = []
    for ply in sorted({r['ply']-r['side'] for r in labelled}):
        group = [r['arms']['dbr']['coverage'] for r in labelled if r['ply']-r['side'] == ply]
        present = [c for c in group if c is not None]
        coverage.append(dict(own_turn=ply//2+1, cases=len(group), diagnostics=len(present),
                             any_constrained=sum(c['constrained'] > 0 for c in present),
                             first_reply_supported=sum(c['first_reply_coverage'] > 0 for c in present),
                             mean_first_reply_coverage=sum(c['first_reply_coverage'] for c in present)/len(group),
                             mean_first_reply_confidence=sum(c['first_reply_confidence'] for c in present)/len(group)))
    result = dict(decisions=len(labelled), frames_verified=sum(len(s) for s in cache.values()), arms=summaries,
                  choice_changes_vs_original={a: sum(r['arms'][a]['move'] != r['arms']['original']['move'] for r in labelled) for a in ['off', 'dbr']},
                  coverage_by_own_turn=coverage, scope=plan['scope'],
                  limitations='Wall-clock search can vary even with feature off; selected observed-history prefixes are not full games. Exchange labels exclude non-capture forcing continuations.')
    dump(OUT/'labelled.json', labelled); dump(OUT/'summary.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('command', choices=['freeze', 'recover', 'run', 'summarize'])
    globals()[p.parse_args().command]()
