"""Check frozen sources, input privacy, course trace consistency and cost sums."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'astra-submissions/analysis/belief-sort-cost-20261110'
sys.path.insert(0, str(ROOT.parent/'fow-starter'))
import referee as ref


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = json.loads((OUT/'plan.json').read_text())
    completion = json.loads((OUT/'completion.json').read_text())
    assert completion['state'] == 'complete' and completion['completed'] == 8
    for path, digest in plan['dependencies'].items():
        assert sha(path) == digest, path
    for source in (HERE/'build/src').iterdir():
        assert source.read_bytes() == (Path(plan['parent'])/'src'/source.name).read_bytes()
    commands = json.loads((OUT/'preflight.json').read_text())['commands']
    redirected = [c for c in commands if '-Dqsort=astra_qsort' in c]
    assert len(redirected) == 1 and str(HERE/'build/src/belief.c') in redirected[0]
    frames, cpu, by_width, maxima, counts = 0, 0, Counter(), Counter(), Counter()
    rows = []
    for case in plan['cases']:
        folder = OUT/case['id']
        row = json.loads((folder/'result.json').read_text())
        assert row['case'] == case and row['exit_code'] == 0
        for name, digest in row['files'].items():
            assert sha(folder/name) == digest, (case['id'], name)
        replay = json.loads(Path(case['replay_path']).read_text())
        board = ref.FowBoard()
        side = ['white', 'black'].index(case['side'])
        expected = ['fow', f"{'w' if side == 0 else 'b'} 180 2"]
        forced = []
        for ply, frame in enumerate(replay['frames'][:case['ply']+1]):
            if ply:
                move = ref.chess.Move.from_uci(frame['move'])
                assert move in ref.fow_moves(board)
                board.push(move)
            assert ref.observation(board, True) == frame['white']
            assert ref.observation(board, False) == frame['black']
            assert ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)) == frame['board']
            expected.append(frame[case['side']])
            if ply % 2 == side:
                expected.append(str(frame['clocks'][side]))
                move = ref.chess.Move.from_uci(replay['frames'][ply+1]['move'])
                assert move in ref.fow_moves(board)
                forced.append(move.uci())
            frames += 1
        assert (folder/'input.txt').read_text() == '\n'.join(expected)+'\n'
        assert re.findall(r'^move (\S+)$', (folder/'stdout.txt').read_text(), re.M) == forced
        stderr = (folder/'stderr.txt').read_text()
        profile = json.loads(re.findall(r'^astra-sort-profile: (.*)$', stderr, re.M)[0])
        assert profile == row['profile']
        assert 'nodes=' not in stderr and 'stockfish ready' not in stderr
        cost = sum(b['thread_cpu_ns'] for b in profile['buckets'])
        assert 0 <= cost <= profile['process_cpu_ns']
        assert abs(cost/profile['process_cpu_ns']-row['sort_cpu_share']) < 1e-14
        cpu += profile['process_cpu_ns']
        for b in profile['buckets']:
            by_width[b['width']] += b['thread_cpu_ns']
            maxima[b['width']] = max(maxima[b['width']], b['max_elements'])
            counts[b['width']] += b['calls']
        rows.append(dict(id=case['id'], cpu_seconds=profile['process_cpu_ns']/1e9,
                         sort_share=row['sort_cpu_share'], result_sha256=sha(folder/'result.json')))
    share = sum(by_width.values())/cpu
    trigger = plan['kernel_experiment_trigger']
    advance = (share >= trigger['aggregate_sort_cpu_share_min']
               and max(maxima.values()) >= trigger['max_array_elements_min'])
    result = dict(at=datetime.now(timezone.utc).isoformat(), completed=8, source_frames=frames,
                  process_cpu_seconds=cpu/1e9, sort_cpu_seconds={str(k): v/1e9 for k, v in by_width.items()},
                  sort_cpu_shares={str(k): v/cpu for k, v in by_width.items()}, aggregate_sort_share=share,
                  max_elements=dict(maxima), calls=dict(counts), kernel_experiment_earned=advance,
                  zero_sort_prefix_serial_bound=1/(1-share), rows=rows,
                  plan_sha256=sha(OUT/'plan.json'), auditor_sha256=sha(Path(__file__)),
                  referee_sha256=sha(ref.__file__),
                  scope='Forced prefix cost only; excludes search. No full-decision or strength bound. '
                        'Instrumented native paid thinning retained; populations can depend on wall time.')
    with (OUT/'audit.json').open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
