"""Independent post-run rule/transcript/clock audit and paired description."""
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from learning import ingest


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    assert summary['complete'] and summary['attempted']==12
    for path,h in plan['deps'].items():assert sha(path)==h,path
    receipts={r['job']['id']:r for r in summary['rows']}
    bycase=defaultdict(dict);byarm=defaultdict(list);frames_checked=views_checked=clocks_checked=0
    for job in plan['jobs']:
        d=OUT/job['id'];r=receipts[job['id']];assert r==json.loads((d/'result.json').read_text())
        assert r['passed'] and r['exit']==0 and not r['timeout'] and not r['unverified_groups']
        assert sha(d/'replay.json')==r['replay_sha256']
        game=json.loads((d/'replay.json').read_text());case=plan['cases'][job['case']]
        p=json.loads((ROOT/case['prefix']).read_text());frames=game['frames'];steps=game['continuation']['steps']
        states,errors=ingest.validate_replay(game);assert not errors;frames_checked+=len(states)
        branch=case['branch_ply'];assert len(steps)==len(frames)-1
        assert all(f[k]==p['frames'][i][k] for i,f in enumerate(frames[:branch+1]) for k in ('move','board','white','black','clocks'))
        for i,(s,pre,post) in enumerate(zip(steps,frames,frames[1:])):
            side=i%2
            assert s['ply']==i and s['side']==side and s['move']==post['move']
            assert abs(s['reported_clock']-pre['clocks'][side])<2e-6
            assert abs(post['clocks'][1-side]-pre['clocks'][1-side])<2e-6
            if i>=branch:assert abs(post['clocks'][side]-pre['clocks'][side]+s['actual_elapsed']-game['timeControl']['incrementSeconds'])<2e-6
        for side,key in enumerate(('white','black')):
            inp=[e for e in game['protocol']['events'] if e['side']==key and e['direction']=='input']
            views=[e for e in inp if len(e['text'])==64]
            last=max(s['ply'] for s in steps if s['side']==side)
            assert [e['ply'] for e in views]==list(range(last+1))
            for e in views:assert e['text']==frames[e['ply']][key]
            clocks=[e for e in inp if len(e['text'])!=64 and e['text']!='fow' and not e['text'].startswith(('w ','b '))]
            assert [e['ply'] for e in clocks]==list(range(side,last+1,2))
            for e in clocks:assert abs(float(e['text'])-frames[e['ply']]['clocks'][side])<2e-6
            views_checked+=len(views);clocks_checked+=len(clocks)
        assert not game['protocol']['truncated'] and not game.get('failedSide') and not game.get('warnings')
        if game['censored']:assert game['result']=='*' and states[-1].outcome() is None
        else:assert states[-1].outcome()==(game['result'],game['reason'])
        bycase[case['id']][job['arm']]=r;byarm[job['arm']].append(r)
    case_rows=[]
    for case in plan['cases']:
        arms=bycase[case['id']]
        oldpath=ROOT/'data/raw/games'/case['game']/'replay.json'
        assert sha(oldpath)==case['source_replay_sha256']
        historical=json.loads(oldpath.read_text())['result']
        comparisons={}
        for a,b in [('cheap','normal'),('normal','normal_repeat')]:
            aa,bb=arms[a],arms[b]
            comparisons[f'{a}_vs_{b}']=dict(first_move_agrees=aa['first_move']==bb['first_move'],
                both_natural=not aa['censored'] and not bb['censored'],
                same_outcome=None if aa['censored'] or bb['censored'] else aa['natural_result']==bb['natural_result'])
        case_rows.append(dict(case=case['id'],source=case['game'],branch_ply=case['branch_ply'],kind=case['kind'],
            historical_result=historical,comparisons=comparisons,arms={arm:{k:r[k] for k in ('first_move','natural_result','censored','new_plies','wall_seconds','warmup_seconds','continuation_seconds')} for arm,r in arms.items()}))
    costs={}
    for arm,rows in byarm.items():
        elapsed=sum(r['wall_seconds'] for r in rows);n=sum(not r['censored'] for r in rows);new=sum(r['new_plies'] for r in rows)
        costs[arm]=dict(jobs=len(rows),natural_terminals=n,censored=len(rows)-n,wall_seconds_sum=elapsed,
            new_decisions=new,seconds_per_new_decision=elapsed/new,
            seconds_per_natural_terminal_including_censored_cost=elapsed/n if n else None,
            warmup_seconds_sum=sum(r['warmup_seconds'] for r in rows))
    result=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,frames_checked=frames_checked,
        delivered_observations_checked=views_checked,clock_prompts_checked=clocks_checked,
        cases=case_rows,costs=costs,summary_sha256=sha(OUT/'summary.json'),source_sha256=sha(__file__),
        scope='Four development prefixes; two selected after prior prediction failures. All planned replicates retained. Censoring is not a draw. Outcome/first-move agreement describes these cases only, not cheap-label equivalence or playing strength.')
    with (OUT/'review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    text=['# Budget sensitivity: independently verified results','','| Prefix | Arm | First move | Outcome | New plies | Wall seconds |','|---|---|---|---|---:|---:|']
    for case in case_rows:
        for arm in ('cheap','normal','normal_repeat'):
            r=case['arms'][arm];outcome='censored' if r['censored'] else r['natural_result']
            text.append(f"| {case['source']}:{case['branch_ply']} | {arm} | {r['first_move']} | {outcome} | {r['new_plies']} | {r['wall_seconds']:.2f} |")
    text+=['','## Costs','','| Arm | Natural terminals | Censored | Seconds per new decision | Seconds per natural terminal including censored work |','|---|---:|---:|---:|---:|']
    for arm in ('cheap','normal','normal_repeat'):
        r=costs[arm];v=r['seconds_per_natural_terminal_including_censored_cost']
        text.append(f"| {arm} | {r['natural_terminals']} | {r['censored']} | {r['seconds_per_new_decision']:.2f} | {v:.2f} |" if v is not None else f"| {arm} | 0 | {r['censored']} | {r['seconds_per_new_decision']:.2f} | undefined |")
    text+=['',f'Independent audit: {frames_checked} frames, {views_checked} delivered observations, {clocks_checked} clock prompts, all transitions and terminal/censor decisions.','',result['scope']]
    (OUT/'results.md').write_text('\n'.join(text)+'\n')
    print(json.dumps({'passed':True,'frames':frames_checked,'costs':costs,'comparisons':[{'case':c['case'],**c['comparisons']} for c in case_rows]}),flush=True)


if __name__=='__main__':main()
