#!/usr/bin/env python3
"""Complete missing calls after a documented root-only diagnostic false alarm.

Preserve the original failed receipt and all 133 first-attempt outputs.
The engine, original plan/runner, thresholds and selected decisions are fixed.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_gate',HERE/'run.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
OUT=gate.OUT;REC=OUT/'recovery'

def root_only(stderr):
    rows=[line for line in stderr.splitlines() if line.startswith('mist: n=')]
    if not rows:return False
    values={k:int(v) for k,v in re.findall(r'(?:^| )(samples|moves|infosets|nodes)=(\d+)',rows[-1])}
    return (set(values)=={'samples','moves','infosets','nodes'} and values['infosets']==1
            and values['samples']>0 and values['moves']>0
            and values['nodes']==1+values['samples']*(1+values['moves']))

def prepare():
    assert json.loads((OUT/'execution.json').read_text())['status']=='failed'
    plan=json.loads((OUT/'plan.json').read_text());rows=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()))
    found={(r['name'],r['arm']) for r in rows};assert len(found)==len(rows)==133
    exceptions=[]
    for r in rows:
        assert r['protocol_valid'] and r['returncode']==0 and not r['error']
        for ext in ('stdout','stderr'):
            assert gate.sha((OUT/(r['name']+'-'+r['arm']+'.'+ext)).read_bytes())==r[ext+'_sha256']
        if r['arm']!='original' and r['search'].get('nodes',0)>0 and r['coverage'] is None:
            text=(OUT/(r['name']+'-'+r['arm']+'.stderr')).read_text();assert root_only(text)
            assert not root_only(text.replace('infosets=1 ','infosets=2 '))
            assert not root_only(text.replace('nodes=113 ','nodes=114 '))
            exceptions.append([r['name'],r['arm']])
    assert exceptions==[['937dbqbv-41','learned']],exceptions
    missing=[(case['name'],arm) for i,case in enumerate(plan['cases'])
             for arm in gate.ARMS[i%4:]+gate.ARMS[:i%4] if (case['name'],arm) not in found]
    assert len(missing)==23 and len(set(missing))==23
    REC.mkdir(exist_ok=False)
    recovery=dict(original_plan_sha256=gate.sha((OUT/'plan.json').read_bytes()),
                  original_receipts_sha256=gate.sha((OUT/'receipts.jsonl').read_bytes()),
                  original_execution_sha256=gate.sha((OUT/'execution.json').read_bytes()),
                  recovery_source_sha256=gate.sha(Path(__file__).read_bytes()),missing=missing,
                  exceptions=exceptions,policy='No repeated cells, changed engine bytes, selection or scoring thresholds. A tree with only the root information set has no opponent model query to report.',
                  source_basis='gtcfr.c root uses player0; expanded replies create another infoset and invoke dbr_install; dbr_report returns when lazy visible_config has never run.',
                  root_only_check_tests=3)
    gate.dump(REC/'plan.json',recovery);print(json.dumps(recovery,indent=2))

def run():
    recovery=json.loads((REC/'plan.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    for filename,key in [('plan.json','original_plan_sha256'),('receipts.jsonl','original_receipts_sha256'),('execution.json','original_execution_sha256')]:
        assert gate.sha((OUT/filename).read_bytes())==recovery[key]
    assert gate.sha(Path(__file__).read_bytes())==recovery['recovery_source_sha256']
    assert gate.sha((HERE/'run.py').read_bytes())==plan['runner_sha256']
    assert gate.sha((HERE/'README.md').read_bytes())==plan['readme_sha256']
    for arm,path in plan['binaries'].items():assert gate.sha(Path(path).read_bytes())==plan['binary_sha256'][arm]
    for p,h in [(gate.MODEL,plan['model_sha256']),(gate.BASE/'bin/stockfish',plan['stockfish_sha256']),(gate.BASE/'data/history.bin',plan['history_sha256'])]:
        assert gate.sha(p.read_bytes())==h
    execution=dict(status='running',pid=os.getpid(),completed=0)
    with (REC/'execution.json').open('x') as f:json.dump(execution,f)
    try:
        with (REC/'receipts.jsonl').open('x') as sink:
            for name,arm in recovery['missing']:
                case=next(c for c in plan['cases'] if c['name']==name)
                feed=(OUT/(name+'.input.txt')).read_text();assert gate.sha(feed.encode())==case['input_sha256']
                env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
                env.update(MIST_FORCE_MOVES=','.join(case['forced']),MIST_MAX_SECONDS=str(plan['seconds']),
                           MIST_STOCKFISH=str(gate.BASE/'bin/stockfish'),MIST_HISTORY_TABLE=str(gate.BASE/'data/history.bin'),FOW_SEED=str(plan['seed']),OMP_NUM_THREADS='1')
                if arm!='original':env.update(ASTRA_VISIBLE_CONFIDENCE=str(plan['confidence']),ASTRA_VISIBLE_MODEL=plan['model'])
                if arm=='projected':env['ASTRA_VISIBLE_PROJECT']='1'
                start=time.monotonic();error=None
                proc=subprocess.Popen(['taskset','-c',plan['cores'],plan['binaries'][arm]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
                try:stdout,stderr=proc.communicate(feed,timeout=plan['timeout_seconds'])
                except subprocess.TimeoutExpired:gate.kill_tree(proc.pid);stdout,stderr=proc.communicate();error='bounded diagnostic timeout'
                for ext,content in [('stdout',stdout),('stderr',stderr)]:
                    with (REC/(name+'-'+arm+'.'+ext)).open('x') as f:f.write(content)
                moves=gate.parse_moves(stdout);valid=proc.returncode==0 and moves is not None and len(moves)==len(case['forced'])+1 and moves[:-1]==case['forced']
                reports=[l for l in stderr.splitlines() if l.startswith('astra_visible: opponent_sets ')];coverage=None
                if reports:
                    parts=reports[-1].split()[1:];coverage={parts[i]:float(parts[i+1]) for i in range(0,len(parts),2)}
                lines=[l for l in stderr.splitlines() if l.startswith('mist: n=')]
                stats=dict((k,float(v)) for k,v in re.findall(r'(?:^| )(nodes|iters|p|v|clock)=([+\-\d.]+)',lines[-1])) if lines else {}
                row=dict(name=name,arm=arm,returncode=proc.returncode,error=error,protocol_valid=valid,move=moves[-1] if valid else None,
                         elapsed=time.monotonic()-start,coverage=coverage,search=stats,stdout_sha256=gate.sha(stdout.encode()),stderr_sha256=gate.sha(stderr.encode()))
                sink.write(json.dumps(row)+'\n');sink.flush();execution['completed']+=1;gate.dump(REC/'execution.json',execution)
                assert valid and not error,row
                if arm!='original' and coverage:assert not any(coverage[k] for k in ('failures','mismatches','load_failed')),row
                if arm!='original' and stats.get('nodes',0)>0 and coverage is None:assert root_only(stderr),row
                print(execution['completed'],len(recovery['missing']),name,arm,row['move'],flush=True)
        execution['status']='complete'
    except BaseException:execution['status']='failed';raise
    finally:gate.dump(REC/'execution.json',execution)

def summarize():
    assert json.loads((REC/'execution.json').read_text())['status']=='complete'
    plan=json.loads((OUT/'plan.json').read_text());view=REC/'merged';view.mkdir(exist_ok=False)
    rows=[]
    for directory in (OUT,REC):
        current=list(map(json.loads,(directory/'receipts.jsonl').read_text().splitlines()));rows+=current
        for r in current:
            for ext in ('stdout','stderr'):
                name=r['name']+'-'+r['arm']+'.'+ext;(view/name).symlink_to(directory/name)
    assert len({(r['name'],r['arm']) for r in rows})==len(rows)==len(plan['cases'])*4
    (view/'plan.json').symlink_to(OUT/'plan.json')
    gate.dump(view/'execution.json',dict(status='complete',scope='Combined first attempts; original failed execution and explicit recovery retained.',original_calls=133,recovery_calls=23))
    (view/'receipts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    gate.OUT=view;gate.summarize()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','summarize']);globals()[p.parse_args().command]()
