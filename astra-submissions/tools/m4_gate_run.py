#!/usr/bin/env python3
"""Sequential, immutable, resumable M4 replay gate. Never an Elo estimate.

Freeze the binary, Stockfish, probe, input-seat manifest and referee hash before
the first decision. Each probe owns a process group: a timeout also removes its
engine descendants. Failures remain in the result ledger and are not retried.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_json(path, value):
    temp = path.with_name(path.name+'.tmp')
    with temp.open('w') as f:
        json.dump(value, f, indent=2, sort_keys=True); f.write('\n')
        f.flush(); os.fsync(f.fileno())
    temp.replace(path)


def bounded_process(command, directory, env, timeout):
    """All descendants inherit this new session; always reap the owned group."""
    start = time.monotonic()
    with (directory/'probe.stdout').open('w') as out, (directory/'probe.stderr').open('w') as err:
        proc = subprocess.Popen(command, stdout=out, stderr=err, env=env, start_new_session=True)
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
    return {'returncode': proc.returncode, 'timed_out': timed_out, 'elapsed':time.monotonic()-start}


def validate(report, case, config, variant, seed):
    """Reject completed-looking output that belongs to another decision/config."""
    expected = {'sha256':config['artifacts']['binary']['sha256'],
                'stockfish_sha256':config['artifacts']['stockfish']['sha256'] if variant=='stockfish' else None,
                'seed':seed, 'seconds':config['seconds'], 'iteration_cap':config['iterations'],
                'fixed_parent_cap':config['parents'], 'sample_target':config['samples'],
                'tactical_witnesses':False, 'child_alternates':variant=='stockfish'}
    for k,v in expected.items():
        if report.get(k)!=v: raise ValueError(f'Probe configuration mismatch: {k}')
    if report.get("tactical_closure",False)!=config.get("tactical_closure",False):
        raise ValueError("Tactical closure setting differs")
    if len(report.get('rows',[]))!=1: raise ValueError('Expected one decision')
    row = report['rows'][0]
    for k in ['game','side','decision','ply','played']:
        if row.get(k)!=case[k]: raise ValueError(f'Probe seat mismatch: {k}')
    if row.get('mode')!=config['mode']: raise ValueError('Probe mode mismatch')
    if row.get('returncode')!=0 or not row.get('prefix_exact') or row.get('outputs')!=case['decision']:
        raise ValueError('Protocol/prefix failed')
    if sorted(row.get('true_safe_moves',[]))!=case['safe_moves']:
        raise ValueError('Referee safe-move set changed')
    if row.get('true_legal_count')!=len(case['legal_moves']):
        raise ValueError('Referee legal-move count changed')
    if not row.get('legal') or row.get('chosen') not in case['legal_moves']:
        raise ValueError('Illegal or absent selected move')
    if row.get('immediate_loss')!=(row['chosen'] not in case['safe_moves']):
        raise ValueError('Candidate outcome disagrees with frozen oracle')
    if config.get('tactical_closure') and not any(m.get('ply')==case['ply'] and not m.get('prefix') for m in row.get('closure_metrics',[])):
        raise ValueError('Enabled tactical closure has no final diagnostic')
    return row


def summary(rows, cases, expected):
    totals = {}
    for variant in ['internal','stockfish']:
        for cohort in ['death','survival']:
            group=[r for r in rows if r['variant']==variant and r['cohort']==cohort]
            good=[r for r in group if r['status']=='ok']
            possible=[r for r in good if not r['unavoidable_immediate_loss']]
            totals[f'{variant}/{cohort}']={'completed':len(group),'valid':len(good),
                'failures':len(group)-len(good), 'immediate_losses':sum(r['immediate_loss'] for r in good),
                'savable_decisions':len(possible), 'savable_saved':sum(not r['immediate_loss'] for r in possible),
                'historical_move_changed':sum(r['chosen']!=r['played'] for r in good),
                'truth_in_belief':sum(r.get('belief_true_states',0)>0 for r in good),
                'tactical_truth_in_belief':sum(r.get('belief_tactical_states',0)>0 for r in good),
                'truth_in_roots':sum(r.get('true_state_roots',0)>0 for r in good),
                'm4_failed_or_missing':sum(not r.get('final_metrics',{}).get('ok',0) for r in good),
                'm4_over_budget':sum(r.get('final_metrics',{}).get('over',0)>0 for r in good),
                'sf_ready':sum(r.get('evaluation',{}).get('ready',0)>0 for r in good),
                'sf_failed_requests':sum(r.get('evaluation',{}).get('failed',0) for r in good)}
    paired=defaultdict(dict)
    for r in rows: paired[(r['case'],r['seed'])][r['variant']]=r
    contrasts=[]
    for key,pair in paired.items():
        if len(pair)!=2 or any(r['status']!='ok' for r in pair.values()):continue
        a,b=pair['internal'],pair['stockfish']
        contrasts.append({'case':key[0],'seed':key[1],'cohort':a['cohort'],
                          'internal_move':a['chosen'],'stockfish_move':b['chosen'],
                          'internal_loss':a['immediate_loss'],'stockfish_loss':b['immediate_loss'],
                          'changed':a['chosen']!=b['chosen']})
    discordance={cohort:dict(Counter(('both_safe' if not r['internal_loss'] and not r['stockfish_loss'] else
                           'both_lose' if r['internal_loss'] and r['stockfish_loss'] else
                           'stockfish_saves' if r['internal_loss'] else 'stockfish_regresses')
                           for r in contrasts if r['cohort']==cohort)) for cohort in ['death','survival']}
    return {'updated_at':now(), 'classification':'selected local replay comparison; paired seeds are not independent games',
            'expected_decisions':expected,'completed':len(rows),'complete':len(rows)==expected,
            'distinct_seats':len(cases),'totals':totals,'paired_outcomes':discordance,'pairs':contrasts,'rows':rows}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seats',type=Path,required=True)
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--binary',type=Path,required=True)
    ap.add_argument('--stockfish',type=Path,required=True)
    ap.add_argument('--probe',type=Path,default=Path(__file__).with_name('m4_replay_probe.py'))
    ap.add_argument('--kit',type=Path,default=Path.home()/'git/fow-starter')
    ap.add_argument('--python',type=Path,default=Path(sys.executable))
    ap.add_argument('--mode',choices=['cold','warm'],default='cold')
    ap.add_argument('--seconds',type=float,default=.5)
    ap.add_argument('--iterations',type=int,default=40)
    ap.add_argument('--parents',type=int,default=20000)
    ap.add_argument('--samples',type=int,default=128)
    ap.add_argument('--seeds',type=int,nargs='+',default=[11,12])
    ap.add_argument('--max-new-jobs',type=int,help='Stop after this many new receipts, then resume with identical config')
    args=ap.parse_args()
    args.run.mkdir(parents=True,exist_ok=True)
    lock=(args.run/'runner.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if len(set(args.seeds))!=len(args.seeds): raise ValueError('Duplicate seeds')
    if args.seconds<=0 or args.iterations<1 or not 2000<=args.parents<=2000000 or not 1<=args.samples<=4096:
        raise ValueError('Invalid replay budget')
    cases=json.loads(args.seats.read_text())['cases']
    if len(cases)!=48 or Counter(r['cohort'] for r in cases)!={'death':24,'survival':24}:
        raise ValueError('Expected frozen 24+24 gate')
    artifacts={k:{'source':str(p.resolve()),'sha256':sha(p)} for k,p in
               [('binary',args.binary),('stockfish',args.stockfish),('probe',args.probe),('seats',args.seats),('runner',Path(__file__))]}
    config={'schema':1,'artifacts':artifacts,'referee':str((args.kit/'referee.py').resolve()),
            'referee_sha256':sha(args.kit/'referee.py'),'python':str(args.python.absolute()),
            'kit':str(args.kit.resolve()),'mode':args.mode,'seconds':args.seconds,'iterations':args.iterations,
            'parents':args.parents,'samples':args.samples,'seeds':args.seeds,'cpu_affinity':sorted(os.sched_getaffinity(0)),
            'nice':os.getpriority(os.PRIO_PROCESS,0), 'order':'interleaved cohorts; seeds; balanced variant order',
            'classification':'offline diagnostic; forced historical prefix; no Elo inference'}
    manifest=args.run/'manifest.json'
    if manifest.exists():
        old=json.loads(manifest.read_text());old.pop('created_at')
        if old!=config: raise ValueError('Frozen configuration differs; use a new run directory')
    else:
        for k,v in artifacts.items():
            p=args.run/(k+('.py' if k in ['probe','runner'] else '.json' if k=='seats' else ''))
            shutil.copyfile(v['source'],p)
            if k in ['binary','stockfish']:p.chmod(0o755)
        write_json(manifest,dict(config,created_at=now()))
    for k,v in artifacts.items():
        p=args.run/(k+('.py' if k in ['probe','runner'] else '.json' if k=='seats' else ''))
        if sha(p)!=v['sha256']:raise ValueError(f'Frozen artifact changed: {k}')
    for case in cases:
        if sha(Path(case['cache']))!=case['cache_sha256']:raise ValueError(f'Input changed: {case["case"]}')
    ordered=sorted(cases,key=lambda c:(int(c['case'][1:]),c['cohort']))
    jobs=[]
    for i,case in enumerate(ordered):
        for j,seed in enumerate(args.seeds):
            variants=['internal','stockfish'] if (i+j)%2==0 else ['stockfish','internal']
            jobs.extend((case,seed,v) for v in variants)
    rows=[];new=0
    for case,seed,variant in jobs:
        key=f'{case["case"]}-seed{seed}-{variant}'
        directory=args.run/'jobs'/key;receipt=directory/'receipt.json'
        if receipt.exists():
            r=json.loads(receipt.read_text())
            if r['config_sha256']!=sha(manifest) or r['case']!=case['case'] or r['seed']!=seed or r['variant']!=variant:
                raise ValueError(f'Invalid cached receipt: {key}')
            for path,digest in r['file_hashes'].items():
                if sha(directory/path)!=digest:raise ValueError(f'Changed job output: {key}/{path}')
            rows.append(r);continue
        if args.max_new_jobs is not None and new>=args.max_new_jobs:continue
        if directory.exists():
            # An interrupted attempt has no receipt; preserve it instead of overwriting.
            directory.rename(directory.with_name(key+'-interrupted-'+str(time.time_ns())))
        directory.mkdir(parents=True)
        command=[str(args.python),str(args.run/'probe.py'),case['cache'],'--binary',str(args.run/'binary'),
                 '--out',str(directory),'--kit',str(args.kit),'--side',case['side'],'--decision',str(case['decision']),
                 '--mode',args.mode,'--seconds',str(args.seconds),'--iterations',str(args.iterations),
                 '--parents',str(args.parents),'--samples',str(args.samples),'--seed',str(seed),'--audit-belief']
        if variant=='stockfish':command.extend(['--stockfish',str(args.run/'stockfish')])
        env={k:v for k,v in os.environ.items() if not k.startswith('MIST_') and k!='FOW_SEED'}
        write_json(directory/'command.json',{'argv':command,'started_at':now(),'cleared_env':'all inherited MIST_* and FOW_SEED'})
        if sha(args.kit/'referee.py')!=config['referee_sha256']:raise ValueError('Referee changed during gate')
        result=bounded_process(command,directory,env,max(90,case['decision']*args.seconds*3+30))
        r={'case':case['case'],'cohort':case['cohort'],'seed':seed,'variant':variant,
           'opponent':case['opponent'],'config_sha256':sha(manifest),'completed_at':now(),
           'status':'failed','process':result,'played':case['played']}
        try:
            if result['returncode']!=0 or result['timed_out']:raise ValueError('Probe process failed or timed out')
            report=json.loads((directory/'results.json').read_text())
            row=validate(report,case,config,variant,seed)
            omit={'metrics','action_profiles','prefix_evaluation','true_safe_moves'}
            r.update({k:v for k,v in row.items() if k not in omit})
            r['final_metrics']=next((v for v in reversed(row['metrics']) if not v['prefix']),{})
            r['prefix_sf_failures']=sum(v.get('failed',0) for v in row.get('prefix_evaluation',[]))
            r['status']='ok'
        except (ValueError,KeyError,OSError,TypeError) as e:r['error']=str(e)
        r['file_hashes']={p.name:sha(p) for p in directory.iterdir() if p.is_file()}
        write_json(receipt,r)
        with (args.run/'progress.jsonl').open('a') as f:
            f.write(json.dumps(r,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        rows.append(r);new+=1
        write_json(args.run/'summary.json',summary(rows,cases,len(jobs)))
        print(json.dumps({'job':key,'status':r['status'],'chosen':r.get('chosen'),
                          'loss':r.get('immediate_loss'),'elapsed':round(result['elapsed'],2),
                          'done':len(rows),'expected':len(jobs)},sort_keys=True),flush=True)
    write_json(args.run/'summary.json',summary(rows,cases,len(jobs)))
    print(json.dumps({'run':str(args.run),'completed':len(rows),'expected':len(jobs),'new':new}),flush=True)


if __name__=='__main__':main()
