#!/usr/bin/env python3
"""Fixed-cap paired posterior gate with exact zero-correction control parity."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from m4_prior_fit import sha,bootstrap


def read_rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def notiming(row):return {k:v for k,v in row.items() if k!='update_cpu_seconds'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--experiment',type=Path,required=True)
    ap.add_argument('--build',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True)
    args=ap.parse_args();out=args.experiment/'sequential';out.mkdir(exist_ok=False)
    shutil.copytree(args.build,out/'build');shutil.copyfile(__file__,out/'run.py')
    m=json.loads((args.experiment/'model.json').read_text())
    base=out/'base26.txt';base.write_text('26\n'+' '.join(f'{x:.12g}' for x in m['base_theta'])+'\n')
    gate=out/'gate7.txt';gate.write_text('7\n'+' '.join(f'{x:.12g}' for x in m['gate_theta'])+'\n')
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4'))}
    env.update(MIST_MODEL='1',MIST_MODEL_TEMP='1',MIST_MODEL_FULL_BELOW='10000')
    metadata=[];control=[];candidate=[];primary=set();cohort_seconds={}
    for name in ['sequential02','sequential-fresh26']:
        source=args.previous/name;target=out/name;target.mkdir()
        old=json.loads((source/'manifest.json').read_text());assert old['cap']==10000 and old['seed']==41
        for file in ['input.txt','manifest.json','control26.jsonl']:
            shutil.copyfile(source/file,target/('original-'+file))
        metadata.append({'name':name,'source':str(source),'input_sha256':sha(source/'input.txt'),
                         'original_control_sha256':sha(source/'control26.jsonl')})
        primary.update(g['id'] for g in old['games'] if g['cohort']!='diagnostic')
        arms={};seconds={}
        for arm,active in [('control26',False),('intent',True)]:
            e=dict(env)
            if active:e['M4_INTENT_GATE']=str(gate)
            start=time.monotonic()
            with (target/(arm+'.jsonl')).open('w') as stdout,(target/(arm+'.stderr')).open('w') as stderr:
                p=subprocess.run([str(out/'build/runner'),str(target/'original-input.txt'),str(base),'10000','41'],
                                 env=e,stdout=stdout,stderr=stderr,timeout=900)
            status={'returncode':p.returncode,'seconds':time.monotonic()-start};seconds[arm]=status['seconds']
            (target/(arm+'-status.json')).write_text(json.dumps(status,indent=2)+'\n')
            if p.returncode:raise RuntimeError(name+' '+arm+' failed')
            arms[arm]=read_rows(target/(arm+'.jsonl'))
            if not active:
                original=read_rows(target/'original-control26.jsonl')
                if [notiming(r) for r in original]!=[notiming(r) for r in arms[arm]]:
                    raise RuntimeError('zero-gate baseline mismatch; do not interpret treatment')
            print(json.dumps({'cohort':name,'arm':arm,**status}),flush=True)
        if [(r['game'],r['ply']) for r in arms['control26']]!=[(r['game'],r['ply']) for r in arms['intent']]:
            raise ValueError('decision mismatch')
        for a,b in zip(arms['control26'],arms['intent']):
            assert not b['inconsistent'] and not b['cheap_calls']
            for k in ['move','actual_attack','actual_fatal','side']:assert a[k]==b[k]
        control.extend(arms['control26']);candidate.extend(arms['intent']);cohort_seconds[name]=seconds
    if len({(r['game'],r['ply']) for r in control})!=len(control):raise ValueError('duplicated cohort decisions')
    summary={}
    for label,indices in [('primary',[i for i,r in enumerate(control) if r['game'] in primary]),
                           ('all_with_diagnostic',list(range(len(control))))]:
        a=[control[i] for i in indices];b=[candidate[i] for i in indices];groups=np.array([r['game'] for r in a]);report={}
        for name,rows in [('control26',a),('intent',b)]:
            last={r['game']:r for r in rows}
            report[name]={'decisions':len(rows),'games':len(last),'truth_present':sum(r['truth_present'] for r in rows),
                          'collapses':sum(r['collapses'] for r in last.values()),
                          'update_cpu_seconds':sum(r['update_cpu_seconds'] for r in last.values())}
            for metric in ['attack','fatal']:
                pred=np.array([r[metric+'_probability'] for r in rows]);truth=np.array([r['actual_'+metric] for r in rows])
                report[name][metric]={'expected':float(pred.sum()),'actual':int(truth.sum()),'brier':float(np.mean((pred-truth)**2))}
        report['paired']={'truth_support_gain':bootstrap(np.array([y['truth_present']-x['truth_present'] for x,y in zip(a,b)]),groups)}
        for metric in ['attack','fatal']:
            delta=np.array([(x[metric+'_probability']-x['actual_'+metric])**2-(y[metric+'_probability']-y['actual_'+metric])**2 for x,y in zip(a,b)])
            report['paired'][metric+'_brier_reduction']=bootstrap(delta,groups)
        summary[label]=report
    result={'cohorts':summary,'timings':cohort_seconds,'inputs':metadata,'zero_gate_exact_nontiming_parity':True,
            'model_sha256':sha(args.experiment/'model.json'),'script_sha256':sha(Path(__file__)),
            'classification':'Historical-policy fixed-cap belief experiment. Reused development cohorts, not Elo or a fresh confirmation test.'}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary['primary'],indent=2))


if __name__=='__main__':main()
