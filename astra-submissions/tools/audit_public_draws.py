#!/usr/bin/env python3
"""Snapshot one arena version's draws and verify conversion opportunities.

GET-only, paced by the shared public client. Reuse completed public replay
cache; never edit it. This is a true-board audit, not a bot or an Elo estimate.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from monitor_arena import Client, TEAM, result_for_team


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def inspect(game, referee, chess):
    side = 'white' if game['whitePlayerId'] == TEAM else 'black'
    color = side == 'white'
    win = '1-0' if color else '0-1'
    loss = '0-1' if color else '1-0'
    board = referee.FowBoard()
    reps = Counter({referee.position_key(board): 1})
    seen = {referee.position_key(board): [0]}
    own_states, missed_wins = [], []
    values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
    def material(b):
        return sum(values[p.symbol().lower()] * (1 if p.color == color else -1)
                   for p in b.piece_map().values())
    for ply, frame in enumerate(game['frames']):
        if frame['ply'] != ply:
            raise ValueError('Nonconsecutive frames')
        if ply:
            if referee.outcome(board, reps):
                raise ValueError('Replay continues beyond rules terminal')
            move = chess.Move.from_uci(frame['move'])
            legal = referee.fow_moves(board)
            if move not in legal:
                raise ValueError(f'Illegal recorded move at {ply}')
            if board.turn == color:
                alternatives = []
                for candidate in legal:
                    child = board.copy(); child.push(candidate)
                    counts = reps.copy(); counts[referee.position_key(child)] += 1
                    outcome = referee.outcome(child, counts)
                    alternatives.append({'move': candidate.uci(), 'outcome': outcome})
                wins = [r['move'] for r in alternatives if r['outcome'] and r['outcome'][0] == win]
                safe = [r['move'] for r in alternatives if not r['outcome'] or r['outcome'][0] != loss]
                live = [r['move'] for r in alternatives if not r['outcome']]
                row = {'ply': ply - 1, 'played': move.uci(), 'true_material_lead': material(board),
                       'winning_moves': wins, 'safe_moves': safe, 'live_moves': live,
                       'draw_moves': [r['move'] for r in alternatives if r['outcome'] and r['outcome'][0] == '1/2-1/2'],
                       'position_key_occurrences': list(seen[referee.position_key(board)])}
                own_states.append(row)
                if wins and move.uci() not in wins:
                    missed_wins.append(row)
            board.push(move)
            key = referee.position_key(board)
            reps[key] += 1
            seen.setdefault(key, []).append(ply)
        elif frame['move'] is not None:
            raise ValueError('Initial move is not null')
        actual = ''.join(board.piece_at(i).symbol() if board.piece_at(i) else '-' for i in range(64))
        if frame['board'] != actual:
            raise ValueError(f'Board mismatch at {ply}')
        for name, c in [('white', chess.WHITE), ('black', chess.BLACK)]:
            if referee.observation(board, c) != frame[name]:
                raise ValueError(f'Observation mismatch at {ply}/{name}')
    ending = referee.outcome(board, reps)
    if not ending or ending[0] != game['result'] or ending[1] != game['reason']:
        raise ValueError(f'Ending differs: referee={ending}, recorded={game["result"],game["reason"]}')
    final_ply = len(game['frames']) - 1
    final_mover = not board.turn
    key = referee.position_key(board)
    last = own_states[-1] if own_states else None
    return {'game': game['id'], 'side': side, 'opponent': game['black' if color else 'white'],
            'opponent_version': game['blackVersion' if color else 'whiteVersion'],
            'plies': final_ply, 'reason': game['reason'], 'final_mover_is_us': final_mover == color,
            'final_true_material_lead': material(board), 'final_key_occurrences': seen[key],
            'closing_cycle_moves': [f['move'] for f in game['frames'][seen[key][-2]+1:]] if len(seen[key])>1 else [],
            'last_own_decision': last, 'missed_immediate_wins': missed_wins,
            'own_decisions': len(own_states), 'frames_verified': len(game['frames']),
            'interpretation': 'True-board alternatives; not proof that one common action works in every observation-consistent world.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version', type=int, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--cache', type=Path, default=Path('data/raw/games'))
    ap.add_argument('--kit', type=Path, default=Path.home()/'git/fow-starter')
    args = ap.parse_args()
    drive = Path('/media/henrytan/seagate')
    if args.output.resolve().is_relative_to(drive) and not drive.is_mount():
        raise ValueError('External disk is not mounted')
    if args.output.exists():
        raise ValueError('Use a new immutable output directory')
    args.output.mkdir(parents=True)
    sys.path.insert(0, str(args.kit))
    import chess
    import referee
    client = Client()
    params = dict(player=TEAM, white=f'IAmAVirus v{args.version}', colors='any',
                  sort='played', order='desc', limit=100)
    save(args.output/'plan.json', {'created_at': datetime.now(timezone.utc).isoformat(),
         'selection': 'All completed draws for this exact team version in one paginated snapshot; no candidate-policy queries.',
         'params': params, 'tool_sha256': digest(Path(__file__).read_bytes()),
         'referee_sha256': digest((args.kit/'referee.py').read_bytes()),
         'scope': 'Fresh diagnostic data, not an untouched training holdout or a winning-strategy certificate.'})
    games, provenance, cursors = [], [], set()
    for page_number in range(20):
        page, fetched = client.get('/api/games', params)
        save(args.output/f'page-{page_number}.json', page)
        provenance.append(fetched)
        games.extend(page['games'])
        cursor = page['nextCursor']
        if not cursor:
            break
        if cursor in cursors:
            raise ValueError('Cursor repeated')
        cursors.add(cursor); params['cursor'] = cursor
    else:
        raise ValueError('Page bound reached; partial snapshot rejected')
    if len({g['id'] for g in games}) != len(games):
        raise ValueError('Duplicate game in snapshot')
    if any(result_for_team(g)['arena_version'] != args.version for g in games):
        raise ValueError('Search returned the wrong team version')
    records = [result_for_team(g) for g in games]
    save(args.output/'games.json', games)
    rows, errors = [], []
    for game in games:
        if game['result'] != '1/2-1/2':
            continue
        cached = args.cache/game['id']/'replay.json'
        if cached.exists():
            raw = cached.read_bytes(); replay = json.loads(raw)
            record = {'cache': str(cached.resolve()), 'sha256': digest(raw)}
        else:
            replay, record = client.get('/api/games/'+game['id'])
        if replay['id'] != game['id']:
            raise ValueError('Cached ID mismatch')
        for k in ['whitePlayerId','blackPlayerId','whiteVersion','blackVersion','result','reason','createdAt']:
            if replay[k] != game[k]:
                raise ValueError(f'Cached metadata differs: {game["id"]}/{k}')
        path = args.output/(game['id']+'.json')
        save(path, replay)
        provenance.append(dict(record, game=game['id'], frozen_sha256=digest(path.read_bytes())))
        try:
            row = inspect(replay, referee, chess)
            row.update(replay=str(path.resolve()), replay_sha256=digest(path.read_bytes()))
            rows.append(row)
        except ValueError as exc:
            errors.append({'game': game['id'], 'error': str(exc)})
        print(json.dumps({'game':game['id'], 'valid':len(rows), 'errors':len(errors)}), flush=True)
    save(args.output/'fetch.json', provenance)
    report = {'created_at': datetime.now(timezone.utc).isoformat(), 'version':args.version,
              'classification':'draw-conversion true-board audit; no policy or Elo estimate',
              'record':dict(Counter(r['result'] for r in records)),
              'games_in_snapshot':len(games), 'draws':sum(r['result']=='D' for r in records),
              'validated_draws':len(rows), 'errors':errors, 'rows':rows,
              'plan_sha256':digest((args.output/'plan.json').read_bytes()),
              'snapshot_sha256':digest((args.output/'games.json').read_bytes()),
              'positive_material_draws':sum(r['final_true_material_lead']>0 for r in rows),
              'three_point_lead_draws':sum(r['final_true_material_lead']>=3 for r in rows),
              'missed_immediate_win_games':sum(bool(r['missed_immediate_wins']) for r in rows)}
    save(args.output/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
