"""Exercise the extended diagnostic driver on synthetic openings, not panel scores."""
import json
from pathlib import Path
import subprocess

from prepare import OUT, BUILD, load_ref, inspect_game, MoveList, NB, SEEDS, sha, save
from run import environment, stable
import ctypes


def main():
    ref = load_ref(); frontend = ctypes.CDLL(str(NB / 'adapter.so')); frontend.fow_init()
    frontend.view_moves.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint64, ctypes.POINTER(MoveList)]
    board = ref.FowBoard(); frames = []
    opening = ('e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'g8f6', 'e1g1', 'f8c5')
    for ply in range(len(opening) + 1):
        if ply:
            move = ref.chess.Move.from_uci(opening[ply - 1]); assert move in ref.fow_moves(board); board.push(move)
        frames.append(dict(ply=ply, move=opening[ply - 1] if ply else None,
                           board=''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)),
                           white=ref.observation(board, True), black=ref.observation(board, False)))
    results = []; updates = 0
    for us in (0, 1):
        lines, bad, count = inspect_game(ref, frontend, dict(id='fx000000', frames=frames), us)
        assert not bad
        path = OUT / f'synthetic-{us}.trace'; path.write_text('\n'.join(lines) + '\n')
        for seed_index, seed in enumerate(SEEDS):
            peers = {}
            for arm in ('original', 'zero', 'learned'):
                binary = BUILD / ('trace-original' if arm == 'original' else 'trace-adapter')
                command = [str(binary), str(path), str(seed)]
                r = subprocess.run(command, capture_output=True, text=True, timeout=20, env=environment(arm))
                label = f'synthetic-{us}-s{seed_index}-{arm}'
                (OUT / (label + '.stdout')).write_text(r.stdout); (OUT / (label + '.stderr')).write_text(r.stderr)
                assert r.returncode == 0, r.stderr
                rows = [json.loads(line) for line in r.stdout.splitlines()]
                assert len(rows) == len(opening) - 1
                assert all(row['matches'] and not row['guard_bad_moves'] for row in rows)
                assert all(row['king_label'] == 0 and row['queen_label'] == 0 for row in rows)
                peers[arm] = rows; updates += len(rows)
                results.append(dict(name=label, code=r.returncode, rows=len(rows), stdout_sha256=sha(OUT / (label + '.stdout'))))
            assert stable(peers['original']) == stable(peers['zero'])
    save(OUT / 'preflight.json', dict(passed=True, synthetic_course_frames=len(frames), calls=results,
                                    synthetic_update_rows=updates, guard_unit_cases=5,
                                    scope='Synthetic opening schema, both observers/seeds, true-state inclusion, zero equality and read-only guard diagnostics. No panel belief update or predictive/posterior quality score.'))
    print(json.dumps(dict(passed=True, calls=len(results), updates=updates)), flush=True)


if __name__ == '__main__': main()
