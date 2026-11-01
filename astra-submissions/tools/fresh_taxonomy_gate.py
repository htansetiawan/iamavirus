#!/usr/bin/env python3
"""Freeze fresh taxonomy cohorts and compare exact ZIPs on permitted replay inputs.

Labels/scoring see the true board; the bots get only their own observation
history, clock, and forced own moves. No recorded opponent continuation is
used after a candidate diverges. Material scoring is an explicitly limited,
omniscient one-capture/one-response diagnostic, NOT a game-strength estimate.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from learning import ingest, move_taxonomy, rules
from learning import compare_archives as ca

VALUE = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
COHORTS = ('king_fatal', 'queen_exposed', 'clean_material_loss', 'recovered_exchange', 'control')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def material(text, side):
    return sum(VALUE[c.lower()] * (1 if c.isupper() == (side == 0) else -1) for c in text if c != '-')


def material_horizons(frames, ply, side):
    """Use the SAME frame for both armies, after the reply and our response."""
    before = material(frames[ply]['board'], side)
    return {str(h): before-material(frames[ply+h]['board'], side) if ply+h < len(frames) else None
            for h in (2, 3)}


def protocol(replay, ply, side):
    key = ('white', 'black')[side]
    tc = replay.get('timeControl', {})
    feed = ['fow', f"{'w' if side == 0 else 'b'} {tc.get('baseSeconds', 180)} {tc.get('incrementSeconds', 2)}"]
    forced = []
    for p in range(ply+1):
        feed.append(replay['frames'][p][key])
        if p % 2 == side:
            feed.append(str(replay['frames'][p]['clocks'][side]))
            if p < ply:
                forced.append(replay['frames'][p+1]['move'])
    return '\n'.join(feed)+'\n', forced


def exchange_probe(state, move):
    """Truth-only vulnerability: opponent captures, then our best safe response.

    Each response uses the exact castling/en-passant/history state. Reject
    suicidal opponent captures and suicidal recaptures. A no-capture opponent
    continuation is outside this horizon. Report forced king loss separately.
    """
    side = state.board.side
    if move not in state.board.legal_moves():
        return {'legal': False}
    child = state.copy(); child.push(move)
    losing = ('0-1', '1-0')[side]
    terminal = child.outcome()
    result = {'legal': True, 'fatal': bool(terminal and terminal[0] == losing),
              'terminal': terminal, 'exchange_loss': None, 'queen_exchange_loss': None,
              'forced_king_loss_after_capture': False}
    if terminal:
        return result
    initial = material(state.board.board_string(), side)
    own_chars = 'PNBRQK' if side == 0 else 'pnbrqk'
    text = child.board.board_string()
    original_count = sum(c in own_chars for c in text)
    queen = 'Q' if side == 0 else 'q'
    worst = worst_queen = 0
    for reply in child.board.legal_moves():
        after = child.copy(); after.push(reply)
        after_text = after.board.board_string()
        if sum(c in own_chars for c in after_text) >= original_count:
            continue
        term = after.outcome()
        if term:  # a suicidal opponent capture or a terminal draw is not material loss
            continue
        best = None; best_move = None
        for response in after.board.legal_moves():
            end = after.copy(); end.push(response)
            outcome = end.outcome()
            if outcome and outcome[0] == losing:
                continue
            # An immediate win/draw is a successful answer, regardless of material.
            score = initial if outcome else material(end.board.board_string(), side)
            if best is None or score > best:
                best, best_move = score, response
        if best is None:
            result['forced_king_loss_after_capture'] = True
            result['forcing_capture'] = reply
            continue
        loss = max(0, initial-best)
        if loss > worst:
            worst = loss
            result.update(worst_capture=reply, best_response=best_move)
        if after_text.count(queen) < text.count(queen):
            worst_queen = max(worst_queen, loss)
    result.update(exchange_loss=worst, queen_exchange_loss=worst_queen)
    return result


def freeze(args):
    raw_rows = (args.raw/'accepted.jsonl').read_bytes()
    rows = {r['id']: r for r in (json.loads(l) for l in raw_rows.splitlines())}
    chosen = []
    for r in rows.values():
        when = r.get('createdAt') or ''
        if not args.since <= when < args.until:
            continue
        side = next((s for s in ('white', 'black') if r.get(s) == 'IAmAVirus' and r.get(s+'Version') == 35), None)
        if side and r['black' if side == 'white' else 'white'] in args.opponents:
            chosen.append((r, side))
    buckets = defaultdict(list); games = []; rejected = []
    for row, key in sorted(chosen, key=lambda rs: rs[0]['id']):
        path = args.raw/'games'/row['id']/'replay.json'
        payload = path.read_bytes(); rp = json.loads(payload)
        states, errors = ingest.validate_replay(rp)
        if errors:
            rejected.append({'game': row['id'], 'errors': errors}); continue
        side = ('white', 'black').index(key); other = ('black', 'white')[side]
        taxonomy = {m['ply']-1: m for m in move_taxonomy.label_game(rp)['moves'] if m['side'] == side}
        games.append({'game': row['id'], 'path': str(path), 'sha256': sha(payload),
                      'opponent': row[other], 'opponent_version': row[other+'Version'], 'side': key,
                      'created_at': row['createdAt'], 'result': row['result'], 'frames': len(states)})
        for ply in range(side, len(states)-1, 2):
            tags = taxonomy[ply]['tags']; played = rp['frames'][ply+1]['move']
            horizon = material_horizons(rp['frames'], ply, side)
            labels = []
            if states[ply].board.move_loses_king(played):
                labels.append('king_fatal')
            if 'queen_exposed_unseen' in tags:
                labels.append('queen_exposed')
            if horizon['3'] is not None and horizon['3'] >= 2:
                labels.append('clean_material_loss')
            if horizon['2'] is not None and horizon['3'] is not None and horizon['2'] >= 2 and horizon['3'] < 2:
                labels.append('recovered_exchange')
            if not labels and 8 <= ply <= 70:
                labels.append('control')
            entry = {'game': row['id'], 'ply': ply, 'side': key, 'opponent': row[other],
                     'opponent_version': row[other+'Version'], 'our_version': 35,
                     'played': played, 'tags': tags, 'recorded_material_loss': horizon,
                     'cohorts': labels, 'replay_path': str(path), 'replay_sha256': sha(payload)}
            for label in labels:
                buckets[(row[other], key, label)].append(entry)
    cases = {}; counts = {}
    for bucket, entries in sorted(buckets.items()):
        entries.sort(key=lambda e: sha(f"fresh-taxonomy-1101:{e['game']}:{e['ply']}".encode()))
        # At most one decision per game in a cohort: long losing games do not dominate.
        used = set(); picked = []
        for e in entries:
            if e['game'] in used:
                continue
            used.add(e['game']); picked.append(e)
            cases[(e['game'], e['ply'])] = e
            if len(picked) >= args.per_group:
                break
        counts[' / '.join(bucket)] = {'available': len(entries), 'selected': len(picked)}
    frozen = {'since': args.since, 'until': args.until, 'source_accepted_sha256': sha(raw_rows),
              'opponents': args.opponents, 'per_group': args.per_group,
              'games': games, 'rejected_games': rejected, 'selection': counts,
              'cases': [cases[k] for k in sorted(cases)],
              'scope': 'Fresh v35 seats, wins and losses, taxonomy-stratified diagnostics; not outcome-unbiased strength or calibration estimates.'}
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out/'cases.json').open('x') as f:
        json.dump(frozen, f, indent=2)
    print(json.dumps({'games': len(games), 'rejected': len(rejected), 'cases': len(cases), 'groups': counts}, indent=2))


def run(args):
    cases_file = args.out/'cases.json'; frozen = json.loads(cases_file.read_text())
    archives = {'v35': ROOT/'fable-submissions/iamavirus-v35-mist-c-v14.zip',
                'v37': ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'}
    pins = {'archives': {k: sha(p.read_bytes()) for k,p in archives.items()},
            'cases_sha256': sha(cases_file.read_bytes()), 'seconds': args.seconds,
            'cores': args.cores, 'seed': args.seed, 'arms': ['v35', 'v37', 'v35_repeat'],
            'truth_to_bot': False, 'counterfactual_recorded_replies': False}
    with (args.out/'run-pins.json').open('x') as f:
        json.dump(pins, f, indent=2)
    binaries = {k: ca.build(p, args.out/'builds') for k,p in archives.items()}
    binaries['v35_repeat'] = binaries['v35']
    results = []
    with (args.out/'results.jsonl').open('x') as output:
        for i, case in enumerate(frozen['cases']):
            payload = Path(case['replay_path']).read_bytes()
            assert sha(payload) == case['replay_sha256']
            replay = json.loads(payload); states, errors = ingest.validate_replay(replay)
            assert not errors, errors
            side = ('white', 'black').index(case['side']); state = states[case['ply']]
            feed, forced = protocol(replay, case['ply'], side)
            row = {'case': case, 'recorded': exchange_probe(state, case['played']), 'arms': {}}
            # Rotate order to avoid always running the candidate warm/last.
            arms = pins['arms'][i%3:] + pins['arms'][:i%3]
            for name in arms:
                env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_'))}
                env.update(MIST_FORCE_MOVES=','.join(forced), MIST_MAX_SECONDS=str(args.seconds), FOW_SEED=str(args.seed))
                start = time.monotonic()
                proc = subprocess.Popen(['taskset', '-c', args.cores, 'bash', str(binaries[name]/'run.sh')],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
                try:
                    stdout, stderr = proc.communicate(feed, timeout=180)
                    moves = [l[5:].strip() for l in stdout.splitlines() if l.startswith('move ')]
                    if proc.returncode or len(moves) != len(forced)+1 or moves[:-1] != forced:
                        raise ValueError(f'protocol mismatch exit={proc.returncode} moves={len(moves)} expected={len(forced)+1}')
                    move = moves[-1]; probe = exchange_probe(state, move)
                    q = re.findall(r'queen risk chosen ([\d.]+)/([\d.]+) least ([\d.]+)/([\d.]+)', stderr)
                    row['arms'][name] = {'move': move, 'elapsed': time.monotonic()-start, **probe,
                                         'queen_risk': [float(x) for x in q[-1]] if q else None,
                                         'king_guard_fired': 'king guard left out' in stderr,
                                         'queen_guard_fired': 'queen guard left out' in stderr}
                    log = args.out/'logs'/f"{case['game']}-{case['ply']}-{name}.stderr"
                    log.parent.mkdir(exist_ok=True); log.write_text(stderr)
                except (subprocess.TimeoutExpired, ValueError) as exc:
                    if proc.poll() is None:
                        ca.kill_tree(proc.pid)
                    proc.wait()
                    row['arms'][name] = {'error': str(exc), 'elapsed': time.monotonic()-start}
            results.append(row); output.write(json.dumps(row)+'\n'); output.flush()
            print(i+1, len(frozen['cases']), case['game'], case['ply'], {n:v.get('move', v.get('error')) for n,v in row['arms'].items()}, flush=True)
    summary = {'cases': len(results), 'games': len({r['case']['game'] for r in results}), 'arms': {}}
    for name in pins['arms']:
        arm = [r['arms'][name] for r in results]
        summary['arms'][name] = {'errors': sum('error' in v for v in arm), 'illegal': sum(v.get('legal') is False for v in arm),
                                 'fatal': sum(v.get('fatal', False) for v in arm),
                                 'exchange_loss_ge2': sum((v.get('exchange_loss') or 0) >= 2 for v in arm),
                                 'queen_exchange_loss_ge4': sum((v.get('queen_exchange_loss') or 0) >= 4 for v in arm),
                                 'forcing_capture': sum(v.get('forced_king_loss_after_capture', False) for v in arm)}
    summary['same_binary_move_flips'] = sum(r['arms']['v35'].get('move') != r['arms']['v35_repeat'].get('move') for r in results)
    summary['candidate_move_flips'] = sum(r['arms']['v35'].get('move') != r['arms']['v37'].get('move') for r in results)
    summary['scope'] = 'Offline, outcome-stratified replay diagnostics; no Elo inference; no recorded continuations after divergence.'
    (args.out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=('freeze', 'run'))
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    ap.add_argument('--since', default='2026-11-01T00:00:00')
    ap.add_argument('--until', default='2026-11-01T10:15:00')
    ap.add_argument('--opponents', nargs='+', default=['Instructors', 'duck', 'HYPOTHERMIA'])
    ap.add_argument('--per-group', type=int, default=2)
    ap.add_argument('--seconds', type=float, default=2.5)
    ap.add_argument('--cores', default='0,1')
    ap.add_argument('--seed', type=int, default=11012026)
    args = ap.parse_args()
    args.out = args.out.resolve()
    (freeze if args.command == 'freeze' else run)(args)


if __name__ == '__main__':
    main()
