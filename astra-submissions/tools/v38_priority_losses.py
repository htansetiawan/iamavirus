"""Reproduce the descriptive terminal audit on the frozen v38 priority losses."""
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

out = Path(sys.argv[1])
games = [g for p in out.glob('games-*.json') for g in json.loads(p.read_text())['games']]
refpath = Path('/home/henrytan/git/fow-starter/referee.py')
spec = importlib.util.spec_from_file_location('arena_ref', refpath)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
team = 'a2c35173659545c99752376a70418438'
rows, groups = [], defaultdict(Counter)
for g in games:
    ours = 'white' if g['whitePlayerId'] == team else 'black'
    other = 'black' if ours == 'white' else 'white'
    if g[other] not in ('Greek Gift', 'duck') or g['result'] != ('0-1' if ours == 'white' else '1-0'):
        continue
    p = Path('data/raw/games')/g['id']/'replay.json'
    raw = p.read_bytes(); replay = json.loads(raw)
    assert replay['id'] == g['id'] and replay['reason'] == 'King capturable'
    board = ref.FowBoard(); frames = replay['frames']
    for frame in frames:
        if frame['move']:
            move = ref.chess.Move.from_uci(frame['move'])
            assert move in ref.fow_moves(board)
            board.push(move)
        assert ref.observation(board, True) == frame['white']
        assert ref.observation(board, False) == frame['black']
    last = board.pop(); loser = ours == 'white'; assert board.turn == loser
    view = frames[-2][ours]; piece = board.piece_at(last.from_square)
    capture = board.is_capture(last)
    attacked = board.is_attacked_by(not loser, board.king(loser)); safe = []
    for move in ref.fow_moves(board):
        board.push(move); king = board.king(loser)
        if king is not None and not board.is_attacked_by(not loser, king):
            safe.append(move.uci())
        board.pop()
    board.push(last)
    attackers = list(board.attackers(not loser, board.king(loser))); assert attackers
    kind = ('king_capture_into_attack' if capture else 'king_move_into_attack') if piece.piece_type == ref.chess.KING else ('ignored_existing_attack' if attacked else 'opened_attack_on_king')
    hidden = [sq for sq in attackers if view[sq] == '?']
    count = groups[g[other]]; count['losses'] += 1; count[kind] += 1
    count['hidden_attacker'] += bool(hidden); count['no_true_safe_reply'] += not bool(safe)
    rows.append(dict(game=g['id'], opponent=g[other], opponent_version=g[other+'Version'],
                     side=ours, plies=g['plies'], kind=kind, truth_safe_reply_count=len(safe),
                     truth_safe_replies=safe, hidden_attacker=bool(hidden),
                     attackers=[dict(square=ref.chess.square_name(sq), piece=board.piece_at(sq).symbol(),
                                     hidden=view[sq]=='?') for sq in attackers],
                     last_move=last.uci(), min_clock=min(f['clocks'][0 if loser else 1] for f in frames),
                     tail=[f['move'] for f in frames[-11:]], replay_sha256=hashlib.sha256(raw).hexdigest()))
assert len(rows) == 26
result = dict(scope='All 26 recorded v38 losses against Greek Gift/duck in the frozen318-game snapshot. Referee checks every move and both observations. Terminal descriptions only; safe moves use hidden truth and are not an executable policy.',
              groups={k:dict(v) for k,v in groups.items()}, rows=rows,
              referee_sha256=hashlib.sha256(refpath.read_bytes()).hexdigest())
path = out/'priority-losses.json'
if path.exists():
    assert json.loads(path.read_text()) == result, 'Audit no longer reproduces original receipt'
    print('Verified original priority-loss receipt; no overwrite.')
else:
    with path.open('x') as handle:
        json.dump(result, handle, indent=2); handle.write('\n')
    print(json.dumps(result['groups']))
