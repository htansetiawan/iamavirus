"""Audit a terminal, fault-stopped batch; this path can never grant promotion."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import importlib.util
import json
import os
import sys

from run import OUT, ROOT, CANDIDATE, legacy, sha, write
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from local_turn_control import process_stat


def main():
    plan = legacy.module().load()
    closure = json.loads((OUT/'collector-closure.json').read_text())
    assert {r['session_id'] for r in closure['lanes']} == {68940, 65547}
    assert all(r['terminal'] and isinstance(r['exit_code'], int) for r in closure['lanes'])
    namespace = json.loads((OUT/'host-process-namespace.json').read_text())
    assert os.readlink('/proc/self/ns/pid') == namespace['observer_pid_namespace']
    assert any(r['matches'] for r in namespace['records'])
    spec = importlib.util.spec_from_file_location('stopped_gate_referee', CANDIDATE/'build/referee.py')
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    rows, missing, faults, live = [], [], [], []
    frames = identities = 0
    blocks = defaultdict(dict)
    for job in plan['jobs']:
        d = OUT/'jobs'/job['id']
        if not (d/'result.json').exists():
            assert not (d/'started.json').exists(), (job['id'], 'started attempt lacks a result')
            missing.append(job)
            continue
        result = json.loads((d/'result.json').read_text())
        start = json.loads((d/'started.json').read_text())
        handle = json.loads((d/'handle.json').read_text())
        assert start['job'] == job and start['plan_sha256'] == sha(OUT/'plan.json')
        assert handle['job'] == job['id'] and result['job'] == job and result['exit'] == 0
        assert result['replay_sha256'] == sha(d/'replay.json')
        assert all(result[k] == v for k,v in legacy.inspect(job,d).items())
        game = json.loads((d/'replay.json').read_text())
        board = ref.FowBoard(); history = Counter({ref.position_key(board):1})
        assert game['timeControl'] == {'baseSeconds':180, 'incrementSeconds':2}
        assert game['frames'][0]['clocks'] == [180,180] and not game.get('warnings')
        for ply, f in enumerate(game['frames']):
            if ply:
                assert ref.outcome(board,history) is None
                assert f['move'] in {m.uci() for m in ref.fow_moves(board)}
                board.push_uci(f['move']); history[ref.position_key(board)] += 1
            actual = ref.make_frame(board,f['clocks'])
            assert all(actual[k] == f[k] for k in ('board','white','black'))
            assert f['ply'] == ply and len(f['clocks']) == 2 and min(f['clocks']) >= 0
            if ply:
                previous = game['frames'][ply-1]['clocks']; mover = (ply-1)%2
                assert abs(f['clocks'][1-mover]-previous[1-mover]) < 1e-6
                assert f['clocks'][mover] <= previous[mover]+2+1e-6
            frames += 1
        if result['faults']:
            assert job['id'] == 'sf257-b7-white-candidate'
            assert result['faults'] == ['bot failure: black Time forfeit']
            assert game['failedSide'] == 'black' and game['reason'] == 'Time forfeit'
            assert ref.outcome(board,history) is None and not game['protocol']['truncated']
            report = game['studentReports'][0]
            event = game['protocol']['events'][-1]
            assert report['code'] == 'time_limit' and report['side'] == event['side'] == 'black'
            assert report['received'] is None and report['clockSeconds'] == 0
            assert event['direction'] == 'input' and event['ply'] == report['ply'] == 75
            elapsed = (report['atMs']-event['atMs'])/1000
            assert 0 <= elapsed-float(event['text']) < .1
            faults.append(dict(job=job, report=report, prompt=event, elapsed_to_report_seconds=elapsed))
        else:
            assert ref.outcome(board,history) == (game['result'],game['reason'])
            blocks[job['pair']][job['arm'],job['side']] = result['score']
        for side, control in enumerate(game['localTurnControl']['controls']):
            events = control['events']; freezes = [e for e in events if e['op']=='freeze']
            moves = sum(ply%2 == side for ply in range(len(game['frames'])-1))
            assert len(freezes) >= moves and sum(e['op']=='resume' for e in events) >= moves
            expected = 3 if side == ('white','black').index(job['side']) else 2
            assert all(e['members'] >= expected for e in freezes)
        for group in json.loads((d/'processes.json').read_text()):
            for identity in [group['leader'], *group['members']]:
                identities += 1; current = process_stat(identity['pid'])
                if current and current['state'] not in ('Z','X') and all(current[k] == identity[k] for k in ('pid','starttime','pgid','sid')):
                    live.append(current)
        rows.append(dict(job=job, score=result['score'], faults=result['faults'], plies=result['plies'],
                         final_clocks=result['final_clocks'], artifacts={p.name:sha(p) for p in d.iterdir() if p.is_file()}))
    assert len(rows)+len(missing)==32 and len(faults)==1 and not live
    stats = {}
    for arm in ('base','candidate'):
        a = [r for r in rows if r['job']['arm']==arm]
        clean = [r for r in a if not r['faults']]
        absent = sum(j['arm']==arm for j in missing)
        points = sum(r['score'] for r in clean)
        stats[arm] = dict(attempts=len(a), clean_games=len(clean), technical_games=len(a)-len(clean),
            unstarted=absent, clean_wins=sum(r['score']==1 for r in clean),
            clean_draws=sum(r['score']==.5 for r in clean), clean_losses=sum(r['score']==0 for r in clean),
            clean_points=points, recorded_points_including_technical=sum(r['score'] for r in a),
            points_bounds_with_technical_and_unstarted_unknown=[points,points+len(a)-len(clean)+absent])
    differences = {str(k):sum(b['candidate',side]-b['base',side] for side in ('white','black'))
                   for k,b in sorted(blocks.items()) if len(b)==4}
    report = dict(at=datetime.now(timezone.utc).isoformat(), completed=len(rows), unstarted=missing,
        gate_pass=False, decision='technical_failure_no_promotion', faults=faults, arms=stats,
        fully_observed_clean_block_point_differences=differences, referee_frames=frames,
        process_identities_checked=identities, live_owned_processes=live, rows=rows,
        plan_sha256=sha(OUT/'plan.json'), script_sha256=sha(__file__),
        collector_closure_sha256=sha(OUT/'collector-closure.json'),
        limitations=['Preserves the stopped first-attempt batch, including the opponent forfeit and every unstarted job.',
                    'Clean-only counts and observed-block differences are descriptive; missing games are outcome-dependent.',
                    'Completion bounds are worst/best possible points, not confidence intervals or replacement results.',
                    'No gate threshold is changed; this audit cannot grant publication.'])
    write(OUT/'stopped-review.json',report)
    md = ['# Matched Misty gate: technical failure', '',
          '**No promotion.** The zero-technical-fault and 32-completed-game requirements are unmet.', '',
          f"{len(rows)} first attempts ended; {len(missing)} games were never started. No attempt was replaced.", '',
          '| arm | clean W–D–L | clean points | technical games | unstarted |', '|---|---|---:|---:|---:|']
    for arm,s in stats.items():
        md.append(f"| {arm} | {s['clean_wins']}–{s['clean_draws']}–{s['clean_losses']} | {s['clean_points']} | {s['technical_games']} | {s['unstarted']} |")
    md += ['', 'The candidate also received a recorded win when Misty timed out as Black at ply 75. '
           'That attempt is retained in the raw scoreboard and reported separately; it is not a clean strength win.', '',
           f'Independent referee checks verify {frames} frames, move legality, observations, clocks and outcomes. '
           'The timeout transcript matches its deadline; the internal cause in Misty is unobserved. '
           f'{identities} recorded process identities were checked in the verified host namespace; none remains live.', '',
           f'Fully observed clean block differences (candidate minus v37): {differences}. '
           'These and clean-only counts describe an incomplete, fault-stopped panel; no confidence interval or Elo claim is made.', '',
           'The complete row ledger, unstarted IDs, hashes and non-probabilistic completion bounds are in stopped-review.json. '
           'The separate 16-game v37 pilot remains valid but does not erase this failed admission gate.']
    (OUT/'README.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','faults','unstarted')}),flush=True)


if __name__ == '__main__':
    main()
