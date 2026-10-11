#!/usr/bin/env python3
"""Run immutable support diagnostics and require exact original replay parity."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(p):return gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
def rows(p):return [json.loads(x) for x in unpack(p).decode().splitlines()]
def semantic(seq):return [{k:v for k,v in r.items() if k!='update_cpu_seconds'} for r in seq]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(exist_ok=False)
    shutil.copytree(args.build,args.out/'build');shutil.copyfile(__file__,args.out/'run.py')
    shutil.copyfile(args.previous/'base26.txt',args.out/'base26.txt')
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','M4'))}
    env.update(MIST_MODEL='1',MIST_MODEL_TEMP='1',MIST_MODEL_FULL_BELOW='10000')
    all_trace=[];all_rows=[];metadata=[];primary=set()
    for name in ['sequential02','sequential-fresh26']:
        old=args.previous/name;target=args.out/name;target.mkdir()
        source=old/'original-input.txt.packed.gz';(target/'input.txt').write_bytes(unpack(source))
        manifest=json.loads((old/'original-manifest.json').read_text())
        primary.update(g['id'] for g in manifest['games'] if g['cohort']!='diagnostic')
        shutil.copyfile(old/'original-manifest.json',target/'input-manifest.json')
        baseline=rows(old/'control26.jsonl.packed.gz')
        begin=time.monotonic()
        with (target/'rows.jsonl').open('w') as stdout,(target/'trace.jsonl').open('w') as stderr:
            run=subprocess.run([str(args.out/'build/runner'),str(target/'input.txt'),str(args.out/'base26.txt'),'10000','41'],
                               env=env,stdout=stdout,stderr=stderr,timeout=180)
        status={'returncode':run.returncode,'wall_seconds':time.monotonic()-begin}
        (target/'status.json').write_text(json.dumps(status,indent=2)+'\n')
        if run.returncode:raise RuntimeError(f'Failed trace: {name}')
        current=rows(target/'rows.jsonl')
        if semantic(current)!=semantic(baseline):raise RuntimeError(f'Original parity failed: {name}')
        trace=[json.loads(s) for s in (target/'trace.jsonl').read_text().splitlines() if s.startswith('{')]
        by_position={(r['game'],r['ply']):r for r in current}
        mass_errors=[]
        for t in trace:
            assert t['kept']==min(t['unique'],t['cap'])
            assert t['truth_kept']<=t['truth_candidate']
            assert 0<=t['truth_share_before_cap']<=1
            assert 0<=t['retained_mass']<=1.00000001
            a=by_position.get((t['game'],t['ply']))
            if a and t['truth_candidate']:
                expected=t['truth_share_before_cap']/t['retained_mass'] if t['truth_kept'] else 0
                mass_errors.append(abs(a['truth_share']-expected))
                assert a['truth_present']==t['truth_kept']
        all_trace.extend(trace);all_rows.extend(current)
        metadata.append({'cohort':name,'input_sha256':sha(target/'input.txt'),'baseline_sha256':sha(old/'control26.jsonl.packed.gz'),
                         'rows':len(current),'non_timing_parity':True,'mass_crosscheck_rows':len(mass_errors),
                         'mass_max_absolute_error':max(mass_errors,default=0),
                         'mass_note':'Pre-cap weights differ from committed weights by float32 recentering; report numeric discrepancy without asserting exact real-arithmetic equality.',**status})
        print(json.dumps(metadata[-1]),flush=True)
    first_loss={};losses=[];filter_failures=[]
    for t in all_trace:
        if t['parent_supported'] and not t['truth_kept']:
            losses.append(t);first_loss.setdefault(t['game'],t)
            if not t['truth_candidate']:filter_failures.append(t)
    first_own={}
    for r in all_rows:
        if not r['truth_present']:first_own.setdefault(r['game'],r['ply'])
    # Every first unsupported own turn must have a causal earlier trace event.
    unexplained={g:p for g,p in first_own.items() if g not in first_loss or first_loss[g]['ply']!=p}
    result={'cohorts':metadata,'trace_events':len(all_trace),'decision_rows':len(all_rows),
            'primary_games':len(primary),'games_with_support_loss':len(first_own),
            'first_support_losses':list(first_loss.values()),'all_supported_parent_losses':losses,
            'supported_parent_filter_failures':filter_failures,'unexplained_first_losses':unexplained,
            'all_non_timing_rows_match':True,'runtime_change':False,
            'limitation':'Fixed cap 10,000, one seed, reused historical-policy development cohort. Not a live-cap or playing-strength result.'}
    (args.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['cohorts','first_support_losses','all_supported_parent_losses']}),flush=True)
    if unexplained or filter_failures:raise RuntimeError('Unexplained/filter support loss: inspect report before proceeding')
    (args.out/'complete.json').write_text(json.dumps({'files':{str(p.relative_to(args.out)):sha(p) for p in sorted(args.out.rglob('*')) if p.is_file()}},indent=2)+'\n')


if __name__=='__main__':main()
