"""Read-only analysis of completed frozen-gate games and captured stderr tails.

Uses truth only for post-game diagnosis, never for a bot decision. No engines run.
"""
import collections
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path.home() / 'git/fow-starter'))
import chess
import referee

IDS = ['v36r3-vs-v35', 'v36r3-vs-misty', 'v35-vs-misty-r3']
VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
          chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def logs(text):
    block = []
    first = True
    for line in text.splitlines():
        block.append(line)
        if line.startswith('mist: n='):
            fields = dict(re.findall(r'(\|P\||\w+)=([^ ]+)', line))
            fields['vetoes'] = [s.split()[-1] for s in block if s.startswith('mist: piece veto ')]
            fields['piece_guard'] = any('piece guard left out' in s for s in block)
            fields['fallback'] = [s for s in block if 'yields' in s or 'not legal' in s or 'no belief' in s]
            fields['block_complete'] = int(fields['n']) == 1 or not first
            yield fields
            block = []
            first = False


def fatal(board, mover):
    king = board.king(mover)
    return king is None or board.is_attacked_by(not mover, king)


def capture_events(board, us, targets, got, threshold):
    events = []
    for move in referee.fow_moves(board):
        victim = board.piece_at(move.to_square)
        if not victim or victim.color != us or victim.piece_type not in targets:
            continue
        capturer = board.piece_type_at(move.from_square)
        after = board.copy(stack=False)
        after.push(move)
        gain = VALUES[victim.piece_type]
        if after.is_attacked_by(us, move.to_square):
            gain -= VALUES[capturer]
        if gain - got >= threshold:
            events.append({'reply': move.uci(), 'net': gain - got,
                           'opponent_loses_immediately': fatal(after, not us)})
    return events


def piece_event(board, move):
    us = board.turn
    victim = board.piece_at(move.to_square)
    if victim and victim.piece_type == chess.KING:
        return None
    got = VALUES[victim.piece_type] if victim else int(board.is_en_passant(move))
    after = board.copy(stack=False)
    after.push(move)
    if fatal(after, us):
        return None
    if capture_events(after, us, {chess.QUEEN}, got, 4):
        return None  # same K/Q/P partition as the candidate
    events = capture_events(after, us, {chess.ROOK, chess.BISHOP, chess.KNIGHT}, got, 3)
    if events and all(e['opponent_loses_immediately'] for e in events):
        return events
    return None


def main():
    rows = [json.loads(s) for s in (ROOT/'data/arena_local/games.jsonl').read_text().splitlines() if s.strip()]
    rows = [r for r in rows if r.get('matchup') in IDS]
    out = {'classification': 'interim descriptive diagnosis; not a causal A/B or gate verdict',
           'games': [], 'source_semantics_cases': [], 'metrics': {}}
    all_logs = collections.defaultdict(list)
    for row in rows:
        replay = json.loads((ROOT/row['replay']).read_text())
        side = row['a_colour']; us = side == 'white'
        board = referee.FowBoard()
        boards = [board.copy()]
        for frame in replay['frames'][1:]:
            board.push(chess.Move.from_uci(frame['move']))
            boards.append(board.copy())
        records = list(logs(replay.get('privateDiagnostics', {}).get(side, '')))
        detail = {'matchup': row['matchup'], 'pair': row['pair'], 'color': side,
                  'score': row['a_score'], 'replay': row['replay'], 'plies': row['plies'],
                  'reason': row['reason'], 'captured_decision_records': len(records),
                  'first_captured_decision': int(records[0]['n']) if records else None,
                  'piece_veto_decisions': 0, 'piece_veto_moves': 0,
                  'fallback_logs': []}
        for record in records:
            n = int(record['n']); ply = 2*(n-1) + (0 if us else 1)
            assert ply+1 < len(boards)
            assert replay['frames'][ply+1]['move'] == record['move'], (row, record)
            record['ply'] = ply
            record['game'] = row['replay']
            record['result'] = row['a_score']
            all_logs[row['matchup']].append(record)
            detail['piece_veto_decisions'] += int(record['piece_guard'])
            detail['piece_veto_moves'] += len(record['vetoes'])
            detail['fallback_logs'] += record['fallback']
            if not record['block_complete']:
                continue
            for uci in record['vetoes']:
                move = chess.Move.from_uci(uci)
                if move not in referee.fow_moves(boards[ply]):
                    continue
                events = piece_event(boards[ply], move)
                if events:
                    out['source_semantics_cases'].append({
                        'replay': row['replay'], 'matchup': row['matchup'], 'score': row['a_score'],
                        'decision': n, 'ply': ply, 'vetoed': uci, 'played': record['move'],
                        'fen': boards[ply].fen(), 'board': replay['frames'][ply]['board'],
                        'castling_rights': boards[ply].castling_rights,
                        'ep_square': boards[ply].ep_square, 'color': side,
                        'false_piece_events_on_truth': events})
        if row['a_score'] == 0 and row['reason'] == 'King capturable':
            end = boards[-1]; pre = replay['frames'][-2]; k = end.king(us)
            detail['terminal'] = {
                'move': replay['frames'][-1]['move'],
                'king': chess.square_name(k) if k is not None else None,
                'attackers': [{'square': chess.square_name(s), 'piece': end.piece_at(s).symbol(),
                               'visible_before': pre[side][s] != '?'} for s in end.attackers(not us, k)] if k is not None else [],
                'true_material_lead': sum(VALUES[p.piece_type]*(1 if p.color == us else -1) for p in end.piece_map().values()),
                'last_decision': records[-1] if records else None}
        out['games'].append(detail)
    for mid, recs in all_logs.items():
        out['metrics'][mid] = {}
        for phase, lower, upper in [('opening',1,10),('middle',11,20),('later',21,1000)]:
            rr = [r for r in recs if lower <= int(r['n']) <= upper]
            out['metrics'][mid][phase] = {'captured_decisions':len(rr),
                'piece_guard_active': sum(r['piece_guard'] for r in rr),
                'median_nodes':statistics.median(int(r['nodes']) for r in rr) if rr else None,
                'median_root_moves':statistics.median(int(r['moves']) for r in rr) if rr else None,
                'median_clock':statistics.median(float(r['clock']) for r in rr) if rr else None}
    target = Path(__file__).with_name('diagnosis.json')
    target.write_text(json.dumps(out,indent=2)+'\n')
    print('games',len(rows),'suspect truth-world vetoes',len(out['source_semantics_cases']))
    print(json.dumps(out['metrics'],indent=2))
    for g in out['games']:
        if g['matchup']=='v36r3-vs-misty' and g['score']==0:
            print('LOSS',g['pair'],g['color'],g['terminal']['move'],g['terminal']['attackers'],
                  'material',g['terminal']['true_material_lead'],
                  'veto turns',g['piece_veto_decisions'],'/',g['captured_decision_records'])
    for c in out['source_semantics_cases'][:10]:
        print('SUSPECT',c['replay'],c['decision'],c['vetoed'],'played',c['played'],c['false_piece_events_on_truth'])


if __name__ == '__main__':
    main()
