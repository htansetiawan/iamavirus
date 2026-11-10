"""Exercise the recovery path on already used training trajectories."""
import json
import time

from build import OUT, NATIVE, NORMAL_REASONS, codec, connect, load, old, reconstruct, save, sha
from verify import replay_cpp, use_pinned_validator


def main():
    plan = load()
    use_pinned_validator()
    start = time.monotonic()
    original = json.loads((OUT.parent/'capture-fixed-prior-20261110/plan.json').read_text())
    native = old.Native(NATIVE)
    games = frames = 0
    with connect() as db:
        for game in original['games']:
            if game['split'] != 'train':
                continue
            joined = db.execute('select m.moves_sha256,m.moves,d.json from moves m '
                'join listings.metadata d on m.game_id=d.game_id where m.game_id=?', (game['game'],)).fetchone()
            if joined is None:
                continue
            digest, text, raw = joined
            metadata = json.loads(raw)
            if metadata['reason'] not in NORMAL_REASONS:
                continue
            moves = text.split()
            assert digest == game['sequence_sha256'] and moves == game['moves']
            packed, outcome = reconstruct(moves, native)
            assert outcome == (metadata['result'],metadata['reason'])
            cpp, fault = replay_cpp(moves, lambda ply:codec.ROW.unpack_from(packed,ply*codec.ROW.size))
            assert cpp == outcome and fault is None
            frames += len(moves)+1
            games += 1
            if games == 24:
                break
    assert games == 24
    receipt = dict(passed=True, reused_train_games=games, course_c_cpp_frames=frames,
        plan_sha256=sha(OUT/'plan.json'), seconds=time.monotonic()-start)
    save(OUT/'preflight.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
