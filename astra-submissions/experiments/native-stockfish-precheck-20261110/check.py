"""Real package smoke tests for the local readiness check. No strength score."""
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/native-stockfish-precheck-20261110'
SHIP=HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
REF=HERE.parent/'last-only-pilot-20261110/build/referee.py'
sys.path.insert(0,str(ROOT/'astra-submissions/tools'))
from native_stockfish_readiness import run_with_native_stockfish
from local_turn_control import cleanup_registry,group_members

def sha(path):
    with Path(path).open('rb') as file:return hashlib.file_digest(file,'sha256').hexdigest()

def now():return datetime.now(timezone.utc).isoformat()

def save(path,value):
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def freeze():
    OUT.mkdir(parents=True,exist_ok=False)
    deps=[Path(__file__),REF,SHIP/'mist',SHIP/'run.sh',SHIP/'bin/stockfish',SHIP/'data/history.bin',
          ROOT/'astra-submissions/tools/native_stockfish_readiness.py',ROOT/'astra-submissions/tools/local_turn_control.py',
          OUT.parent/'sf-startup-diagnosis-20261110/result.json',OUT.parent/'prospective-quiet-teacher-20261110/plan.json']
    plan=dict(at=now(),cores=[4,5],base=3,increment=0,ply_cap=1,wall_cap_seconds=95,
        cases=['healthy','white-fallback','black-fallback','black-absent'],
        private_store=str(ROOT/'data/astra-spool/native-stockfish-precheck-20261110'),
        dependencies={str(p):sha(p) for p in deps})
    save(OUT/'plan.json',plan);print(json.dumps(dict(pins=len(deps),plan=sha(OUT/'plan.json'))))

def lease(take,cores):
    path=ROOT/'chatroom/cores.json';owner='astra-native-stockfish-precheck-20261110'
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);state=json.loads(path.read_text())
        if take:
            assert all(not set(cores)&set(r['cores']) for r in state['allocation'])
            state['allocation'].append(dict(owner=owner,cores=cores,pid=os.getpid(),at=now(),purpose='four bounded startup-readiness smoke cases'))
        else:state['allocation']=[r for r in state['allocation'] if r.get('owner')!=owner]
        state['updated']=now();save(path,state)

def run():
    plan=json.loads((OUT/'plan.json').read_text())
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    root=Path(plan['private_store']);root.mkdir(parents=True,exist_ok=False)
    broken={}
    for kind in ('fallback','absent'):
        dest=root/kind;dest.mkdir();(dest/'bin').mkdir()
        for name in ('run.sh','mist'):shutil.copy2(SHIP/name,dest/name)
        (dest/'data').symlink_to(SHIP/'data',target_is_directory=True)
        if kind=='fallback':
            engine=dest/'bin/stockfish';engine.write_text('#!/bin/sh\nexit 127\n');engine.chmod(0o755)
        broken[kind]=dest
    spec=importlib.util.spec_from_file_location('readiness_referee',REF)
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref);original=ref.Bot
    for key in list(os.environ):
        if key.startswith(('MIST_','ASTRA_','FOW_')):del os.environ[key]
    os.environ['FOW_SEED']='3341110'
    os.sched_setaffinity(0,set(plan['cores']));lease(True,plan['cores']);rows=[]
    start=time.monotonic();unclean=[]
    def deadline(*_): raise TimeoutError('readiness smoke wall bound')
    signal.signal(signal.SIGALRM,deadline)
    signal.alarm(plan['wall_cap_seconds'])
    try:
        for case in plan['cases']:
            assert time.monotonic()-start<plan['wall_cap_seconds']
            case_path=root/case;case_path.mkdir();registry=case_path/'processes.json'
            sides=case.split('-');failed=sides[0] if len(sides)>1 else None;kind=sides[-1]
            commands=[['/bin/bash',str((broken[kind] if s==failed else SHIP)/'run.sh')] for s in ('white','black')]
            try:
                game=run_with_native_stockfish(ref,*commands,base=plan['base'],increment=plan['increment'],
                    max_plies=plan['ply_cap'],match_id=case,registry_path=registry,retain_stderr=True)
                save(case_path/'game.json',game)
            finally:
                if not registry.exists():unclean.append(case)
                else:
                    unclean.extend(cleanup_registry(registry))
                    for group in json.loads(registry.read_text()):
                        if any(r['state'] not in ('Z','X') for r in group_members(group['leader']['pgid'])):unclean.append(group['leader']['pgid'])
            assert ref.Bot is original and not unclean
            checks=game['localNativeStockfishReadiness'];frames=game['frames']
            assert frames[0]==ref.make_frame(ref.FowBoard(),[3.,3.])
            assert not game.get('failedSide') and not game['warnings']
            if not failed:
                assert [r['status'] for r in checks]==['ready','ready'] and len(frames)==2
                assert ref.chess.Move.from_uci(frames[1]['move']) in ref.fow_moves(ref.FowBoard())
                assert game['reason']=='Move limit reached'
            else:
                expected='fallback' if kind=='fallback' else 'missing_ready'
                assert (checks[-1]['side'],checks[-1]['status'])==(failed,expected)
                assert [r['status'] for r in checks[:-1]]==(['ready'] if failed=='black' else [])
                assert len(frames)==1 and game['result']=='*'
                assert game['reason']==f'Infrastructure startup failure: Local benchmark requires native Stockfish: {failed} {expected}'
                assert not any(e['text'].startswith('move ') for e in game['protocol']['events'])
                assert frames[-1]['clocks']==[3.,3.]
            rows.append(dict(case=case,checks=checks,plies=len(frames)-1,result=game['result'],reason=game['reason'],source_sha256=sha(case_path/'game.json')))
    finally:
        signal.alarm(0)
        if not unclean:lease(False,plan['cores'])
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    result=dict(at=now(),passed=True,cases=rows,seconds=time.monotonic()-start,
        cleanup_verified=not unclean,plan_sha256=sha(OUT/'plan.json'),
        scope='Pre-move benchmark rejection only; exact v38 bytes unchanged. No real-clock playing score, startup retry, live repair, or arena action.')
    save(OUT/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('freeze','run'));args=parser.parse_args()
    (freeze if args.action=='freeze' else run)()
