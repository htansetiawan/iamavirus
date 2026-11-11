"""Read-only source, input, arithmetic and timing reduction for 423."""
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/recapture-guard-cost-20261111'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def main():
    plan=read(OUT/'plan.json');spec=read(OUT/'spec.json')
    assert sha(OUT/'spec.json')==plan['spec_sha256']
    assert sha(HERE/'study.py')==plan['runner_sha256']==spec['runner_sha256']
    for p,v in spec['pins'].items():assert sha(ROOT/p)==v,p
    for b in plan['binaries'].values():assert sha(ROOT/b['path'])==b['sha256']
    generated=HERE/'build/tree/src'
    for name,v in plan['generated_source_sha256'].items():assert sha(generated/name)==v
    profile=(generated/'profile-main.c').read_text()
    coherent=(ROOT/'astra-submissions/experiments/safe-recapture-integration-20261111/build/coherent/src/main.c').read_text()
    assert re.sub(r'#ifdef ASTRA_COUNT_GUARD\n[^\n]*\n#endif\n','',profile)==coherent
    build=read(OUT/'compilation.json');assert len(build)==2 and all(r['exit_code']==0 for r in build)
    assert '-DASTRA_COUNT_GUARD' not in build[0]['argv'] and '-DASTRA_COUNT_GUARD' in build[1]['argv']
    runs=[json.loads(l) for l in (OUT/'runs.jsonl').read_text().splitlines()]
    assert len(runs)==10 and read(OUT/'completion.json')['completed']
    assert len({(r['case'],r['mode']) for r in runs})==10
    reports=[];input_rows=0
    for c in plan['cases']:
        p=ROOT/c['input_path'];assert sha(p)==c['input_sha256']
        lines=p.read_text().splitlines();head=lines[0].split();n,cap,us,temp=int(head[0]),int(head[1]),int(head[2]),float(head[3]);view=head[4]
        assert len(lines)==n+1 and n==c['worlds'] and cap==20000 and len(view)==64
        if c['kind'] in ('saved','cycle-saved'):worlds=read(ROOT/c['source'])['worlds']
        else:
            assert c['kind']=='constructed-repeat';old=read(ROOT/c['source'])[0]
            worlds=[dict(board=old['board'],side=0,castle='0',ep=-1,halfmove=0,logw=0)]
        for i,line in enumerate(lines[1:]):
            fields=line.split();w=worlds[i%len(worlds)]
            assert fields[0]==w['board'] and len(fields[0])==64
            assert int(fields[1])==w['side']==us and int(fields[2],16)==int(w['castle'],16)
            assert int(fields[3])==w['ep'] and int(fields[4])==w['halfmove'] and float(fields[5])==w['logw']
        input_rows+=n
        rows={}
        for mode in ('time','trace'):
            r=next(r for r in runs if r['case']==c['name'] and r['mode']==mode)
            assert r['exit_code']==0 and not r['timed_out'] and not r['stderr']
            assert r['argv'][1]==mode and r['argv'][2]==str(p)
            rows[mode]=[json.loads(l) for l in r['stdout'].splitlines()]
        m=rows['time'][0];assert m['type']=='metadata' and m==rows['trace'][0]
        stride=max(1,(n+cap-1)//cap);evaluated=(n+stride-1)//stride
        assert m['stride']==stride and m['evaluated']==evaluated and m['worlds']==n
        assert m['repeats']==max(1,(65536+evaluated*m['moves']-1)//(evaluated*m['moves']))
        risks=[r for r in rows['time'] if r['type']=='risks'];timings=[r for r in rows['time'] if r['type']=='timing']
        assert len(risks)==m['moves'] and len(timings)==8 and len(rows['trace'])==2
        assert len({r['move'] for r in risks})==m['moves']
        expected=[]
        changed=0
        for r in risks:
            assert len(r['arms'])==2 and all(len(a)==6 for a in r['arms'])
            old,new=r['arms'];changed+=any(abs(a-b)>1e-12 for a,b in zip(old,new))
            for arm in (old,new):
                assert all(math.isfinite(v) and -1e-12<=v<=1+1e-12 for v in arm)
                assert all(arm[k]+arm[k+3]<=1+1e-12 for k in range(3))
            for k in range(3):
                assert new[k]>=old[k]-1e-12 and new[k+3]<=old[k+3]+1e-12
                assert new[k]+new[k+3]>=old[k]+old[k+3]-1e-12
        for arm in (0,1):expected.append(math.fsum((k+1)*r['arms'][arm][k] for r in risks for k in range(6)))
        ratios=[];walls=[];per_arm=[[],[]]
        for block in range(4):
            pair=[r for r in timings if r['block']==block]
            assert [r['arm'] for r in pair]==([0,1] if block%2==0 else [1,0])
            byarm={r['arm']:r for r in pair}
            for arm,r in byarm.items():
                assert r['cpu_ns']>=plan['minimum_cpu_ns'] and r['wall_ns']>0
                assert math.isclose(r['checksum']/m['repeats'],expected[arm],rel_tol=1e-9,abs_tol=1e-8)
                per_arm[arm].append(r['cpu_ns']/m['repeats']/1e6)
            ratios.append(byarm[1]['cpu_ns']/byarm[0]['cpu_ns']);walls.append(byarm[1]['wall_ns']/byarm[0]['wall_ns'])
        trace=rows['trace'][1];assert trace['type']=='trace'
        assert 0<=trace['attempts']<=trace['scanned_pieces'] and 0<=trace['calls']<=trace['scanned_pieces']
        assert math.isclose(trace['checksum'],expected[1],rel_tol=1e-9,abs_tol=1e-8)
        reports.append(dict(name=c['name'],kind=c['kind'],worlds=n,moves=m['moves'],repeats=m['repeats'],
            original_pass_cpu_ms=statistics.median(per_arm[0]),coherent_pass_cpu_ms=statistics.median(per_arm[1]),
            cpu_ratios=ratios,median_cpu_ratio=statistics.median(ratios),wall_ratios=walls,
            changed_action_vectors=changed,trace_counts={k:trace[k] for k in ('calls','scanned_pieces','attempts')},
            trace_calls_per_world_action=trace['calls']/(evaluated*m['moves'])))
    result=dict(review_passed=True,cases=reports,source_pins=len(spec['pins']),input_world_rows=input_rows,
                minimum_timer_precision_passed=True,normal_trace_checksum_parity=True,
                original_coherent_risk_invariants_passed=True,
                natural_cost_concerns=[r['name'] for r in reports if r['kind']=='saved' and r['median_cpu_ratio']>1.25],
                source_sha256=sha(Path(__file__)),runs_sha256=sha(OUT/'runs.jsonl'),
                policy_or_backend_processes=0,limits=plan['limits'])
    with (OUT/'review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'review_passed':True,'input_rows':input_rows,'natural_cost_concerns':result['natural_cost_concerns'],'cases':[{k:r[k] for k in ('name','median_cpu_ratio','original_pass_cpu_ms','coherent_pass_cpu_ms','changed_action_vectors','trace_counts')} for r in reports]}))


if __name__=='__main__':main()
