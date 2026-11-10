"""One bounded pre-noon v38 replay health snapshot; no training or live policy."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'astra-submissions/analysis/v38-latest-ten-20261110'
sys.path.insert(0, str(ROOT))
from learning.api_client import ApiClient, atomic_write
from learning.ingest import validate_replay
from learning.move_taxonomy import label_game, fen
import chess
sys.path.insert(0, str(ROOT.parent / 'fow-starter'))
import referee as ref

OWN = 'a2c35173659545c99752376a70418438'


def now():
    return datetime.now(timezone.utc).isoformat()


def instant(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    return atomic_write(path, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode())


class Client(ApiClient):
    def _pace(self):
        assert self.requests_made < 30, 'request ceiling reached; no retry run'
        super()._pace()


def course_check(replay):
    board, repetitions = ref.FowBoard(), Counter()
    repetitions[ref.position_key(board)] += 1
    for ply, frame in enumerate(replay['frames']):
        if ply:
            assert ref.outcome(board, repetitions) is None
            move = chess.Move.from_uci(frame['move'])
            assert move in ref.fow_moves(board)
            board.push(move)
            repetitions[ref.position_key(board)] += 1
        text = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        assert text == frame['board']
        assert ref.observation(board, True) == frame['white']
        assert ref.observation(board, False) == frame['black']
    verdict = ref.outcome(board, repetitions)
    if replay['reason'] in {'King capturable', 'Threefold repetition', '50-move rule', 'No legal moves'}:
        assert verdict == (replay['result'], replay['reason'])
    return len(replay['frames'])


def describe(replay, states):
    side = next(i for i, s in enumerate(('white', 'black')) if replay.get(s + 'PlayerId') == OWN)
    key, other = ('white', 'black')[side], ('black', 'white')[side]
    assert replay[key + 'Version'] == 38 and replay.get(other + 'PlayerId') != OWN
    draw = replay['result'] == '1/2-1/2'
    win = not draw and ((replay['result'] == '1-0') == (side == 0))
    frames = replay['frames']
    tags = label_game(replay)
    record = dict(game=replay['id'], created_at=replay['createdAt'], side=key,
                  opponent=replay[other], opponent_version=replay.get(other + 'Version'),
                  result='draw' if draw else 'win' if win else 'loss', reason=replay['reason'],
                  plies=len(frames) - 1, own_tags=tags['counts'][key], opponent_tags=tags['counts'][other],
                  minimum_recorded_clock=min(f['clocks'][side] for f in frames), queen_event=None,
                  terminal_king=None)
    queen, enemy_queen = ('Q', 'q') if side == 0 else ('q', 'Q')
    for ply in range(1, len(frames)):
        if frames[ply]['board'].count(queen) < frames[ply - 1]['board'].count(queen):
            end = min(ply + 3, len(frames) - 1)
            beginning = max(0, ply - 3)
            trade = frames[end]['board'].count(enemy_queen) < frames[beginning]['board'].count(enemy_queen)
            record['queen_event'] = dict(ply=ply, move=frames[ply]['move'],
                classification='queen_exchange_within_three_plies' if trade else
                'no_trade_in_three_plies' if end == ply + 3 else 'no_trade_yet_right_censored',
                first_observed_ply=beginning,
                last_observed_ply=end)
            break
    if record['result'] == 'loss' and replay['reason'] == 'King capturable':
        ply = len(frames) - 1
        assert (ply - 1) % 2 == side
        before, after = states[-2].board, states[-1].board
        king = after.king_square(side)
        move = frames[-1]['move']
        attackers = chess.Board(fen(frames[-1]['board'])).attackers(side == 1, king)
        # Enemy is Black when our side is White, and conversely.
        assert attackers and after.is_attacked(king, 1 - side)
        start_square = chess.parse_square(move[:2])
        record['terminal_king'] = dict(move=move, moving_piece=frames[-2]['board'][start_square],
            king=chess.square_name(king),
            attacked_before=before.is_attacked(before.king_square(side), 1 - side),
            attackers=[dict(square=chess.square_name(s), piece=frames[-1]['board'][s],
                            hidden_before=frames[-2][key][s] == '?',
                            hidden_after=frames[-1][key][s] == '?') for s in attackers],
            true_board_safe_alternatives=[m for m in before.legal_moves() if not before.move_loses_king(m)],
            alternative_scope='Oracle one-ply legality/safety on the true board, not a runtime recommendation.')
    return record, tags


def main():
    plan = json.loads((OUT / 'plan.json').read_text())
    for p, h in plan['dependencies'].items():
        assert sha(p) == h, p
    assert datetime.now(timezone.utc) < instant(plan['stop_before'])
    archive = Path(plan['archive']); archive.mkdir(exist_ok=False)
    assert archive.stat().st_dev == ROOT.stat().st_dev
    client = Client(min_interval=1.2, timeout=30)
    execution = dict(at=now(), status='running', plan_sha256=sha(OUT / 'plan.json'))
    write(OUT / 'execution.json', execution)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('five-minute snapshot wall cap')))
    signal.alarm(300)
    try:
        lb, fetch = client.leaderboard()
        write(OUT / 'leaderboard.json', dict(leaderboard=lb, fetch=fetch.__dict__))
        page, fetch = client.games_page(dict(sort='played', order='desc', limit=10,
                                             colors='any', white='IAmAVirus v38'), None)
        write(OUT / 'listing.json', dict(page=page, fetch=fetch.__dict__))
        rows = page['games']; assert len(rows) == len({r['id'] for r in rows}) == 10
        assert page['sort'] == 'played' and page['order'] == 'desc'
        assert page['summary']['team1']['ambiguous'] == 0
        selected_at = now()
        assert instant(selected_at) < instant(plan['stop_before'])
        write(OUT / 'selected.json', dict(at=selected_at, games=[r['id'] for r in rows],
                                         rule='All ten first-page rows, without outcome or opponent filtering.'))
        records, labels, frames = [], [], 0
        for row in rows:
            assert instant(row['createdAt']) < instant(plan['stop_before'])
            assert datetime.now(timezone.utc) < instant(plan['stop_before'])
            path = archive / (row['id'] + '.json')
            data, fetch = client.get_bytes('/api/games/' + row['id'])
            assert len(data) <= 4 * 1024 * 1024
            path.write_bytes(data)
            replay = json.loads(data)
            for field in ('id', 'createdAt', 'whitePlayerId', 'blackPlayerId', 'whiteVersion', 'blackVersion', 'result', 'reason'):
                assert replay.get(field) == row.get(field), field
            assert len(replay['frames']) == row['plies'] + 1
            states, problems = validate_replay(replay)
            assert not problems, (row['id'], problems)
            frames += course_check(replay)
            record, label = describe(replay, states)
            record.update(replay_sha256=sha(path), fetch=fetch.__dict__)
            records.append(record); labels.append(label)
        assert sum(p.stat().st_size for p in archive.iterdir()) <= 48 * 1024 * 1024
        own = next(p for p in lb['players'] if p['id'] == OWN)
        rank = 1 + sorted(lb['players'], key=lambda p: -(p.get('rating') or 0)).index(own)
        result = dict(at=now(), games=records, counts=dict(Counter(r['result'] for r in records)),
            course_frames=frames, native_and_course_checks_passed=True,
            current_elo=own['rating'], rank=rank, active_version=own['activeVersion'],
            version_record=page['summary']['team1'], version_total=page['summary']['total'],
            requests=client.requests_made, scope=plan['scope'], limitations=plan['limitations'])
        write(OUT / 'taxonomy.json', labels)
        write(OUT / 'result.json', result)
        execution.update(status='complete', frames=frames, result_sha256=sha(OUT / 'result.json'))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as error:
        execution.update(status='failed', error=repr(error))
        raise
    finally:
        signal.alarm(0)
        execution.update(ended_at=now(), requests=client.requests_made)
        write(OUT / 'execution.json', execution)


if __name__ == '__main__':
    main()
