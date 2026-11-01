#!/usr/bin/env python3
"""Preserve queen captures, recoveries and exposure controls as offline cases.

Recorded outcomes describe the original line only. The independent exchange
probe tests the played action and never follows recorded replies after a change.
This creates a diagnostic collection, not population calibration or a new gate.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import ingest, move_taxonomy
from fresh_taxonomy_gate import exchange_probe, material, protocol


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--since', required=True)
    ap.add_argument('--until', required=True)
    ap.add_argument('--team', default='IAmAVirus')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    raw = ROOT/'data/raw'
    index = raw/'accepted.jsonl'
    # The complete cached time window is used, not the subset newly downloaded:
    # already-cached games must not vanish from the sampling frame.
    index_bytes = index.read_bytes()
    indexed = {r['id']: r for r in map(json.loads, index_bytes.splitlines())}
    games = sorted((r for r in indexed.values()
                    if args.since <= (r.get('createdAt') or '') < args.until
                    and args.team in (r.get('white'), r.get('black'))), key=lambda r:r['id'])
    oracle_path = ROOT/'astra-submissions/experiments/persistent-response-20261101/review.py'
    spec = importlib.util.spec_from_file_location('queen_case_oracle', oracle_path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    ref = oracle.ref
    cases = []; provenance = []; cohorts = Counter(); frames_checked = transitions = 0
    for game in games:
        path = raw/'games'/game['id']/'replay.json'
        replay = json.loads(path.read_text())
        states, errors = ingest.validate_replay(replay)
        assert not errors, (game['id'], errors)
        side = 0 if replay['white'] == args.team else 1
        key = ('white', 'black')[side]; enemy = ('black', 'white')[side]
        queen = 'Q' if side == 0 else 'q'
        frames = replay['frames']
        tags = {m['ply']-1:m['tags'] for m in move_taxonomy.label_game(replay)['moves'] if m['side']==side}
        candidates = defaultdict(list)
        for ply in range(side, len(states)-1, 2):
            if queen not in frames[ply+1]['board']:
                continue
            # Full three-ply labels require the opponent reply AND our response.
            # Terminal/censored exchanges are retained as a separate category.
            captured = (ply+2 < len(frames)
                        and frames[ply+2]['board'].count(queen) < frames[ply+1]['board'].count(queen))
            horizons = {str(h): material(frames[ply]['board'], side)-material(frames[ply+h]['board'], side)
                        if ply+h < len(frames) else None for h in (2, 3, 5)}
            if captured:
                label = ('queen_capture_censored' if horizons['3'] is None else
                         'recorded_queen_net_ge4' if horizons['3'] >= 4 else
                         'recorded_queen_net_lt4')
            elif 'queen_exposed_unseen' in tags[ply]:
                label = 'exposed_without_next_reply_capture'
            elif 8 <= ply <= 70 and queen in frames[ply]['board']:
                label = 'ordinary_queen_present_control'
            else:
                continue
            candidates[label].append(dict(game=game['id'], ply=ply, side=key,
                played=frames[ply+1]['move'], cohort=label, tags=tags[ply],
                recorded_net_loss=horizons, recorded_queen_captured_next_reply=captured))
        selected = []
        for cohort, entries in sorted(candidates.items()):
            # All recorded queen captures, plus one stable-hash example of each
            # control per game. No policy outcome enters this selection.
            entries.sort(key=lambda c:hashlib.sha256(f"queen-216:{c['game']}:{c['ply']}".encode()).hexdigest())
            selected.extend(entries if cohort.startswith(('recorded_', 'queen_capture_')) else entries[:1])
        if not selected:
            continue
        board = ref.FowBoard(); history = Counter({ref.position_key(board):1}); ref_states = []
        for ply, frame in enumerate(frames):
            if ply:
                assert ref.outcome(board, history) is None
                assert frame['move'] in {m.uci() for m in ref.fow_moves(board)}
                board.push_uci(frame['move']); history[ref.position_key(board)] += 1
            frame_ref = ref.make_frame(board, frame['clocks'])
            for field in ('board', 'white', 'black'):
                assert frame_ref[field] == frame[field], (game['id'], ply, field)
            assert ref.outcome(board, history) == states[ply].outcome()
            ref_states.append((board.copy(), history.copy())); frames_checked += 1
        provenance.append(dict(game=game['id'], replay_path=str(path.relative_to(ROOT)), replay_sha256=sha(path),
            created_at=game['createdAt'], side=key, version=replay.get(key+'Version'),
            opponent=replay[enemy], opponent_version=replay.get(enemy+'Version'), result=replay['result']))
        for case in sorted(selected, key=lambda c:c['ply']):
            ply = case['ply']; label = exchange_probe(states[ply], case['played'])
            independent, checks = oracle.probe(*ref_states[ply], case['played'], side)
            transitions += checks
            for field in ('legal', 'fatal', 'exchange_loss', 'queen_exchange_loss', 'forced_king_loss_after_capture'):
                assert label.get(field) == independent.get(field), (game['id'], ply, field, label, independent)
            feed, forced = protocol(replay, ply, side)
            folder = args.out/'inputs'; folder.mkdir(exist_ok=True)
            feed_path = folder/f"{game['id']}-{ply}.txt"; feed_path.write_text(feed)
            forced_path = folder/f"{game['id']}-{ply}.forced.json"
            forced_path.write_text(json.dumps(forced)+'\n')
            case.update(played_probe=label, input_path=str(feed_path.relative_to(ROOT)), input_sha256=sha(feed_path),
                        forced_path=str(forced_path.relative_to(ROOT)), forced_sha256=sha(forced_path),
                        version=replay.get(key+'Version'), opponent=replay[enemy], opponent_version=replay.get(enemy+'Version'))
            cases.append(case); cohorts[case['cohort']] += 1
    result = dict(created_at=datetime.now(timezone.utc).isoformat(), since=args.since, until=args.until, team=args.team,
        source_sha256=sha(Path(__file__)), accepted_index_sha256=hashlib.sha256(index_bytes).hexdigest(), oracle_sha256=sha(oracle_path),
        referee_sha256=sha(oracle.REFPATH), probe_sha256=sha(ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py'),
        taxonomy_sha256=sha(ROOT/'learning/move_taxonomy.py'), eligible_games=len(games), games=provenance, cases=cases,
        cohort_counts=dict(cohorts), independent_frames=frames_checked, independent_transitions=transitions,
        played_immediate_king_losses=sum(c['played_probe']['fatal'] for c in cases),
        played_queen_exchange_loss_ge4=sum((c['played_probe']['queen_exchange_loss'] or 0)>=4 for c in cases),
        scope='Selected offline diagnostics, not an unbiased sample or a new promotion gate. No candidate is run or changed. Inputs contain only permitted views, clocks and separately forced own moves. Truth labels remain outside bot input.',
        limitations=['Recorded horizons describe the recorded line only; cannot be used after candidate divergence.',
                     'The exchange probe covers one opponent capture and one best safe response; quiet moves and longer combinations remain outside its scope.',
                     'A recorded low net loss or unpunished exposure is not proof of a sound move; inspect the counterfactual probe separately.',
                     'Repeated decisions from a game are correlated. Cases may overlap earlier inspected development games.'])
    (args.out/'cases.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    summary={k:result[k] for k in ('eligible_games','cohort_counts','independent_frames','independent_transitions','played_immediate_king_losses','played_queen_exchange_loss_ge4')}
    summary.update(games=len(provenance), cases=len(cases))
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
