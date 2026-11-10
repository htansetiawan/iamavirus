"""Independent referee and stored-byte audit of a bounded target refresh."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT.parent/'fow-starter')]
import referee as ref
from learning.histories import classify_termination
from learning.move_taxonomy import aggregate, label_game


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    os.sched_setaffinity(0, {6})
    receipt = json.loads((args.out/'receipt.json').read_text())
    for path, digest in receipt['dependencies'].items():
        assert sha(Path(path).read_bytes()) == digest, path
    assert sha((ROOT/'astra-submissions/tools/refresh_target_intel.py').read_bytes()) == receipt['source_sha256']
    with (args.raw/'accepted.jsonl').open('rb') as handle:
        prefix = handle.read(receipt['accepted_prefix']['bytes'])
        assert sha(prefix) == receipt['accepted_prefix']['sha256']
        old = {json.loads(line)['id'] for line in prefix.splitlines()}
        tail = handle.read()
    tail = tail[:tail.rfind(b'\n')+1]
    added = {json.loads(line)['id']: json.loads(line) for line in tail.splitlines()}
    new = {r['id']: r for r in receipt['new_games']}
    assert len(new) == receipt['counts'].get('accepted', 0)
    assert not set(new) & old
    assert all(g in added for g in new)
    targets = [json.loads(p.read_text()) for p in args.out.glob('*.json')
               if p.name not in ('leaderboard.json', 'receipt.json', 'summary.json', 'audit.json')]
    targets = [t for t in targets if 'games_used' in t]
    assert len(targets) == receipt['completed_targets']
    required = dict(new)
    for target in targets:
        for item in target['games_used']:
            if item['id'] in required:
                assert required[item['id']]['replay_sha256'] == item['replay_sha256']
            required[item['id']] = item
    checks, labelled, frames = [], {}, 0
    for game_id, expected in required.items():
        path = args.raw/'games'/game_id/'replay.json'
        data = path.read_bytes()
        assert sha(data) == expected['replay_sha256'], game_id
        game = json.loads(data)
        board = ref.FowBoard()
        repetitions = Counter({ref.position_key(board): 1})
        previous = None
        increment = game.get('timeControl', {}).get('incrementSeconds')
        for index, frame in enumerate(game['frames']):
            assert frame['ply'] == index
            if index:
                side = 0 if board.turn else 1
                move = ref.chess.Move.from_uci(frame['move'])
                assert move in ref.fow_moves(board), (game_id, index)
                board.push(move)
                repetitions[ref.position_key(board)] += 1
                assert frame['clocks'][1-side] == previous[1-side]
                if increment is not None:
                    assert frame['clocks'][side] <= previous[side]+increment+1e-6
            else:
                assert frame['move'] is None
            assert len(frame['clocks']) == 2 and all(math.isfinite(t) and t >= 0 for t in frame['clocks'])
            assert ref.observation(board, True) == frame['white'], (game_id, index, 'white')
            assert ref.observation(board, False) == frame['black'], (game_id, index, 'black')
            assert ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)) == frame['board']
            if index < len(game['frames'])-1:
                assert ref.outcome(board, repetitions) is None
            previous = frame['clocks']
            frames += 1
        if classify_termination(game['result'], game['reason']) == 'normal':
            terminal = ref.outcome(board, repetitions)
            if terminal is None and len(game['frames']) == 1001:
                terminal = ('1/2-1/2', 'Move limit reached')
            assert terminal == (game['result'], game['reason']), game_id
        moves_hash = sha(' '.join(f['move'] for f in game['frames'][1:]).encode())
        if game_id in new:
            assert moves_hash == new[game_id]['moves_sha256'] == added[game_id]['moves_sha256']
            assert 'a2c35173659545c99752376a70418438' not in (game['whitePlayerId'], game['blackPlayerId'])
        labelled[game_id] = label_game(game)
        meta = json.loads((path.parent/'fetch_metadata.json').read_text())
        checks.append(dict(id=game_id, stored_sha256=sha(data), moves_sha256=moves_hash,
                           transport_sha256=meta.get('replay', {}).get('sha256'), frames=len(game['frames'])))
    for target in targets:
        sides = {r['id']: r['side'] for r in target['games_used']}
        fresh = aggregate([labelled[r['id']] for r in target['games_used']], lambda r: sides[r['id']])
        assert fresh == target['taxonomy'], target['team']
        for item in target['games_used']:
            game = json.loads((args.raw/'games'/item['id']/'replay.json').read_text())
            assert game[item['side']+'Version'] == target['active_version']
            assert game[item['side']+'PlayerId'] == target['team_id']
    output = dict(at=datetime.now(timezone.utc).isoformat(), collection_completed=receipt['completed'],
                  audited_games=len(checks), new_games=len(new), referee_frames=frames,
                  completed_targets=[t['team'] for t in targets], taxonomy_recomputed=True,
                  initial_prefix_verified=True, checks=checks,
                  auditor_sha256=sha(Path(__file__).read_bytes()), referee_sha256=sha(Path(ref.__file__).read_bytes()),
                  receipt_sha256=sha((args.out/'receipt.json').read_bytes()),
                  scope='Stored-byte, move-hash and independent referee audit of all new and taxonomized replays. '
                        'Existing transport SHA describes the original HTTP encoding, not reserialized stored JSON. '
                        'Not a playing-strength estimate, model fit or full-time-window coverage claim.')
    with (args.out/'audit.json').open('x') as handle:
        json.dump(output, handle, indent=2)
        handle.write('\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'checks'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, default=ROOT/'data/raw')
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args())
