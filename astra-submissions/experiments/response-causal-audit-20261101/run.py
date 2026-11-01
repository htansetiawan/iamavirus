#!/usr/bin/env python3
"""Nine post-decision traces; no policy selection or training from this panel."""
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/response-causal-audit-20261101'
BASE=HERE.parent/'stable-mix-20261101/build/base'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
GAMES=ROOT/'astra-submissions/analysis/learned-response-search-20261101/full-games/jobs'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol
from learning import ingest
from learning.compare_archives import kill_tree
ARMS=['unrestricted','raw','projected']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def freeze():
    tests=json.loads((OUT/'correctness.json').read_text());assert len(tests['tests'])==2 and all(r['returncode']==0 for r in tests['tests'])
    cases=[]
    for job,ply,side,seed in [('h2h-p0-white',20,0,209200),('h2h-p0-black',31,1,209200),('h2h-p1-black',17,1,209202)]:
        path=GAMES/job/'replay.json';rp=json.loads(path.read_text());states,errors=ingest.validate_replay(rp);assert not errors
        feed,forced=protocol(rp,ply,side);redacted=json.loads(path.read_text());other=('black','white')[side]
        for i,frame in enumerate(redacted['frames']):
            frame['board']='X'*64;frame[other]='X'*64
            if i==0 or (i-1)%2!=side or i>ply:frame['move']='REDACTED'
        assert protocol(redacted,ply,side)==(feed,forced)
        name=job+'-p'+str(ply);input_path=OUT/(name+'.input.txt');input_path.write_text(feed)
        cases.append(dict(name=name,job=job,ply=ply,side=side,seed=seed,path=str(path),replay_sha256=sha(path),forced=forced,input_sha256=sha(input_path)))
    pins={str(p):sha(p) for p in [HERE/'build/mist',HERE/'provenance.json',HERE/'trace.h',HERE/'test.py',HERE/'test_trace.c',Path(__file__),OUT/'correctness.json',BASE/'bin/stockfish',BASE/'data/history.bin',MODEL]}
    plan=dict(at_utc=datetime.now(timezone.utc).isoformat(),cases=cases,pins=pins,arms=ARMS,cores='4,5',seconds_cap=10,timeout=120,
              selection='First balanced-material bishop exposure, another early bishop event, and a possible ordinary-exchange control from the rejected209 match pilot; post-match selected diagnostics, no population claim.',
              scope='Log full inferred belief and root/two-ply sampled continuations after choosing. No true board input, no policy or model change, no extra solver iterations.',
              limitations='Forced prefixes omit previous searches/Stockfish cache warmup. Tiny initial-value copy and extra code can affect wall timing. Not an exact replay of historical search or a strength test.',
              stop='Any invalid output, assertion failure, label mismatch or changed pinned input stops diagnostics; no automatic reruns.')
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
    print(json.dumps({'cases':len(cases),'calls':len(cases)*3}))

def run():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['pins'].items():assert sha(Path(p))==h,p
    status=dict(status='running',pid=os.getpid(),completed=0,started_at=datetime.now(timezone.utc).isoformat())
    with (OUT/'execution.json').open('x') as f:json.dump(status,f)
    try:
        with (OUT/'receipts.jsonl').open('x') as sink:
            for i,case in enumerate(plan['cases']):
                path=OUT/(case['name']+'.input.txt');assert sha(path)==case['input_sha256'];feed=path.read_text()
                for arm in ARMS[i%3:]+ARMS[:i%3]:
                    name=case['name']+'-'+arm;env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
                    env.update(MIST_FORCE_MOVES=','.join(case['forced']),MIST_MAX_SECONDS=str(plan['seconds_cap']),FOW_SEED=str(case['seed']),
                               MIST_STOCKFISH=str(BASE/'bin/stockfish'),MIST_HISTORY_TABLE=str(BASE/'data/history.bin'),
                               ASTRA_VISIBLE_MODEL=str(MODEL),ASTRA_VISIBLE_CONFIDENCE='0' if arm=='unrestricted' else '.25',
                               ASTRA_VISIBLE_PROJECT='1' if arm=='projected' else '0',ASTRA_RESPONSE_TRACE=str(OUT/(name+'.trace.json')),OMP_NUM_THREADS='1')
                    start=time.monotonic();error=None
                    proc=subprocess.Popen(['taskset','-c',plan['cores'],str(HERE/'build/mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
                    try:stdout,stderr=proc.communicate(feed,timeout=plan['timeout'])
                    except subprocess.TimeoutExpired:kill_tree(proc.pid);stdout,stderr=proc.communicate();error='timeout'
                    for ext,value in [('stdout',stdout),('stderr',stderr)]:
                        with (OUT/(name+'.'+ext)).open('x') as f:f.write(value)
                    moves=[l[5:] for l in stdout.splitlines() if l.startswith('move ')]
                    valid=proc.returncode==0 and bool(stdout.splitlines()) and stdout.splitlines()[0]=='ready' and moves[:-1]==case['forced'] and len(moves)==len(case['forced'])+1
                    record=dict(name=case['name'],arm=arm,returncode=proc.returncode,error=error,protocol_valid=valid,move=moves[-1] if valid else None,elapsed=time.monotonic()-start,
                                stdout_sha256=sha(OUT/(name+'.stdout')),stderr_sha256=sha(OUT/(name+'.stderr')))
                    trace=OUT/(name+'.trace.json')
                    if trace.exists():record['trace_sha256']=sha(trace)
                    sink.write(json.dumps(record)+'\n');sink.flush();status['completed']+=1;dump(OUT/'execution.json',status)
                    assert valid and not error and trace.exists(),record
                    assert not re.search(r'(?:failures|mismatches|load_failed) [1-9]',stderr),stderr
                    assert json.loads(trace.read_text())['chosen']==record['move']
                    print(status['completed'],9,name,record['move'],round(record['elapsed'],2),flush=True)
        status['status']='complete'
    except BaseException:status['status']='failed';raise
    finally:status['ended_at']=datetime.now(timezone.utc).isoformat();dump(OUT/'execution.json',status)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run']);globals()[p.parse_args().command]()
