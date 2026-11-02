"""Separate referee, source-body and arithmetic audit of the cost experiment."""
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import re
import statistics
from run import HERE,ROOT,OUT,OLD,sha,write,parse,check_profile


def body(source,name):
    m=re.search(r'(?m)^(?:static )?(?:int|void) '+name+r'\([^;]*?\) \{',source)
    assert m,name
    first=m.end()-1;depth=1;i=first+1
    while depth:
        if source[i]=='{':depth+=1
        if source[i]=='}':depth-=1
        i+=1
    return source[first:i]


def main():
    plan=json.loads((OUT/'plan.json').read_text());receipt=json.loads((OUT/'receipt.json').read_text())
    assert receipt['state']=='completed' and len(receipt['jobs'])==32
    assert receipt['plan_sha256']==sha(OUT/'plan.json')
    for p,h in plan['pins'].items():assert sha(ROOT/p)==h,p
    original=HERE.parent/'sparse-cfr-20261102/build';function_count=0
    for arm in ('base','fast'):
        for file,names in {'cfr.c':['pcfr_iteration','pcfr_current','game_grow'],
                           'gtcfr.c':['build_children_scored','pick_once','gtcfr_decide'],
                           'sfeval.c':['sf_children','sf_submit','sf_collect','sf_poll']}.items():
            a=(original/arm/'src'/file).read_text();b=(HERE/'build'/arm/'src'/file).read_text()
            for name in names:
                assert body(a,name)==body(b,name+'_profile_impl'),(arm,file,name)
                function_count+=1
    path=ROOT.parent/'fow-starter/referee.py'
    spec=importlib.util.spec_from_file_location('cost_referee',path);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    rows=[];frames=0;inputs=0
    for c in plan['cases']:
        rp=ROOT/'data/raw/games'/c['game']/'replay.json';assert sha(rp)==c['replay_sha256']
        replay=json.loads(rp.read_text());board=ref.FowBoard()
        key=('white','black')[c['side']];tc=replay.get('timeControl',{})
        expected=['fow',f"{'w' if c['side']==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"];forced=[]
        for ply,f in enumerate(replay['frames'][:c['ply']+1]):
            if ply:board.push_uci(f['move'])
            actual=ref.make_frame(board,f['clocks'])
            assert all(actual[k]==f[k] for k in ('board','white','black'));frames+=1
            expected.append(f[key])
            if ply%2==c['side']:
                expected.append(str(f['clocks'][c['side']]))
                if ply<c['ply']:forced.append(replay['frames'][ply+1]['move'])
        assert forced==c['forced']
        # Legacy 227 feed uses canonical integer formatting for whole-second
        # clocks. Compare parsed numeric values, retaining exact observation lines.
        actual_lines=(OLD/(c['name']+'.input.txt')).read_text().splitlines()
        assert len(actual_lines)==len(expected)
        for a,b in zip(actual_lines,expected):
            if a!=b:assert float(a)==float(b),(a,b)
        inputs+=1;legal={m.uci() for m in ref.fow_moves(board)}
        for arm in plan['arm_order']:
            result=json.loads((OUT/(c['name']+'-'+arm+'.json')).read_text())
            assert result['exit_code']==0 and result['error'] is None
            moves=[s[5:] for s in result['stdout'].splitlines() if s.startswith('move ')]
            assert moves[:-1]==forced and moves[-1] in legal
            final=next(s for s in result['stderr'].splitlines() if s.startswith('mist: n='))
            nodes=int(re.search(r'nodes=(\d+)',final)[1]);iterations=int(re.search(r'iters=(\d+)',final)[1])
            belief=int(re.search(r'\|P\|=(\d+)',final)[1])
            prof=parse(result['stderr'])
            if arm.endswith('-profile'):
                assert len(prof)==1;check_profile(prof[0]);assert prof[0]['nodes']==nodes and prof[0]['iterations']==iterations
            else:assert not prof
            rows.append(dict(case=c['name'],arm=arm,nodes=nodes,iterations=iterations,belief_count=belief,profile=prof[0] if prof else None))
    totals={};overhead={}
    for arm in ('base','fast'):
        measured=[r['profile'] for r in rows if r['arm']==arm+'-profile']
        wall=sum(p['wall'] for p in measured);cpu=sum(p['cpu'] for p in measured)
        categories={k:{'wall':sum(p['buckets'][k]['wall'] for p in measured),
                       'cpu':sum(p['buckets'][k]['cpu'] for p in measured),
                       'calls':sum(p['buckets'][k]['calls'] for p in measured)} for k in measured[0]['buckets']}
        for v in categories.values():v['wall_share']=v['wall']/wall
        totals[arm]=dict(wall=wall,cpu=cpu,buckets=categories)
        ratios=[];belief_changes=0
        for c in plan['cases']:
            a=next(r for r in rows if r['case']==c['name'] and r['arm']==arm)
            b=next(r for r in rows if r['case']==c['name'] and r['arm']==arm+'-profile')
            ratios.append(b['nodes']/a['nodes']);belief_changes+=a['belief_count']!=b['belief_count']
        overhead[arm]=dict(median_profiled_node_ratio=statistics.median(ratios),ratios=ratios,changed_belief_counts=belief_changes)
    review=dict(rows=rows,totals=totals,instrumentation_sensitivity=overhead,
                preserved_original_function_bodies=function_count,referee_frames=frames,
                legal_choices=32,actor_inputs=inputs,plan_sha256=sha(OUT/'plan.json'),
                receipt_sha256=sha(OUT/'receipt.json'),referee_sha256=sha(path),
                scope='Exclusive wall and main-thread CPU only; worker CPU is not measured. '
                      'Independent-process controls include search randomness and adaptive thinning, not pure timer overhead.')
    write(OUT/'review.json',review)
    print(json.dumps({k:v for k,v in review.items() if k not in ('rows','instrumentation_sensitivity')}))


if __name__=='__main__':main()
