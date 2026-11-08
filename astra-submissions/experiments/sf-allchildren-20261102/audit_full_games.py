"""Close the original full-game pilot from immutable receipts and referee play."""
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import sys

from full_games import OUT, HERE, ROOT, legacy
from build import sha, write
from run import now
sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from local_turn_control import process_stat

def main():
    plan=legacy.module().load()
    assert len(plan['jobs'])==16 and len({j['id'] for j in plan['jobs']})==16
    assert {p.name for p in (OUT/'jobs').iterdir()}=={j['id'] for j in plan['jobs']}
    spec=importlib.util.spec_from_file_location('sf256_full_referee',HERE/'build/referee.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    rows=[];frames=0;known=0;live=[];pairs=defaultdict(list);colors=defaultdict(list)
    for job in plan['jobs']:
        directory=OUT/'jobs'/job['id'];result=json.loads((directory/'result.json').read_text())
        start=json.loads((directory/'started.json').read_text());handle=json.loads((directory/'handle.json').read_text())
        assert start['job']==job and start['plan_sha256']==sha(OUT/'plan.json')
        assert handle['job']==job['id'] and result['job']==job
        assert result['exit']==0 and not result['faults']
        assert sha(directory/'replay.json')==result['replay_sha256']
        checked=legacy.inspect(job,directory)
        assert all(result[k]==v for k,v in checked.items())
        replay=json.loads((directory/'replay.json').read_text());board=ref.FowBoard()
        history=Counter({ref.position_key(board):1})
        assert replay['timeControl']=={'baseSeconds':180,'incrementSeconds':2}
        for ply,f in enumerate(replay['frames']):
            if ply:
                assert ref.outcome(board,history) is None,(job['id'],ply,'continued after terminal')
                assert f['move'] in {m.uci() for m in ref.fow_moves(board)}
                board.push_uci(f['move']);history[ref.position_key(board)]+=1
            actual=ref.make_frame(board,f['clocks'])
            assert all(actual[k]==f[k] for k in ('board','white','black'))
            assert f['ply']==ply and len(f['clocks'])==2 and min(f['clocks'])>=0
            if ply:
                before=replay['frames'][ply-1]['clocks'];mover=(ply-1)%2
                assert abs(f['clocks'][1-mover]-before[1-mover])<1e-6
                assert f['clocks'][mover]<=before[mover]+2+1e-6
            frames+=1
        assert ref.outcome(board,history)==(replay['result'],replay['reason'])
        # The native process and both Stockfish children must have been stopped
        # together during the opponent's turn; the recorded event count is also
        # checked against the actual number of moves.
        for side,control in enumerate(replay['localTurnControl']['controls']):
            events=control['events'];freezes=[e for e in events if e['op']=='freeze'];resumes=[e for e in events if e['op']=='resume']
            moves=sum(1 for ply in range(len(replay['frames'])-1) if ply%2==side)
            assert len(freezes)>=moves and len(resumes)>=moves
            assert all(e['members']>=3 for e in freezes)
        for group in json.loads((directory/'processes.json').read_text()):
            for identity in [group['leader'],*group['members']]:
                known+=1;current=process_stat(identity['pid'])
                if current and current['state'] not in ('Z','X') and all(current[k]==identity[k] for k in ('pid','starttime','pgid','sid')):live.append(current)
        pairs[job['pair']].append(result['score']);colors[job['side']].append(result['score'])
        rows.append(dict(job=job,result=replay['result'],score=result['score'],plies=result['plies'],
                         final_clocks=result['final_clocks'],elapsed_seconds=result['elapsed_seconds'],finished=result['finished'],
                         artifacts={p.name:sha(p) for p in directory.iterdir() if p.is_file()}))
    assert not live,live
    assert len(pairs)==8 and all(len(v)==2 for v in pairs.values())
    points=sum(r['score'] for r in rows);scores=[r['score'] for r in rows]
    # Exact bootstrap distribution over eight observed color pairs. This is
    # descriptive small-sample uncertainty, not a validated arena Elo interval.
    pair_units=[int(round(2*sum(pairs[k]))) for k in sorted(pairs)]
    freq=Counter(pair_units);dist={0:1.0}
    for _ in pair_units:
        nxt=defaultdict(float)
        for total,p in dist.items():
            for value,n in freq.items():nxt[total+value]+=p*n/len(pair_units)
        dist=nxt
    def quantile(q):
        cumulative=0
        for total,p in sorted(dist.items()):
            cumulative+=p
            if cumulative>=q:return total/32
    result=dict(audited_at=now(),completed=16,wins=scores.count(1),draws=scores.count(.5),losses=scores.count(0),
                points=points,score=points/16,gate_pass=points>=10,referee_frames=frames,
                pair_points={str(k):sum(v) for k,v in pairs.items()},
                by_color={k:dict(wins=v.count(1),draws=v.count(.5),losses=v.count(0)) for k,v in colors.items()},
                descriptive_pair_bootstrap_95=[quantile(.025),quantile(.975)],
                positive_pairs=sum(sum(v)>1 for v in pairs.values()),tied_pairs=sum(sum(v)==1 for v in pairs.values()),
                known_process_identities_checked=known,live_owned_processes=live,original_sessions_now_missing=[13598,26030],
                plan_sha256=sha(OUT/'plan.json'),referee_sha256=sha(HERE/'build/referee.py'),rows=rows,
                scope='Original 16 first-attempt local games. Original tool sessions no longer exist; all complete game receipts independently audited. No reruns or claim of arena superiority.')
    write(OUT/'independent-review.json',result)
    (OUT/'README.md').write_text(f'''# All-child scorer pilot: 11 wins, 1 draw, 4 losses

The candidate scores **{points}/16 (71.875%)** against unchanged v37 at 180+2,
passing the predeclared 10-point pilot gate. White: 6W–0D–2L; Black: 5W–1D–2L.
The eight color-pair scores are 1, 1, 1, 1.5, 2, 2, 1, 2 out of two.

All games finished on 2 November, last at 17:42:05 UTC, within the four-hour
cap. This audit was performed on {result['audited_at']}. The original exec
sessions 13598/26030 no longer exist. Sixteen original started/worker/result
receipts and replay hashes match the frozen plan; no game was restarted.

Independent course-referee reconstruction checks {frames} frames, every move,
both observations, terminal results, and clock changes. Both sides' native bot
and Stockfish children were covered by turn isolation. No recorded technical
fault, warning, illegal move or time forfeit. No recorded process identity
remains live. All frozen binary/source/launcher dependencies still match.

Both arms use identical v37 native bytes and history data. Only the candidate's
Stockfish scorer and opt-in flag differ. It is the same approximation that
passed played-parent, search-frontier and equal-clock native decision checks.

This is a small pilot against one reference. Four seed pairs favor the candidate
and four tie; no pair favors v37. The descriptive pair-bootstrap 95% score range
is {quantile(.025):.1%}–{quantile(.975):.1%}, conditional on these eight observed
pairs. It cannot establish a broad strength gain or arena Elo. The predeclared
next step is a separate matched opponent comparison, with v37 as control.

No new arena ZIP, version reservation or deployment follows from this result.
The earlier executable-permission smoke failure and initial plan are retained;
they occurred before any full game and did not change either playing binary.
''')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows',)}),flush=True)

if __name__=='__main__':main()
