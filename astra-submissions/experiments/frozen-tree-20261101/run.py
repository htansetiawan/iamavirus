#!/usr/bin/env python3
"""Outcome-stratified mechanism audit; never a same-clock strength test.

Freeze before any audit runs. The subprocess receives only own observations,
clocks and prior own moves. Truth and counterfactual tactical labels are joined
after it terminates. Do not continue the recorded opponent line after a change.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/frozen-tree-20261101'
sys.path[:0] = [str(ROOT), str(ROOT / 'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol, exchange_probe
from learning import ingest, rules
from learning import compare_archives as ca

OPPONENTS = ['Instructors', 'duck', 'HYPOTHERMIA', 'Strongly Invisible',
             'Decent Chess Bot', 'Mist Opportunities', 'Crimson Fog', 'Knight Vision']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def freeze():
    OUT.mkdir(exist_ok=True)
    data = (ROOT / 'data/raw/accepted.jsonl').read_bytes()
    rows = {r['id']: r for r in map(json.loads, data.splitlines())}
    excluded = set()
    for directory in ['context-mixture-20261101', 'temporal-belief-20261101']:
        excluded |= {p.name.split('.')[0] for p in (OUT.parent / directory).glob('*.input.json')}
    groups = defaultdict(list)
    for r in rows.values():
        if r['id'] in excluded:
            continue
        side = next((s for s in ('white', 'black') if r[s] == 'IAmAVirus' and r.get(s+'Version') == 37), None)
        if side is None:
            continue
        opponent = r['black' if side == 'white' else 'white']
        if opponent not in OPPONENTS:
            continue
        win = '1-0' if side == 'white' else '0-1'
        result = 'win' if r['result'] == win else 'draw' if r['result'] == '1/2-1/2' else 'loss'
        groups[(opponent, result)].append((r, side))
    cases = []; selections = []
    for (opponent, outcome), choices in sorted(groups.items()):
        r, key = min(choices, key=lambda rs: sha(('frozen-tree-20261101:' + rs[0]['id']).encode()))
        path = ROOT / 'data/raw/games' / r['id'] / 'replay.json'
        payload = path.read_bytes(); replay = json.loads(payload)
        states, errors = ingest.validate_replay(replay); assert not errors, errors
        side = ('white', 'black').index(key)
        own = list(range(side, len(states)-1, 2)); assert own
        # Terminal losing choice plus three own turns earlier; winning/drawn
        # controls two and five own turns before the last recorded own move.
        positions = [own[-1], own[max(0, len(own)-4)]] if outcome == 'loss' else [own[max(0, len(own)-3)], own[max(0, len(own)-6)]]
        selections.append({'game': r['id'], 'opponent': opponent, 'outcome': outcome, 'available_games': len(choices)})
        for ply in sorted(set(positions)):
            feed, forced = protocol(replay, ply, side)
            redacted = json.loads(payload)
            other = 'black' if key == 'white' else 'white'
            for i, frame in enumerate(redacted['frames']):
                frame['board'] = 'X'*64; frame[other] = 'X'*64
                if i == 0 or (i-1) % 2 != side or i > ply:
                    frame['move'] = 'REDACTED'
            assert protocol(redacted, ply, side) == (feed, forced)
            name = f"{r['id']}-{ply}"
            (OUT / (name + '.input.txt')).write_text(feed)
            cases.append({'name': name, 'game': r['id'], 'ply': ply, 'side': side,
                          'opponent': opponent, 'opponent_version': r[other+'Version'],
                          'outcome': outcome, 'created_at': r['createdAt'],
                          'replay_sha256': sha(payload), 'input_sha256': sha(feed.encode()),
                          'forced': forced, 'private_input_redaction_check': True})
    provenance = json.loads((HERE / 'provenance.json').read_text())
    plan = {'scope': 'Selected v37 mechanism diagnostics; no population rate, Elo, or same-clock strength claim.',
            'selection': 'One hash-selected game per opponent/result, two history-relative decisions per game; excludes prior temporal/context panels.',
            'source_accepted_sha256': sha(data), 'excluded_games': sorted(excluded), 'groups': selections,
            'cases': cases, 'provenance': provenance, 'runner_sha256': sha(Path(__file__).read_bytes()),
            'search_seconds': 2.5, 'extra_solver_wall_cap': 3.0, 'extra_targets': [20, 200, 1000],
            'seed': 11012026, 'cores': '0,1', 'truth_to_engine': False,
            'decision': 'Only if more iterations meaningfully change root strategy AND improve sampled tactical diagnostics without new failures is a separate same-clock experiment justified. Stability is not correctness; no tuning on this panel.'}
    with (OUT / 'plan.json').open('x') as f:
        json.dump(plan, f, indent=2)
    print(json.dumps({'games': len(selections), 'decisions': len(cases), 'groups': selections}, indent=2))


def run():
    plan = json.loads((OUT / 'plan.json').read_text())
    assert sha(Path(__file__).read_bytes()) == plan['runner_sha256'], 'runner changed after freeze'
    binary = HERE / 'build/mist'
    assert sha(binary.read_bytes()) == plan['provenance']['binary_sha256']
    with (OUT / 'receipts.jsonl').open('x') as sink:
        for number, case in enumerate(plan['cases']):
            feed = (OUT / (case['name'] + '.input.txt')).read_text()
            assert sha(feed.encode()) == case['input_sha256']
            diag = OUT / (case['name'] + '.audit.json'); assert not diag.exists()
            env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
            env.update(MIST_FORCE_MOVES=','.join(case['forced']), MIST_MAX_SECONDS=str(plan['search_seconds']),
                       FOW_SEED=str(plan['seed']), MIST_STOCKFISH=str(HERE / 'build/bin/stockfish'),
                       MIST_HISTORY_TABLE=str(HERE / 'build/data/history.bin'), ASTRA_FROZEN_TREE_OUT=str(diag))
            start = time.monotonic()
            proc = subprocess.Popen(['taskset', '-c', plan['cores'], str(binary)], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            try:
                stdout, stderr = proc.communicate(feed, timeout=180)
                error = None
            except subprocess.TimeoutExpired:
                ca.kill_tree(proc.pid); stdout, stderr = proc.communicate(); error = 'timeout'
            (OUT / (case['name'] + '.stdout')).write_text(stdout)
            (OUT / (case['name'] + '.stderr')).write_text(stderr)
            moves = [line[5:].strip() for line in stdout.splitlines() if line.startswith('move ')]
            valid = proc.returncode == 0 and len(moves) == len(case['forced'])+1 and moves[:-1] == case['forced']
            row = {'name': case['name'], 'exit': proc.returncode, 'error': error, 'protocol_valid': valid,
                   'elapsed': time.monotonic()-start, 'emitted_move': moves[-1] if valid else None,
                   'audit_available': diag.exists(), 'stdout_sha256': sha(stdout.encode()), 'stderr_sha256': sha(stderr.encode()),
                   'audit_sha256': sha(diag.read_bytes()) if diag.exists() else None}
            sink.write(json.dumps(row) + '\n'); sink.flush()
            print(number+1, len(plan['cases']), row['name'], row['exit'], row['emitted_move'], round(row['elapsed'], 2), flush=True)


def summarize():
    plan = json.loads((OUT / 'plan.json').read_text())
    receipts = {r['name']: r for r in map(json.loads, (OUT / 'receipts.jsonl').read_text().splitlines())}
    assert len(receipts) == len(plan['cases'])
    rows = []; skipped = []
    for case in plan['cases']:
        receipt = receipts[case['name']]
        assert receipt['exit'] == 0 and receipt['protocol_valid'], receipt
        if not receipt['audit_available']:
            skipped.append({'case': case['name'], 'reason': 'Search bypassed; inspect stderr', 'move': receipt['emitted_move']}); continue
        data = (OUT / (case['name'] + '.audit.json')).read_bytes()
        assert sha(data) == receipt['audit_sha256']
        audit = json.loads(data); snaps = audit['snapshots']; first, last = snaps[0], snaps[-1]
        assert len({s['tree_hash'] for s in snaps}) == 1
        assert first['selected'] == audit['original_solver_move']
        assert abs(first['root_value'] - audit['original_value']) < 1e-8
        assert abs(sum(s['weight'] for s in audit['samples'])-1) < 1e-8
        assert all(abs(sum(a['probability'] for a in s['actions'])-1) < 1e-8 for s in snaps)
        payload = (ROOT / 'data/raw/games' / case['game'] / 'replay.json').read_bytes()
        assert sha(payload) == case['replay_sha256']
        replay = json.loads(payload); states, errors = ingest.validate_replay(replay); assert not errors
        state = states[case['ply']]; board = state.board
        legal = board.legal_moves(); true_fatal = {m: board.move_loses_king(m) for m in legal}
        samples = [(rules.Board.from_board_string(s['board'], s['side'], s['castle'], s['ep']), s['weight']) for s in audit['samples']]
        sampled_risk = {}
        for a in first['actions']:
            m = a['move']
            sampled_risk[m] = sum(w for b,w in samples if m in b.legal_moves() and b.move_loses_king(m))
        actions = {a['move'] for a in first['actions']}
        labels = {m: exchange_probe(state, m) for m in {receipt['emitted_move'], *(s['selected'] for s in snaps)}}
        for s in snaps:
            m = s['selected']; s['truth_probe'] = labels[m]; s['sampled_king_risk'] = sampled_risk[m]
        row = {'case': case['name'], 'opponent': case['opponent'], 'outcome': case['outcome'],
               'emitted_matches_original_solver': receipt['emitted_move'] == audit['original_solver_move'],
               'true_board_sample_mass': sum(w for b,w in samples if b.board_string() == board.board_string()),
               'true_state_sample_mass': sum(w for b,w in samples if b.board_string() == board.board_string() and b.castling == board.castling and b.en_passant == board.en_passant),
               'true_safe_legal_moves': sum(not f for f in true_fatal.values()),
               'true_safe_root_moves': sum(not true_fatal.get(m, True) for m in actions),
               'true_safe_avoided': [m for m in audit['avoid'] if m in true_fatal and not true_fatal[m]],
               'root_action_truth': [{'move': a['move'], 'fatal': true_fatal.get(a['move']), 'sample_risk': sampled_risk[a['move']]} for a in first['actions']],
               'original_iterations': audit['original_iterations'], 'nodes': audit['nodes'], 'belief_count': audit['belief_count'],
               'snapshots': snaps, 'initial': audit['initial']}
        rows.append(row)
    def stage(s):
        return {'fatal': sum(r['snapshots'][s]['truth_probe']['fatal'] for r in rows),
                'illegal': sum(not r['snapshots'][s]['truth_probe']['legal'] for r in rows),
                'material_loss_ge2': sum((r['snapshots'][s]['truth_probe']['exchange_loss'] or 0) >= 2 for r in rows),
                'queen_loss_ge4': sum((r['snapshots'][s]['truth_probe']['queen_exchange_loss'] or 0) >= 4 for r in rows)}
    changed = [r for r in rows if r['snapshots'][0]['selected'] != r['snapshots'][-1]['selected']]
    summary = {'cases': len(plan['cases']), 'audited': len(rows), 'skipped': skipped,
               'original': stage(0), 'final_settled': stage(-1), 'choice_changes': len(changed),
               'changes': [{'case': r['case'], 'from': r['snapshots'][0]['selected'], 'to': r['snapshots'][-1]['selected'],
                            'fatal_before': r['snapshots'][0]['truth_probe']['fatal'], 'fatal_after': r['snapshots'][-1]['truth_probe']['fatal'],
                            'tv': r['snapshots'][-1]['root_total_variation']} for r in changed],
               'median_root_tv': statistics.median(r['snapshots'][-1]['root_total_variation'] for r in rows),
               'root_tv_gt_01': sum(r['snapshots'][-1]['root_total_variation'] > .1 for r in rows),
               'median_root_gap_before': statistics.median(r['snapshots'][0]['root_deviation_gain'] for r in rows),
               'median_root_gap_after': statistics.median(r['snapshots'][-1]['root_deviation_gain'] for r in rows),
               'min_extra_iterations': min(r['snapshots'][-1]['extra_iterations'] for r in rows),
               'max_extra_iterations': max(r['snapshots'][-1]['extra_iterations'] for r in rows),
               'scope': plan['scope'], 'tree_unchanged_all': True}
    dump(OUT / 'labelled.json', rows); dump(OUT / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('command', choices=['freeze', 'run', 'summarize'])
    globals()[ap.parse_args().command]()
