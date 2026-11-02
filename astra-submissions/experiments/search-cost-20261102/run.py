from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,signal,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/search-cost-20261102'
OLD=ROOT/'astra-submissions/analysis/move-cost-profile-20261102'
RESOURCE=HERE.parent/'queen-terminal-backport-20261102/build-r2/base'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def env():return {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
def binaries():return {'base':HERE.parent/'sparse-cfr-20261102/build/base/mist','fast':HERE.parent/'sparse-cfr-20261102/build/fast/mist',
                      'base-profile':HERE/'build/base/mist','fast-profile':HERE/'build/fast/mist'}
def parse(stderr):return [json.loads(s[len('astra-search-cost '):]) for s in stderr.splitlines() if s.startswith('astra-search-cost ')]
def check_profile(p):
    assert p['async']==0 and p['wall']>0 and 0<=p['cpu']<=p['wall']+.01
    for k in ('wall','cpu'):
        assert abs(sum(b[k] for b in p['buckets'].values())-p[k])<2e-7,(k,p)
        assert all(b[k]>=-2e-7 for b in p['buckets'].values())
def preflight():
    os.sched_setaffinity(0,{0,1})
    sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
    from fresh_taxonomy_gate import protocol
    old=json.loads((OLD/'plan.json').read_text());rp=json.loads((ROOT/'data/raw/games'/old['cases'][0]['game']/'replay.json').read_text())
    records=[]
    for side in (0,1):
        feed,forced=protocol(rp,side,side);assert not forced
        ref=None
        for name,binary in binaries().items():
            e=env();e.update(MIST_MAX_SECONDS='0',FOW_SEED='2551102')
            r=subprocess.run([str(binary)],input=feed,capture_output=True,text=True,env=e,timeout=30)
            row=dict(side=side,arm=name,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,binary_sha256=sha(binary));records.append(row)
            assert r.returncode==0,r.stderr
            final=next(s for s in r.stderr.splitlines() if s.startswith('mist: n='))
            stats=dict(re.findall(r'(nodes|iters|p|v|move)=([^ ]+)',final))
            value=(r.stdout,stats)
            if ref is None:ref=value
            else:assert value==ref,(side,name,value,ref)
            profiles=parse(r.stderr)
            if name.endswith('-profile'):assert len(profiles)==1;check_profile(profiles[0])
            else:assert not profiles
    write(OUT/'preflight.json',dict(passed=True,records=records));print(json.dumps(dict(passed=True,cases=len(records))))
def prepare():
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    old=json.loads((OLD/'plan.json').read_text());cases=old['cases'];assert len(cases)==8
    pins=json.loads((OUT/'build.json').read_text())['pins']
    sources=[*HERE.glob('*.py'),*HERE.glob('*.[ch]'),HERE/'README.md',OUT/'preflight.json',OUT/'build.json',RESOURCE/'bin/stockfish',RESOURCE/'data/history.bin',*binaries().values()]
    sources += [OLD/(c['name']+'.input.txt') for c in cases]
    sources += [ROOT/'data/raw/games'/c['game']/'replay.json' for c in cases]
    for p in sources:pins[str(p)]=sha(p)
    for p,h in pins.items():assert sha(ROOT/p)==h,p
    write(OUT/'plan.json',dict(at=now(),cases=cases,binaries={k:str(v) for k,v in binaries().items()},pins=pins,
                              arm_order=['base','base-profile','fast','fast-profile'],order='rotate by case index modulo four',
                              seed=2551102,cores=[0,1],search_seconds=2.5,total_seconds=1200,case_seconds=120,
                              stockfish=str(RESOURCE/'bin/stockfish'),history=str(RESOURCE/'data/history.bin'),
                              scope='Cost profile on reused cases; not strength, no candidate promotion. Synchronous round mode.'))
    print(json.dumps(dict(prepared=True,processes=32,plan_sha256=sha(OUT/'plan.json'))))
def collect():
    plan=json.loads((OUT/'plan.json').read_text());os.sched_setaffinity(0,set(plan['cores']))
    for p,h in plan['pins'].items():assert sha(ROOT/p)==h,p
    begin=time.monotonic();receipt=dict(state='running',at=now(),plan_sha256=sha(OUT/'plan.json'),jobs=[]);write(OUT/'receipt.json',receipt)
    try:
        for i,c in enumerate(plan['cases']):
            names=plan['arm_order'];order=names[i%4:]+names[:i%4]
            for name in order:
                left=plan['total_seconds']-(time.monotonic()-begin);assert left>0
                e=env();e.update(MIST_MAX_SECONDS=str(plan['search_seconds']),MIST_FORCE_MOVES=','.join(c['forced']),
                                MIST_STOCKFISH=plan['stockfish'],MIST_HISTORY_TABLE=plan['history'],FOW_SEED=str(plan['seed']),MIST_THREADS='2')
                feed=OLD/(c['name']+'.input.txt');assert sha(feed)==c['input_sha256']
                start=time.monotonic();p=subprocess.Popen([plan['binaries'][name]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=e,start_new_session=True)
                error=None
                try:stdout,stderr=p.communicate(feed.read_text(),timeout=min(left,plan['case_seconds']))
                except BaseException as exc:
                    error=repr(exc);os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
                r=dict(case=c['name'],arm=name,elapsed=time.monotonic()-start,exit_code=p.returncode,error=error,stdout=stdout,stderr=stderr)
                write(OUT/(c['name']+'-'+name+'.json'),r);receipt['jobs'].append({k:r[k] for k in ('case','arm','elapsed','exit_code','error')})
                assert not error and p.returncode==0,r
                moves=[s[5:] for s in stdout.splitlines() if s.startswith('move ')]
                assert moves[:-1]==c['forced'] and len(moves)==len(c['forced'])+1
                assert 'mist: stockfish ready' in stderr
                profiles=parse(stderr)
                if name.endswith('-profile'):assert len(profiles)==1;check_profile(profiles[0])
                else:assert not profiles
                print(json.dumps(dict(done=len(receipt['jobs']),case=c['name'],arm=name,profile=profiles[0] if profiles else None)),flush=True)
        receipt['state']='completed'
    except BaseException as exc:receipt.update(state='failed',error=repr(exc));raise
    finally:
        receipt.update(ended_at=now(),seconds=time.monotonic()-begin);(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':globals()[sys.argv[1]]()
