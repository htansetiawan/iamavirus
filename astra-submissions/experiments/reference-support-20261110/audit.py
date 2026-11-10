"""Check policy rows, source-private inputs and every emitted native alias."""
from collections import Counter
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import re
import time
from prepare import ROOT,OUT,ANCESTRY,feed,sha,write

spec=importlib.util.spec_from_file_location('native_helpers',ANCESTRY/'audit.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
ref=native.ref

def main():
    before=time.monotonic();plan=json.loads((OUT/'plan.json').read_text());done=json.loads((OUT/'completion.json').read_text())
    assert done['status']=='complete' and done['attempted']==len(plan['cases'])==32
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    totals=Counter();supported_games=Counter();results=[];reference_records=[]
    for case,result in zip(plan['cases'],done['results']):
        assert case['context']==result['context'] and result['exit_code']==0 and not result['timed_out']
        folder=Path(result['folder']);text,moves=feed(case)
        assert (folder/'input.txt').read_text()==text and sha(folder/'input.txt')==result['input_sha256']
        for name in ('stdout','stderr'):assert sha(folder/f'{name}.txt')==result[f'{name}_sha256']
        stdout=(folder/'stdout.txt').read_text();stderr=(folder/'stderr.txt').read_text()
        assert re.findall(r'^move (\S+)$',stdout,re.M)==moves
        rows=[json.loads(s) for s in re.findall(r'^astra-reference: (.*)$',stderr,re.M)]
        policies=[r for r in rows if r['kind']=='policy'];assert len(policies)==1
        policy=policies[0];prior={r['move']:r['reference'] for r in policy['rows']};legal=set(policy['legal'])
        assert len(prior)==len(policy['rows']) and all(0<=v<=1 for v in prior.values()) and abs(sum(prior.values())-1)<1e-9
        argmax=next(r['move'] for r in policy['rows'] if r['pure_search_play'])
        assert sum(r['pure_search_play'] for r in policy['rows'])==1 and prior[argmax]==max(prior.values())
        cov=next(r for r in rows if r['kind']=='coverage');contexts=[r for r in rows if r['kind']=='context'];assert len(contexts)==cov['valid']
        replay=json.loads(Path(case['replay_path']).read_text());h=native.own_histories(replay,case)
        assert int(policy['own_history'],16)==h[-3]
        us=case['side']=='white';them=not us;counts=Counter();masses=[]
        for row in contexts:
            assert int(row['own_before'],16)==h[-3] and int(row['own_now'],16)==h[-1]
            assert row['own']==replay['frames'][case['ply']-1]['move']
            p=native.board(row['ancestor']);assert ref.observation(p,us)==replay['frames'][case['ply']-2][case['side']]
            native.push(p,row['own']);op1=ref.observation(p,them)
            ph=native.hm(int(row['opponent_before'],16),native.vh(op1))
            assert ref.observation(p,us)==replay['frames'][case['ply']-1][case['side']]
            native.push(p,row['hypothesized_reply']);assert native.position(p)==row['current']
            assert ref.observation(p,us)==replay['frames'][case['ply']][case['side']]
            op2=ref.observation(p,them);ph=native.hm(native.hm(ph,native.encoded(row['hypothesized_reply'])),native.vh(op2))
            assert ph==int(row['opponent_now'],16)
            assert row['actual_reference']==prior.get(row['own'],0)
            assert row['actual_guarded']==int(row['own'] not in prior and row['own'] in legal)
            assert row['actual_outside']==int(row['own'] not in prior and row['own'] not in legal)
            mass=positive=guarded=outside=0
            assert len({a['move'] for a in row['alternatives']})==len(row['alternatives'])==row['count']
            for alt in row['alternatives']:
                q=native.board(row['ancestor']);assert alt['move']!=row['own']
                native.push(q,alt['move']);assert ref.observation(q,them)==op1
                qh=native.hm(native.hm(h[-3],native.encoded(alt['move'])),native.vh(ref.observation(q,us)))
                native.push(q,row['hypothesized_reply']);assert native.position(q)==alt['current'] and ref.observation(q,them)==op2
                qh=native.hm(qh,native.vh(ref.observation(q,us)));assert qh==int(alt['own_history'],16) and qh!=h[-1]
                assert int(alt['opponent_history'],16)==ph
                assert alt['reference']==prior.get(alt['move'],0)
                assert alt['guarded']==int(alt['move'] not in prior and alt['move'] in legal)
                assert alt['outside']==int(alt['move'] not in prior and alt['move'] not in legal)
                mass+=alt['reference'];positive+=alt['reference']>1e-6;guarded+=alt['guarded'];outside+=alt['outside']
            assert abs(mass-row['mass'])<1e-12 and positive==row['positive'] and guarded==row['guarded'] and outside==row['outside']
            c=plan['criteria'];onpolicy=row['own']==argmax
            supported=onpolicy and row['actual_reference']>c['min_actual_reference'] and mass>=c['min_alternative_mass']
            counts['contexts']+=1;counts['aliases']+=row['count'];counts['positive_aliases']+=positive;counts['guarded_aliases']+=guarded
            counts['outside_aliases']+=outside;counts['historical_argmax_matches']+=onpolicy;counts['supported']+=supported
            counts['zero_actual_reference']+=row['actual_reference']<=c['min_actual_reference'];masses.append(mass)
            if supported:supported_games[case['game']]+=1
        totals.update(counts);results.append(dict(context=case['context'],game=case['game'],ply=case['ply'],counts=dict(counts),
               raw_reference_support=sum(v>1e-6 for v in prior.values()),historical_previous=replay['frames'][case['ply']-1]['move'],
               searched_argmax=argmax,max_alias_reference_mass=max(masses,default=0),coverage=cov))
        reference_records.append(dict(game=case['game'],ply=case['ply'],rows=rows))
    fraction=totals['supported']/max(1,totals['contexts'])
    passed=fraction>=plan['criteria']['min_supported_context_fraction'] and len(supported_games)>=plan['criteria']['min_supported_games']
    write(OUT/'audit.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,necessary_support_gate=passed,counts=dict(totals),
          supported_fraction=fraction,supported_games=dict(supported_games),cases=results,seconds=time.monotonic()-before,
          scope='Necessary raw-search-reference support only, on reused development prefixes with forced historical actions. '
                'Argmax matches are a subset, not an on-policy game. Pure execution supplies zero mass to past-own alternatives on that subset. '
                'No opponent reference reaches, valid gadget probabilities, certified full draw histories or playing-strength estimate.'))
    write(OUT/'reference-records.json',reference_records)
    print(json.dumps(dict(necessary_support_gate=passed,counts=dict(totals),supported_fraction=fraction,supported_games=len(supported_games))),flush=True)
if __name__=='__main__':main()
