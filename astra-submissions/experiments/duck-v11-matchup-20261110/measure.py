"""Measure when material deficits persist in the v38–Duck v11 matchup."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from statistics import median
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'astra-submissions/analysis'/HERE.name
STORE = ROOT/'data/astra-spool'/HERE.name
LISTINGS = ROOT/'data/astra-spool/v38-metadata-20261110T222700Z'
VALIDATOR = HERE.parent/'last-only-pilot-20261110/build/native-validator.so'
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import _native, ingest
from learning.api_client import ApiClient
from v38_checkpoint import load, stats

spec = importlib.util.spec_from_file_location('course_referee', ROOT.parent/'fow-starter/referee.py')
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
VALUES = dict(p=1, n=3, b=3, r=5, q=9, k=0)
CUTOFF = datetime(2026, 11, 10, 19, 15, tzinfo=timezone.utc)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def material(text, ours):
    white_advantage = sum(VALUES[c.lower()] * (1 if c.isupper() else -1) for c in text if c != '-')
    return white_advantage if ours == 'white' else -white_advantage


def scan(listing, replay):
    for key in ('id', 'result', 'reason', 'white', 'black', 'whiteVersion', 'blackVersion'):
        assert replay[key] == listing[key], (listing['id'], key)
    states, problems = ingest.validate_replay(replay)
    assert not problems, (listing['id'], problems)
    frames = replay['frames']
    assert len(states) == len(frames) == listing['plies']+1
    ours = listing['side']
    color = ours == 'white'
    trajectory = [material(frame['board'], ours) for frame in frames]
    onset = next((i for i in range(1,len(frames)-4) if max(trajectory[i:i+5]) <= -3), None)
    first_crossing = next((i for i,n in enumerate(trajectory) if n <= -3), None)
    detail = None
    safe_replies = None
    hidden_attacker = None
    board = ref.FowBoard()
    repetitions = Counter({ref.position_key(board):1})
    for ply, frame in enumerate(frames):
        if ply:
            move = ref.chess.Move.from_uci(frame['move'])
            assert move in ref.fow_moves(board)
            if ply == onset:
                attacker = board.piece_at(move.from_square)
                taker = 'ours' if board.turn == color else 'duck'
                decision_view = frames[max(0,ply-2)][ours]
                detail = dict(ply=ply, mover=taker, piece=attacker.symbol().lower(),
                    capture=board.is_capture(move), before=trajectory[ply-1], after=trajectory[ply],
                    hidden_before_previous_own_move=taker=='duck' and decision_view[move.from_square]=='?')
            if ply == listing['plies'] and listing['score']==0 and replay['reason']=='King capturable':
                assert board.turn == color
                safe_replies = 0
                for action in ref.fow_moves(board):
                    board.push(action)
                    king = board.king(color)
                    safe_replies += king is not None and not board.is_attacked_by(not color, king)
                    board.pop()
            board.push(move)
            repetitions[ref.position_key(board)] += 1
            if safe_replies is not None:
                king = board.king(color)
                if king is not None:
                    attackers = board.attackers(not color, king)
                    hidden_attacker = any(frames[ply-1][ours][square]=='?' for square in attackers)
        actual = ref.make_frame(board, frame['clocks'], frame['move'])
        assert all(actual[k] == frame[k] for k in ('ply','board','white','black','move')), (listing['id'], ply)
    expected = ref.outcome(board, repetitions)
    if expected is None and listing['plies'] == 1000:
        expected = ('1/2-1/2', 'Move limit reached')
    if ingest.classify_termination(replay['result'], replay['reason']) == 'normal':
        assert expected == (replay['result'], replay['reason'])
    else:
        assert expected is None
    return dict(game=listing['id'], side=ours, score=listing['score'], plies=listing['plies'],
        onset=detail, first_crossing=first_crossing, final_material=trajectory[-1],
        terminal_safe_replies=safe_replies, terminal_hidden_attacker=hidden_attacker)


def main():
    games = [g for g in load(LISTINGS,'games-*.json',38) if g['opponent']=='duck' and g['stratum'][1]==11]
    selected = [g for g in games if datetime.fromisoformat(g['createdAt']) < CUTOFF]
    OUT.mkdir(parents=True, exist_ok=False)
    STORE.mkdir(parents=True, exist_ok=False)
    plan = dict(game_ids=[g['id'] for g in selected], cutoff=CUTOFF.isoformat(),
        deficit_pawns=3, following_plies=4, early_plies=20,
        listing_sha256={p.name:digest(p) for p in LISTINGS.glob('games-*.json')},
        source_sha256=digest(Path(__file__)), referee_sha256=digest(Path(ref.__file__)), validator_sha256=digest(VALIDATOR))
    write(OUT/'plan.json', plan)
    _native.ensure_built = lambda verbose=True: VALIDATOR
    client = ApiClient(min_interval=1.5, cache_dir=STORE/'source', timeout=20)
    rows = []
    raw = {}
    for listing in selected:
        replay, receipt, _ = client.replay(listing['id'])
        rows.append(scan(listing, replay))
        raw[listing['id']] = receipt.sha256
    write(STORE/'matchup-rows.json', rows)
    metrics = {}
    for name, score in (('wins',1),('draws',.5),('losses',0)):
        group = [row for row in rows if row['score']==score]
        onsets = [row['onset'] for row in group if row['onset'] is not None]
        metrics[name] = dict(games=len(group), material_deficit_persists=len(onsets),
            median_onset_ply=median([event['ply'] for event in onsets]) if onsets else None,
            onset_by_ply_20=sum(event['ply']<=20 for event in onsets),
            hidden_capture_onset=sum(event['mover']=='duck' and event['capture'] and
                event['hidden_before_previous_own_move'] for event in onsets),
            terminal_without_safe_reply=sum(row['terminal_safe_replies']==0 for row in group),
            terminal_hidden_attacker=sum(row['terminal_hidden_attacker'] is True for row in group))
    result = dict(at=datetime.now(timezone.utc).isoformat(), matched_before_cutoff=stats(selected),
        total_listing=stats(games), frames=sum(row['plies']+1 for row in rows), metrics=metrics,
        source_replay_sha256=raw, requests=client.requests_made,
        scope='Onset requires a deficit of at least three points in five consecutive frames. Timing is descriptive and true-board derived.')
    write(OUT/'result.json', result)
    print(json.dumps({k:v for k,v in result.items() if k!='source_replay_sha256'}), flush=True)


if __name__ == '__main__':
    main()
