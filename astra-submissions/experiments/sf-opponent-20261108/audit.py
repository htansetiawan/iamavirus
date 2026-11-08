"""Independent completed-batch audit; never modifies or restarts a game."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import importlib.util
import json
import sys

from run import OUT, ROOT, CANDIDATE, legacy, sha, write
sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
from local_turn_control import process_stat

def main():
    plan = legacy.module().load()
    assert len(plan['jobs']) == 32 and len({j['id'] for j in plan['jobs']}) == 32
    assert {p.name for p in (OUT / 'jobs').iterdir()} == {j['id'] for j in plan['jobs']}
    spec = importlib.util.spec_from_file_location('sf257_independent_referee', CANDIDATE / 'build/referee.py')
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    rows = []
    frames = identities = 0
    live = []
    pairs = defaultdict(dict)
    for job in plan['jobs']:
        d = OUT / 'jobs' / job['id']
        result = json.loads((d / 'result.json').read_text())
        start = json.loads((d / 'started.json').read_text())
        handle = json.loads((d / 'handle.json').read_text())
        assert start['job'] == job and start['plan_sha256'] == sha(OUT / 'plan.json')
        assert handle['job'] == job['id'] and result['job'] == job
        assert result['exit'] == 0 and not result['faults']
        assert result['replay_sha256'] == sha(d / 'replay.json')
        assert all(result[k] == v for k, v in legacy.inspect(job, d).items())
        game = json.loads((d / 'replay.json').read_text())
        board = ref.FowBoard()
        history = Counter({ref.position_key(board): 1})
        assert game['timeControl'] == {'baseSeconds': 180, 'incrementSeconds': 2}
        assert game['frames'][0]['clocks'] == [180, 180]
        for ply, f in enumerate(game['frames']):
            if ply:
                assert ref.outcome(board, history) is None, (job['id'], ply, 'post-terminal move')
                assert f['move'] in {m.uci() for m in ref.fow_moves(board)}
                board.push_uci(f['move'])
                history[ref.position_key(board)] += 1
            actual = ref.make_frame(board, f['clocks'])
            assert all(actual[k] == f[k] for k in ('board', 'white', 'black'))
            assert f['ply'] == ply and len(f['clocks']) == 2 and min(f['clocks']) >= 0
            if ply:
                before = game['frames'][ply - 1]['clocks']
                mover = (ply - 1) % 2
                assert abs(f['clocks'][1 - mover] - before[1 - mover]) < 1e-6
                assert f['clocks'][mover] <= before[mover] + 2 + 1e-6
            frames += 1
        assert ref.outcome(board, history) == (game['result'], game['reason'])
        for side, control in enumerate(game['localTurnControl']['controls']):
            events = control['events']
            freezes = [e for e in events if e['op'] == 'freeze']
            resumes = [e for e in events if e['op'] == 'resume']
            moves = sum(ply % 2 == side for ply in range(len(game['frames']) - 1))
            assert len(freezes) >= moves and len(resumes) >= moves
            # Native+two SF workers; Misty adapter+one SF process.
            expected_members = 3 if side == ('white', 'black').index(job['side']) else 2
            assert all(e['members'] >= expected_members for e in freezes)
        for group in json.loads((d / 'processes.json').read_text()):
            for identity in [group['leader'], *group['members']]:
                identities += 1
                current = process_stat(identity['pid'])
                if current and current['state'] not in ('Z', 'X') and all(current[k] == identity[k] for k in ('pid', 'starttime', 'pgid', 'sid')):
                    live.append(current)
        key = (job['arm'], job['side'])
        assert key not in pairs[job['pair']]
        pairs[job['pair']][key] = result['score']
        rows.append(dict(job=job, score=result['score'], plies=result['plies'], final_clocks=result['final_clocks'],
                         artifacts={p.name: sha(p) for p in d.iterdir() if p.is_file()}))
    assert not live
    assert len(pairs) == 8 and all(len(p) == 4 for p in pairs.values())
    stats = {}
    for arm in ('base', 'candidate'):
        scores = [r['score'] for r in rows if r['job']['arm'] == arm]
        assert len(scores) == 16
        stats[arm] = dict(wins=scores.count(1), draws=scores.count(.5), losses=scores.count(0), points=sum(scores))
    differences = [sum(p['candidate', side] - p['base', side] for side in ('white', 'black')) for _, p in sorted(pairs.items())]
    # Exact bootstrap across the eight matched seed/color blocks. Descriptive,
    # conditional uncertainty; not an arena-Elo or sequential-test claim.
    freq = Counter(int(2 * x) for x in differences)
    distribution = {0: 1.}
    for _ in differences:
        nxt = defaultdict(float)
        for total, mass in distribution.items():
            for x, count in freq.items():
                nxt[total + x] += mass * count / 8
        distribution = nxt
    def quantile(q):
        cumulative = 0
        for total, mass in sorted(distribution.items()):
            cumulative += mass
            if cumulative >= q:
                return total / 32
    g = plan['gate']
    passed = stats['candidate']['points'] >= g['candidate_min_points'] and sum(differences) >= g['candidate_min_advantage_points']
    report = dict(at=datetime.now(timezone.utc).isoformat(), completed=32, arms=stats, gate_pass=passed,
                  matched_block_point_differences=differences, descriptive_paired_score_difference_95=[quantile(.025), quantile(.975)],
                  referee_frames=frames, process_identities_checked=identities, live_owned_processes=live,
                  plan_sha256=sha(OUT / 'plan.json'), rows=rows,
                  limitation='Local Misty 0.1.3, not verified current arena bytes; small development gate, not Elo.')
    write(OUT / 'independent-review.json', report)
    (OUT / 'README.md').write_text(
        '# Matched Misty gate\n\n'
        f"Frozen gate: **{'PASS' if passed else 'FAIL'}**. Candidate {stats['candidate']['points']}/16; v37 {stats['base']['points']}/16.\n\n"
        f"All 32 first attempts completed cleanly. Independent course-referee audit verifies {frames} frames, legal moves, both observations, terminal outcomes, clocks and process isolation. No recorded process identity remains live. All frozen source/binary/launcher pins match.\n\n"
        f"Candidate-minus-v37 points by matched two-color block: {differences}. Descriptive paired-bootstrap score difference range: {quantile(.025):.1%} to {quantile(.975):.1%}.\n\n"
        'The opponent is authentic local Misty 0.1.3, not verified current arena bytes. This is a small development gate with shared seeds and colors, not an Elo estimate. Portable-package and final ZIP checks are separate requirements.\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}), flush=True)

if __name__ == '__main__':
    main()
