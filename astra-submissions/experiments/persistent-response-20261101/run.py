#!/usr/bin/env python3
"""Fresh private-history comparison, fixed before any candidate decisions."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-response-20261101'
BASE=HERE.parent/'stable-mix-20261101/build/base'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol, exchange_probe
from learning import ingest, move_taxonomy
from learning.compare_archives import kill_tree
ARMS=['original','local','off','persistent']
PRIOR=HERE.parent/'observable-response-search-20261101'
TEAMS=['Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','Crimson Fog',
       'Instructors','Mist Opportunities','duck','HYPOTHERMIA']

def sha(payload):return hashlib.sha256(payload).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def parse_moves(stdout):
    lines=stdout.splitlines()
    if not lines or lines[0]!='ready':return None
    out=[]
    for line in lines[1:]:
        m=re.fullmatch(r'move ([a-h][1-8][a-h][1-8][qrbn]?)',line)
        if not m:return None
        out.append(m[1])
    return out

def freeze():
    assert not (OUT/'plan.json').exists()
    raw=(ROOT/'data/raw/accepted.jsonl').read_bytes();rows={r['id']:r for r in map(json.loads,raw.splitlines())}
    excluded=set()
    for rel in ['frozen-tree-20261101/plan.json','frozen-tree-20261101/early/plan.json','data-biased-search-20261101/plan.json','learned-response-search-20261101/plan.json','observable-response-search-20261101/plan.json']:
        excluded.update(c['game'] for c in json.loads((OUT.parent/rel).read_text())['cases'])
    selected=[]
    for side in ('white','black'):
        other='black' if side=='white' else 'white'
        choices=[r for r in rows.values() if r['id'] not in excluded and r.get(side)=='IAmAVirus'
                 and r.get(side+'Version')==37 and r.get(other) in TEAMS
                 and (r.get('createdAt') or '').startswith('2026-11-01')]
        choices.sort(key=lambda r:sha(('persistent-response214:'+r['id']).encode()))
        assert len(choices)>=4,(side,len(choices));selected.extend((r,side) for r in choices[:4])
    cases=[];games=[]
    for row,key in selected:
        side=('white','black').index(key);other=('black','white')[side]
        payload=(ROOT/'data/raw/games'/row['id']/'replay.json').read_bytes();rp=json.loads(payload)
        states,errors=ingest.validate_replay(rp);assert not errors,(row['id'],errors)
        games.append(dict(game=row['id'],side=side,opponent=row[other],opponent_version=row[other+'Version'],
                          result=row['result'],frames=len(states),replay_sha256=sha(payload)))
        own=list(range(side,len(states)-1,2))
        plies=sorted(set([side+16,side+32,side+48]+own[-2:])&set(own))
        for ply in plies:
            feed,forced=protocol(rp,ply,side);redacted=json.loads(payload)
            for i,frame in enumerate(redacted['frames']):
                frame['board']='X'*64;frame[other]='X'*64
                if i==0 or (i-1)%2!=side or i>ply:frame['move']='REDACTED'
            assert protocol(redacted,ply,side)==(feed,forced)
            name=f"{row['id']}-{ply}"
            (OUT/(name+'.input.txt')).write_text(feed)
            cases.append(dict(name=name,game=row['id'],ply=ply,side=side,opponent=row[other],forced=forced,
                              input_sha256=sha(feed.encode()),replay_sha256=sha(payload)))
    provenance=json.loads((HERE/'provenance.json').read_text())
    for path,digest in provenance['source_sha256'].items():assert sha((ROOT/path).read_bytes())==digest,path
    binaries={'original':str(BASE/'mist'),'local':str(PRIOR/'build/mist'),'off':str(HERE/'build/mist'),'persistent':str(HERE/'build/mist')}
    assert sha(Path(binaries['persistent']).read_bytes())==provenance['binary_sha256']
    tests=json.loads((OUT/'native-tests.json').read_text())
    assert len(tests['runs'])==20 and all(r['returncode']==0 for r in tests['runs'])
    for path,digest in tests['source_sha256'].items():assert sha(Path(path).read_bytes())==digest,path
    assert json.loads((OUT.parent/'learned-response-search-20261101/adapter-tests.json').read_text())['actual_actor_queries']>=1000
    plan=dict(created_at=datetime.now(timezone.utc).isoformat(),games=games,cases=cases,excluded_games=sorted(excluded),
              source_accepted_sha256=sha(raw),provenance=provenance,arms=ARMS,binaries=binaries,
              binary_sha256={a:sha(Path(p).read_bytes()) for a,p in binaries.items()},
              runner_sha256=sha(Path(__file__).read_bytes()),readme_sha256=sha((HERE/'README.md').read_bytes()),
              helper_sha256={str(p):sha(p.read_bytes()) for p in [ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',ROOT/'learning/ingest.py',ROOT/'learning/move_taxonomy.py',ROOT/'learning/compare_archives.py',Path('/usr/bin/time')]},
              validation_sha256={p.name:sha(p.read_bytes()) for p in [OUT/'native-tests.json',OUT/'math-tests.json']},
              model=str(MODEL),model_sha256=sha(MODEL.read_bytes()),
              history_sha256=sha((BASE/'data/history.bin').read_bytes()),stockfish_sha256=sha((BASE/'bin/stockfish').read_bytes()),
              seconds=2.5,seed=2141101,confidence=.25,cores='0,1',timeout_seconds=120,
              selection='ID-hash selected four games each colour; no outcomes; own turns9,17,25 and final two own decisions, deduplicated.',
              truth_to_engine=False,scope='Mechanism and bounded safety diagnostic; not a strength estimate.',
              gate=dict(no_technical_errors=True,no_extra_king_loss_vs_any_control=True,no_extra_queen_loss_vs_any_control=True,
                        allowed_extra_material_vs_worse_control=1,minimum_choices_changed_vs_off=3,
                        minimum_change_excess_over_off_original=2,minimum_coverage_case_share=.75,
                        first_reply_coverage_threshold=.125,maximum_median_model_seconds=.25,minimum_median_node_ratio=.6,maximum_peak_rss_kb=3500000,
                        minimum_total_projected_sets=1))
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
    assert parse_moves('ready\nmove e2e4\nmove e7e8q\n')==['e2e4','e7e8q']
    for bad in ['ready\ne2e4\n','e2e4\n','ready\nmove e7e8k\n']:assert parse_moves(bad) is None
    print(json.dumps(dict(games=games,decisions=len(cases),executions=len(ARMS)*len(cases)),indent=2))

def run():
    plan=json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__).read_bytes())==plan['runner_sha256']
    assert sha((HERE/'README.md').read_bytes())==plan['readme_sha256']
    for p,h in plan['helper_sha256'].items():assert sha(Path(p).read_bytes())==h,p
    for p,h in plan['validation_sha256'].items():assert sha((OUT/p).read_bytes())==h,p
    for a,p in plan['binaries'].items():assert sha(Path(p).read_bytes())==plan['binary_sha256'][a]
    for p,h in [(MODEL,plan['model_sha256']),(BASE/'bin/stockfish',plan['stockfish_sha256']),(BASE/'data/history.bin',plan['history_sha256'])]:assert sha(p.read_bytes())==h
    execution=OUT/'execution.json';state=dict(status='running',pid=os.getpid(),pgid=os.getpgid(0),starttime=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],started_at=datetime.now(timezone.utc).isoformat(),completed=0)
    with execution.open('x') as f:json.dump(state,f)
    try:
        with (OUT/'receipts.jsonl').open('x') as sink:
            for number,case in enumerate(plan['cases']):
                feed=(OUT/(case['name']+'.input.txt')).read_text();assert sha(feed.encode())==case['input_sha256']
                for arm in ARMS[number%len(ARMS):]+ARMS[:number%len(ARMS)]:
                    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
                    env.update(MIST_FORCE_MOVES=','.join(case['forced']),MIST_MAX_SECONDS=str(plan['seconds']),
                               MIST_STOCKFISH=str(BASE/'bin/stockfish'),MIST_HISTORY_TABLE=str(BASE/'data/history.bin'),
                               FOW_SEED=str(plan['seed']),OMP_NUM_THREADS='1')
                    if arm!='original':env.update(ASTRA_VISIBLE_CONFIDENCE='0' if arm=='off' else str(plan['confidence']),ASTRA_VISIBLE_MODEL=plan['model'],ASTRA_VISIBLE_PROJECT='1',ASTRA_PERSISTENT='1' if arm=='persistent' else '0')
                    begin=time.monotonic();error=None
                    usage=OUT/(case['name']+'-'+arm+'.usage.json')
                    assert not usage.exists(),usage
                    proc=subprocess.Popen(['/usr/bin/time','-f','{"max_rss_kb":%M,"user_seconds":%U,"system_seconds":%S}','-o',str(usage),'taskset','-c',plan['cores'],plan['binaries'][arm]],stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
                    try:stdout,stderr=proc.communicate(feed,timeout=plan['timeout_seconds'])
                    except subprocess.TimeoutExpired:
                        kill_tree(proc.pid);stdout,stderr=proc.communicate();error='bounded diagnostic timeout'
                    name=case['name']+'-'+arm
                    for ext,content in [('stdout',stdout),('stderr',stderr)]:
                        with (OUT/(name+'.'+ext)).open('x') as f:f.write(content)
                    moves=parse_moves(stdout)
                    valid=proc.returncode==0 and moves is not None and len(moves)==len(case['forced'])+1 and moves[:-1]==case['forced']
                    reports=[line for line in stderr.splitlines() if line.startswith('astra_visible: opponent_sets ')]
                    coverage=None
                    if reports:
                        parts=reports[-1].split()[1:];coverage={parts[i]:float(parts[i+1]) for i in range(0,len(parts),2)}
                    engine=[line for line in stderr.splitlines() if line.startswith('mist: n=')]
                    stats=dict((k,float(v)) for k,v in re.findall(r'(?:^| )(nodes|iters|p|v|clock|samples|moves)=([+\-\d.]+)',engine[-1])) if engine else {}
                    mode_reports=[line for line in stderr.splitlines() if line.startswith('astra_persistent: ')]
                    mode_info=None
                    if mode_reports:
                        parts=mode_reports[-1].split()[1:];mode_info={parts[i]:float(parts[i+1]) for i in range(0,len(parts),2)}
                    usage_info=json.loads(usage.read_text()) if usage.exists() and usage.read_text().lstrip().startswith('{') else None
                    row=dict(name=case['name'],arm=arm,mode=mode_info,usage=usage_info,returncode=proc.returncode,error=error,protocol_valid=valid,
                             move=moves[-1] if valid else None,elapsed=time.monotonic()-begin,coverage=coverage,search=stats,
                             stdout_sha256=sha(stdout.encode()),stderr_sha256=sha(stderr.encode()),usage_sha256=sha(usage.read_bytes()) if usage.exists() else None)
                    sink.write(json.dumps(row)+'\n');sink.flush();state['completed']+=1;dump(execution,state)
                    print(state['completed'],len(ARMS)*len(plan['cases']),name,row['move'],round(row['elapsed'],2),coverage,flush=True)
                    if not valid or error:raise RuntimeError(row)
                    if arm!='original' and coverage and any(coverage[k] for k in ['failures','mismatches','load_failed']):raise RuntimeError(row)
                    if arm=='persistent' and stats.get('nodes',0)>0:
                        assert coverage is not None and mode_info is not None,row
                        assert mode_info['prior']==.25 and mode_info['branches']==2*mode_info['physical_worlds'],row
                    assert usage_info is not None,row
        state['status']='complete'
    except BaseException:
        state['status']='failed';raise
    finally:
        state['ended_at']=datetime.now(timezone.utc).isoformat();dump(execution,state)

def summarize():
    plan=json.loads((OUT/'plan.json').read_text());assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    receipts=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()));keyed={(r['name'],r['arm']):r for r in receipts}
    assert len(keyed)==len(receipts)==len(plan['cases'])*len(ARMS)
    labelled=[];cache={}
    for case in plan['cases']:
        if case['game'] not in cache:
            raw=(ROOT/'data/raw/games'/case['game']/'replay.json').read_bytes();assert sha(raw)==case['replay_sha256']
            rp=json.loads(raw);states,errors=ingest.validate_replay(rp);assert not errors
            cache[case['game']]=(states,{r['ply']-1:r['tags'] for r in move_taxonomy.label_game(rp)['moves']})
        states,tags=cache[case['game']];state=states[case['ply']]
        safe=[m for m in state.board.legal_moves() if not state.board.move_loses_king(m)]
        row=dict(name=case['name'],game=case['game'],ply=case['ply'],opponent=case['opponent'],safe_moves=safe,
                 recorded_move_tags=tags[case['ply']],arms={})
        for arm in ARMS:
            r=keyed[(case['name'],arm)];assert r['protocol_valid'] and r['returncode']==0
            for ext in ['stdout','stderr']:assert sha((OUT/(case['name']+'-'+arm+'.'+ext)).read_bytes())==r[ext+'_sha256']
            assert sha((OUT/(case['name']+'-'+arm+'.usage.json')).read_bytes())==r['usage_sha256']
            label=exchange_probe(state,r['move']);assert label['legal']
            row['arms'][arm]=dict(mode=r['mode'],usage=r['usage'],move=r['move'],label=label,coverage=r['coverage'],elapsed=r['elapsed'],search=r['search'])
        labelled.append(row)
    summary={}
    for arm in ARMS:
        group=[r['arms'][arm] for r in labelled]
        summary[arm]=dict(king_loss=sum(r['label']['fatal'] for r in group),
                          exchange_loss_ge2=sum((r['label']['exchange_loss'] or 0)>=2 for r in group),
                          queen_loss_ge4=sum((r['label']['queen_exchange_loss'] or 0)>=4 for r in group),
                          median_elapsed=statistics.median(r['elapsed'] for r in group),
                          median_nodes=statistics.median(r['search'].get('nodes',0) for r in group),maximum_peak_rss_kb=max(r['usage']['max_rss_kb'] for r in group))
    changes=sum(r['arms']['persistent']['move']!=r['arms']['off']['move'] for r in labelled)
    noise=sum(r['arms']['off']['move']!=r['arms']['original']['move'] for r in labelled)
    cov=[r['arms']['persistent']['coverage'] for r in labelled if r['arms']['persistent']['coverage'] is not None and sum(r['arms']['persistent']['mode'][k] for k in ['free_expansions','fixed_expansions'])>0]
    median_time=statistics.median(c['seconds'] for c in cov) if cov else 0
    share=sum(c['first_reply_coverage']>=.125 for c in cov)/len(cov) if cov else 0
    controls=[summary[a] for a in ['original','off']];candidate=summary['persistent']
    checks=dict(technical=all(not c[k] for c in cov for k in ['failures','mismatches','load_failed']),
                projection_active=sum(c.get('projected_sets',0) for c in cov)>=1,
                king=candidate['king_loss']<=min(c['king_loss'] for c in controls),
                queen=candidate['queen_loss_ge4']<=min(c['queen_loss_ge4'] for c in controls),
                material=candidate['exchange_loss_ge2']<=max(c['exchange_loss_ge2'] for c in controls)+1,
                meaningful_choices=changes>=3 and changes>=noise+2,coverage=share>=.75,cost=median_time<=.25,
                node_budget=candidate['median_nodes']>=.6*summary['original']['median_nodes'],
                memory=candidate['maximum_peak_rss_kb']<3500000)
    result=dict(decisions=len(labelled),frames_verified=sum(len(s) for s,t in cache.values()),arms=summary,
                changes_vs_off=changes,off_changes_vs_original=noise,coverage_case_share=share,coverage_reports=len(cov),
                median_model_seconds=median_time,checks=checks,decision='manual_review_before_full_games' if all(checks.values()) else 'stop_this_configuration',
                scope=plan['scope'],limitations='Wall-clock controls can differ. Short exchange label excludes quiet forcing continuations. Endpoint decisions are selected; not a population or strength estimate.')
    dump(OUT/'labelled.json',labelled);dump(OUT/'summary.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run','summarize']);globals()[p.parse_args().command]()
