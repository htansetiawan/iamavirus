#!/usr/bin/env python3
"""Paired fixed-cap, fixed-history gate; seeds are replicates, not new games."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from m4_prior_fit import bootstrap


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
def rows(p):return [json.loads(x) for x in read(p).decode().splitlines()]
def semantic(r):return {k:v for k,v in r.items() if k!='update_cpu_seconds'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seeds',type=int,nargs='+',default=[41,73,109]);a=ap.parse_args()
    a.out.mkdir(exist_ok=False);shutil.copytree(a.build,a.out/'native');shutil.copyfile(__file__,a.out/'run.py')
    shutil.copyfile(Path(__file__).with_name('m4_prior_fit.py'),a.out/'m4_prior_fit.py')
    shutil.copyfile(a.previous/'base26.txt',a.out/'base26.txt')
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4'))}
    env.update(MIST_MODEL='1',MIST_MODEL_TEMP='1',MIST_MODEL_FULL_BELOW='10000')
    primary=set();inputs={}
    for name in ['sequential02','sequential-fresh26']:
        old=a.previous/name;target=a.out/name;target.mkdir()
        (target/'input.txt').write_bytes(read(old/'input.txt.packed.gz'))
        shutil.copyfile(old/'input-manifest.json',target/'input-manifest.json')
        manifest=json.loads((target/'input-manifest.json').read_text())
        primary.update(g['id'] for g in manifest['games'] if g['cohort']!='diagnostic')
        inputs[name]={'input_sha256':sha(target/'input.txt'),'baseline':old/'rows.jsonl.packed.gz'}
    runs=[];data={}
    for seed in a.seeds:
        for arm in ['control','finite','raw']:
            all_rows=[]
            for name in inputs:
                target=a.out/name;stem=f'{arm}-{seed}';e=dict(env)
                if arm!='control':e['M4_CAP_MODE']=arm
                start=time.monotonic()
                with (target/(stem+'.jsonl')).open('w') as stdout,(target/(stem+'.stderr')).open('w') as stderr:
                    p=subprocess.run([str(a.out/'native/runner'),str(target/'input.txt'),str(a.out/'base26.txt'),'10000',str(seed)],
                                     env=e,stdout=stdout,stderr=stderr,timeout=300)
                result={'cohort':name,'arm':arm,'seed':seed,'returncode':p.returncode,'seconds':time.monotonic()-start}
                runs.append(result);(target/(stem+'-status.json')).write_text(json.dumps(result,indent=2)+'\n')
                if p.returncode:raise RuntimeError(str(result))
                current=rows(target/(stem+'.jsonl'))
                if arm=='control' and seed==41:
                    assert list(map(semantic,current))==list(map(semantic,rows(inputs[name]['baseline'])))
                    result['original_exact_nontiming_parity']=True
                for r in current:assert not r['inconsistent'] and not r['cheap_calls']
                all_rows+=current;print(json.dumps(result),flush=True)
            data[(arm,seed)]=all_rows
            if arm!='control':
                control=data[('control',seed)]
                assert len(control)==len(all_rows)
                for x,y in zip(control,all_rows):
                    for k in ['game','ply','side','move','actual_attack','actual_fatal']:assert x[k]==y[k]
    report={'classification':'Reused development games, fixed historical policy, cap10000. No Elo inference.',
            'seeds':a.seeds,'runs':runs,'per_seed':{},'paired_game_bootstrap':{},'zero_switch_exact_nontiming_parity':41 in a.seeds}
    aggregate={arm:[] for arm in ['control','finite','raw']}
    for seed in a.seeds:
        summary={}
        for arm in aggregate:
            rr=[r for r in data[(arm,seed)] if r['game'] in primary];last={r['game']:r for r in rr}
            summary[arm]={'games':len(last),'decisions':len(rr),'truth_present':sum(r['truth_present'] for r in rr),
                          'collapses':sum(r['collapses'] for r in last.values()),
                          'cpu_seconds':sum(r['update_cpu_seconds'] for r in last.values())}
            for metric in ['attack','fatal']:
                summary[arm][metric+'_brier']=float(np.mean([(r[metric+'_probability']-r['actual_'+metric])**2 for r in rr]))
            aggregate[arm]+=rr
        report['per_seed'][str(seed)]=summary
    # Bootstrap whole game IDs, keeping all their decisions and all seed replicates together.
    base=aggregate['control'];groups=np.array([r['game'] for r in base])
    for arm in ['finite','raw']:
        candidate=aggregate[arm];d={}
        delta=np.array([b['truth_present']-x['truth_present'] for x,b in zip(base,candidate)])
        d['truth_support_gain']=bootstrap(delta,groups)
        for metric in ['attack','fatal']:
            diff=np.array([(x[metric+'_probability']-x['actual_'+metric])**2-(b[metric+'_probability']-b['actual_'+metric])**2 for x,b in zip(base,candidate)])
            d[metric+'_brier_reduction']=bootstrap(diff,groups)
        report['paired_game_bootstrap'][arm]=d
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['per_seed'],indent=2),flush=True)
    (a.out/'complete.json').write_text(json.dumps({'files':{str(p.relative_to(a.out)):sha(p) for p in sorted(a.out.rglob('*')) if p.is_file()}},indent=2)+'\n')


if __name__=='__main__':main()
