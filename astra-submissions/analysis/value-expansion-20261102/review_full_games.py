"""Describe every completed planned game, using the independent referee audit.

No bot execution, model update, gate modification, or selected-loss sampling.
An incomplete snapshot is labelled as such; later snapshots use new files.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'astra-submissions/tools')]
import audit_top6_tactics as tactical
import analyze_mist
import mine_top6_exploits


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--allow-partial', action='store_true'); args = ap.parse_args()
    directory = HERE / 'full-games'; plan = json.loads((directory / 'plan.json').read_text())
    for path, digest in plan['dependencies'].items(): assert sha(path) == digest, path
    refpath = ROOT / 'astra-submissions/experiments/value-expansion-20261102/build/referee.py'
    referee = tactical.load_referee(refpath)
    complete = [j for j in plan['jobs'] if (directory / 'jobs' / j['id'] / 'result.json').exists()]
    assert args.allow_partial or len(complete) == len(plan['jobs'])
    rows = []; faults = []; receipts = {}; full_frames = 0
    for job in complete:
        folder = directory / 'jobs' / job['id']; result = json.loads((folder / 'result.json').read_text())
        assert result['job'] == job
        receipts[job['id']] = sha(folder / 'result.json')
        if result['faults'] or result['exit'] != 0:
            faults.append(result); continue
        replay = json.loads((folder / 'replay.json').read_text())
        assert sha(folder / 'replay.json') == result['replay_sha256']
        frames = replay['frames']
        # Check every board and both views, not only the final decision.
        b = referee.FowBoard(); hist = Counter({referee.position_key(b): 1})
        for i, frame in enumerate(frames):
            if i:
                assert frame['move'] in {m.uci() for m in referee.fow_moves(b)}
                b.push_uci(frame['move']); hist[referee.position_key(b)] += 1
            calculated = referee.make_frame(b, frame['clocks'])
            assert all(calculated[k] == frame[k] for k in ('board', 'white', 'black'))
            full_frames += 1
        assert referee.outcome(b, hist) == (replay['result'], replay['reason'])
        for actor in ('candidate', 'base'):
            analysis = tactical.audit(replay, actor, referee)
            side = analysis['side']; si = int(side == 'black')
            moves = [f['move'] for f in frames[1:] if (f['ply'] - 1) % 2 == si]
            diagnostics = []
            pattern = r'^mist: n=(\d+) \|P\|=(\d+) samples=(\d+) moves=(\d+) .* p=([\d.]+) v=([-+\d.]+) lead=([-+\d]+) clock=([\d.]+).* move=(\w+)'
            for line in replay['privateDiagnostics'][side].splitlines():
                match = re.match(pattern, line)
                if match:
                    n, worlds, samples, allowed, prob, value, lead, clock, move = match.groups()
                    assert moves[int(n) - 1] == move
                    diagnostics.append(dict(decision=int(n), belief_worlds=int(worlds), searched_worlds=int(samples),
                        allowed_moves=int(allowed), chosen_strategy_probability=float(prob), search_value=float(value),
                        material_lead=int(lead), start_clock_rounded=float(clock), move=move))
            analysis.update(actor=actor, job=job['id'], pair=job['pair'], replay_sha256=result['replay_sha256'],
                engine_diagnostics=diagnostics, charged_clock_seconds=180 + 2 * len(moves) - frames[-1]['clocks'][si],
                value_pass_seconds=result['q_seconds'] if actor == 'candidate' else 0.)
            if analysis['terminal']:
                analysis['terminal']['engine_diagnostic'] = next((d for d in diagnostics if d['decision'] == len(moves)), None)
            rows.append(analysis)
    result = dict(at=datetime.now(timezone.utc).isoformat(), planned_games=len(plan['jobs']), completed_games=len(complete),
        full_frames_verified=full_frames, faults=faults, plan_sha256=sha(directory / 'plan.json'), result_sha256=receipts,
        sources={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), refpath, Path(tactical.__file__), Path(analyze_mist.__file__), Path(mine_top6_exploits.__file__)]},
        summaries={a: tactical.summary([r for r in rows if r['actor'] == a]) for a in ('candidate', 'base')},
        games=rows, scope='All completed first attempts, both actors, independent referee verification. Terminal safe moves are omniscient alternatives, not proof those moves survived the belief guard. Printed strategy probability is not king-loss risk. No truth-weight reconstruction, causal attribution, candidate update, or promotion change. Incomplete snapshots can be colour-imbalanced.')
    with args.output.open('x') as f: json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    compact = dict(completed=len(complete), frames=full_frames, faults=len(faults))
    for a in ('candidate', 'base'):
        s = result['summaries'][a]
        compact[a] = {k: s[k] for k in ('wdl', 'terminal', 'losses_down3_held4')}
    print(json.dumps(compact))


if __name__ == '__main__':
    main()
