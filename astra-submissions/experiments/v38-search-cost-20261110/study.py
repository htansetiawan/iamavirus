"""Attribute deployed v38 search cost; no candidate or strength gate."""
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/v38-search-cost-20261110'
LEGACY=HERE.parent/'search-cost-20261102'
sys.path[:0]=[str(ROOT),str(LEGACY),str(ROOT.parent/'fow-starter')]
import run as old
from review import body
from learning.api_client import ApiClient
import referee as ref


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def pins(plan):
    for p,h in plan['dependencies'].items():assert sha(p)==h,p


class SourceClient(ApiClient):
    def __init__(self,budget):
        super().__init__(min_interval=1.2,timeout=20);self.budget=budget
    def _pace(self):
        assert self.requests_made<self.budget,'source request cap, including retries'
        while True:
            status=json.loads((ROOT/'astra-submissions/analysis/prospective-full-prior-20261110b/execution.json').read_text())
            if status['status']!='running':break
            left=datetime.fromisoformat(status['updated_at']).timestamp()+1200-time.time()
            if left>120:break
            time.sleep(10)
        super()._pace()


def prepare():
    OUT.mkdir(exist_ok=False)
    previous=json.loads((ROOT/'astra-submissions/analysis/search-cost-20261102/plan.json').read_text())
    ship=HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
    original=HERE.parent/'sparse-cfr-20261102/build/base'
    assert all((original/'src'/p.name).read_bytes()==p.read_bytes() for p in (ship/'src').iterdir() if p.is_file())
    assert sha(ship/'mist')==sha(original/'mist')=='14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    dest=HERE/'build';shutil.copytree(LEGACY/'build/base/src',dest/'src')
    shutil.copyfile(LEGACY/'build/base/build.sh',dest/'build.sh')
    main=dest/'src/main.c';s=main.read_text();needle='        clock_left = reported - (now_seconds() - view_at) + increment;'
    head,sep,tail=s.rpartition(needle);assert sep and s.count(needle)==2
    main.write_text(head+'        fprintf(stderr, "astra-turn-wall %.9f\\n", now_seconds() - view_at);\n'+sep+tail)
    assert head+sep+tail==(ship/'src/main.c').read_text()
    preserved=0
    for name,names in {'cfr.c':['pcfr_iteration','pcfr_current','game_grow'],
        'gtcfr.c':['build_children_scored','pick_once','gtcfr_decide'],
        'sfeval.c':['sf_children','sf_submit','sf_collect','sf_poll']}.items():
        for func in names:
            assert body((ship/'src'/name).read_text(),func)==body((dest/'src'/name).read_text(),func+'_profile_impl')
            preserved+=1
    built=subprocess.run(['bash','build.sh'],cwd=dest,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    write(OUT/'build.json',dict(at=now(),exit_code=built.returncode,stdout=built.stdout,stderr=built.stderr,
          preserved_original_function_bodies=preserved,observer_only_main_line=True,
          original_source_identical_to_v38=True,baseline_sha256=sha(ship/'mist'),profile_sha256=sha(dest/'mist')))
    cases=previous['cases'];assert len(cases)==8
    feeds=ROOT/'astra-submissions/analysis/move-cost-profile-20261102'
    for c in cases:assert sha(feeds/(c['name']+'.input.txt'))==c['input_sha256']
    dependencies=[HERE/'study.py',LEGACY/'run.py',LEGACY/'review.py',LEGACY/'profile.c',LEGACY/'profile.h',
          ROOT/'learning/api_client.py',ROOT.parent/'fow-starter/referee.py',OUT/'build.json',
          ROOT/'astra-submissions/analysis/search-cost-20261102/plan.json',
          ROOT/'astra-submissions/analysis/search-cost-20261102/review.json',
          ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip',ship/'mist',ship/'bin/stockfish',ship/'data/history.bin',
          *sorted((ship/'src').glob('*')),*sorted((dest/'src').glob('*')),dest/'build.sh',dest/'mist']
    dependencies += [feeds/(c['name']+'.input.txt') for c in cases]
    plan=dict(at=now(),cases=cases,feeds=str(feeds),ship=str(ship),
        binaries={'control':str(ship/'mist'),'profile':str(dest/'mist')},cores=[2,3],seed=2551102,
        max_seconds=10,per_process_seconds=120,total_seconds=1200,source_requests=24,
        archive=str(ROOT/'data/astra-spool/v38-search-cost-20261110'),archive_bytes=8*1024*1024,
        ordering='Control/profile alternate first by case index; all16 first attempts, no dropped cases/retries.',
        actor='Exactly old255 own-observation, own-clock and forced-own-move feeds. Public replay truth only validates source and final legality. '
              'No opponent actions/views/clocks, full board, future307 sources or model scores in the actor input. '
              'Historical elapsed think time/RNG/native belief are not reconstructed; wall-cost thinning can change between independent processes.',
        source='Eight fixed old game IDs; reuse readable shared cache first. Shared store loss permits bounded private completed-replay GET fallback. '
               'New API metadata bytes need not match the cold old raw JSON; replay frames must reconstruct the exact frozen actor feed/own moves and course rules. '
               'At most24 sequential requests with>=1.2s spacing, no shared writes or persistent watcher.',
        mechanism='Reuse255 audited exclusive timer wrappers with the actual immutable v38 Stockfish binary and ASTRA_SF_ALLCHILDREN=1. '
                  'Native v38 default max10-second cap and recorded clock budgets, synchronous default; no solver optimization arm. '
                  'One observer-only final main diagnostic measures the current target-view-to-move wall interval; native update/guard logs recorded separately.',
        scope='Cost attribution on eight old belief-size-selected replay decisions, not a causal comparison to historical255 timings, on-policy arena profile or strength estimate. '
              'Main-thread CPU excludes Stockfish worker CPU; call wall-minus-CPU includes waiting/scheduling and is not pipe overhead. '
              'Profile/control differences include instrumentation and adaptive-thinning/RNG effects. No fit, GPU, runtime candidate, game, ZIP, version or arena mutation.',
        nearest_prior='254 exactsolver1.252x kernel passed but1.021x equal-clock nodes failed; remains closed. '
                      '255 profile used originalv37 scorer,82.2%call wall.279 measured v38 updater sorting only. '
                      'This changes the measured scorer/default clock regime and adds target-turn timing, not a new optimization or reopening of254.',
        next='Publish audited current cost shares and fixed-work Amdahl bounds only. No automatic solver retest, parameter sweep, match or runtime choice; finish307 first.',
        dependencies={str(p):sha(p) for p in sorted(set(dependencies))})
    write(OUT/'plan.json',plan);print(json.dumps(dict(prepared=True,pins=len(plan['dependencies']),preserved=preserved,plan_sha256=sha(OUT/'plan.json'))),flush=True)


def sources(plan):
    archive=Path(plan['archive']);archive.mkdir(exist_ok=False)
    client=SourceClient(plan['source_requests']);sources=[];size=0;frames=0
    for c in plan['cases']:
        assert client.requests_made<plan['source_requests']
        shared=ROOT/'data/raw/games'/c['game']/'replay.json'
        raw=None;error=None
        try:
            if shared.is_file():raw=shared.read_bytes()
            healthy=(ROOT/'data/raw').is_dir()
        except OSError as exc:healthy=False;error=repr(exc)
        if raw is None:
            assert not healthy,'own cache miss: defer to watcher, close bounded study'
            raw,fetch=client.get_bytes('/api/games/'+c['game'])
            origin=dict(source='public API; shared store unavailable',fetch=fetch.__dict__,cache_error=error)
        else:origin=dict(source='existing shared cache',path=str(shared))
        size+=len(raw);assert len(raw)<=4*1024*1024 and size<=plan['archive_bytes']
        target=archive/(c['game']+'.json');target.write_bytes(raw);replay=json.loads(raw)
        assert replay['id']==c['game'] and replay.get('rulesVersion')=='fow-v1'
        validate_source(c,replay,plan)
        frames+=c['ply']+1;sources.append(dict(game=c['game'],path=str(target),sha256=sha(target),origin=origin))
    write(OUT/'sources.json',dict(at=now(),sources=sources,bytes=size,requests=client.requests_made,course_frames=frames))


def validate_source(c,replay,plan):
    b=ref.FowBoard();key=('white','black')[c['side']];tc=replay.get('timeControl',{})
    expected=['fow',f"{'w' if c['side']==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"];forced=[]
    for ply,f in enumerate(replay['frames'][:c['ply']+1]):
        assert f['ply']==ply
        if ply:
            a=ref.chess.Move.from_uci(f['move']);assert a in ref.fow_moves(b);b.push(a)
        frame=ref.make_frame(b,f['clocks'])
        assert all(frame[k]==f[k] for k in ('board','white','black'))
        expected.append(f[key])
        if ply%2==c['side']:
            expected.append(str(f['clocks'][c['side']]))
            if ply<c['ply']:forced.append(replay['frames'][ply+1]['move'])
    feed=Path(plan['feeds'])/(c['name']+'.input.txt');assert sha(feed)==c['input_sha256']
    actual=feed.read_text().splitlines();assert len(actual)==len(expected) and forced==c['forced']
    for a,z in zip(actual,expected):
        if a!=z:assert float(a)==float(z),(c['name'],a,z)
    return b


def environment(plan,forced=(),zero=False):
    e=old.env();ship=Path(plan['ship'])
    e.update(ASTRA_SF_ALLCHILDREN='1',MIST_STOCKFISH=str(ship/'bin/stockfish'),
        MIST_HISTORY_TABLE=str(ship/'data/history.bin'),MIST_MAX_SECONDS='0' if zero else str(plan['max_seconds']),
        MIST_THREADS='2',MIST_TIMING='1',FOW_SEED=str(plan['seed']))
    if forced:e['MIST_FORCE_MOVES']=','.join(forced)
    return e


def process(binary,feed,e,bound):
    begin=time.monotonic();p=subprocess.Popen([binary],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,env=e,start_new_session=True);error=None
    try:stdout,stderr=p.communicate(feed,timeout=bound)
    except BaseException as exc:
        error=repr(exc);os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
    return dict(exit_code=p.returncode,error=error,seconds=time.monotonic()-begin,stdout=stdout,stderr=stderr)


def collect():
    plan=json.loads((OUT/'plan.json').read_text());pins(plan);os.sched_setaffinity(0,set(plan['cores']))
    assert not (OUT/'execution.json').exists(),'one attempt'
    receipt=dict(at=now(),status='running',jobs=[],plan_sha256=sha(OUT/'plan.json'));write(OUT/'execution.json',receipt)
    begin=time.monotonic()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('global study wall bound')))
    signal.alarm(plan['total_seconds'])
    try:
        sources(plan)
        replay=json.loads((Path(plan['archive'])/(plan['cases'][0]['game']+'.json')).read_text());preflight=[]
        for side in (0,1):
            key=('white','black')[side];tc=replay.get('timeControl',{})
            feed=['fow',f"{'w' if side==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"]
            for ply in range(side+1):
                feed.append(replay['frames'][ply][key])
                if ply%2==side:feed.append(str(replay['frames'][ply]['clocks'][side]))
            values=[]
            for arm,binary in plan['binaries'].items():
                r=process(binary,'\n'.join(feed)+'\n',environment(plan,zero=True),30)
                preflight.append(dict(side=side,arm=arm,**r));assert r['exit_code']==0 and not r['error']
                final=next(s for s in r['stderr'].splitlines() if s.startswith('mist: n='))
                values.append((r['stdout'],dict(re.findall(r'(nodes|iters|p|v|move)=([^ ]+)',final))))
            assert values[0]==values[1],(side,values)
        write(OUT/'preflight.json',dict(passed=True,rows=preflight))
        for index,c in enumerate(plan['cases']):
            arms=['control','profile'] if index%2==0 else ['profile','control']
            for arm in arms:
                left=plan['total_seconds']-(time.monotonic()-begin);assert left>0
                feed=(Path(plan['feeds'])/(c['name']+'.input.txt')).read_text()
                r=process(plan['binaries'][arm],feed,environment(plan,c['forced']),min(left,plan['per_process_seconds']))
                write(OUT/(c['name']+'-'+arm+'.json'),r)
                receipt['jobs'].append(dict(case=c['name'],arm=arm,exit_code=r['exit_code'],seconds=r['seconds'],error=r['error']))
                assert r['exit_code']==0 and r['error'] is None,(c['name'],arm,r)
                moves=[s[5:] for s in r['stdout'].splitlines() if s.startswith('move ')]
                assert moves[:-1]==c['forced'] and len(moves)==len(c['forced'])+1
                assert 'mist: stockfish ready' in r['stderr']
                profiles=old.parse(r['stderr'])
                if arm=='profile':assert len(profiles)==1;old.check_profile(profiles[0])
                else:assert not profiles
                print(json.dumps(receipt['jobs'][-1]),flush=True)
        receipt['status']='complete'
    except BaseException as exc:receipt.update(status='failed',error=repr(exc));raise
    finally:
        signal.alarm(0)
        receipt.update(ended_at=now(),seconds=time.monotonic()-begin)
        (OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')


def review():
    plan=json.loads((OUT/'plan.json').read_text());pins(plan)
    receipt=json.loads((OUT/'execution.json').read_text());assert receipt['status']=='complete' and len(receipt['jobs'])==16
    source={s['game']:s for s in json.loads((OUT/'sources.json').read_text())['sources']}
    rows=[]
    for c in plan['cases']:
        src=source[c['game']];assert sha(src['path'])==src['sha256']
        board=validate_source(c,json.loads(Path(src['path']).read_text()),plan);legal={a.uci() for a in ref.fow_moves(board)}
        for arm in ('control','profile'):
            r=json.loads((OUT/(c['name']+'-'+arm+'.json')).read_text());assert r['exit_code']==0 and r['error'] is None
            chosen=[s[5:] for s in r['stdout'].splitlines() if s.startswith('move ')][-1];assert chosen in legal
            final=next(s for s in r['stderr'].splitlines() if s.startswith('mist: n='))
            nodes=int(re.search(r'nodes=(\d+)',final)[1]);iters=int(re.search(r'iters=(\d+)',final)[1]);belief=int(re.search(r'\|P\|=(\d+)',final)[1])
            p=old.parse(r['stderr']);turn=None
            if arm=='profile':
                assert len(p)==1;old.check_profile(p[0]);assert p[0]['nodes']==nodes and p[0]['iterations']==iters
                turns=[float(s.split()[1]) for s in r['stderr'].splitlines() if s.startswith('astra-turn-wall ')]
                assert len(turns)==1;turn=turns[0];assert turn>=p[0]['wall']>0
            rows.append(dict(case=c['name'],arm=arm,move=chosen,nodes=nodes,iters=iters,belief=belief,profile=p[0] if p else None,target_turn_wall=turn))
    profiles=[r for r in rows if r['arm']=='profile'];wall=sum(r['profile']['wall'] for r in profiles)
    categories={k:dict(wall=sum(r['profile']['buckets'][k]['wall'] for r in profiles),
                      cpu=sum(r['profile']['buckets'][k]['cpu'] for r in profiles),
                      calls=sum(r['profile']['buckets'][k]['calls'] for r in profiles)) for k in profiles[0]['profile']['buckets']}
    for v in categories.values():v['wall_share']=v['wall']/wall
    f=categories['solver']['wall_share']+categories['strategy']['wall_share'];sf=categories['stockfish']['wall_share']
    ratios=[];belief_differences=0
    for c in plan['cases']:
        a,b=[next(r for r in rows if r['case']==c['name'] and r['arm']==arm) for arm in ('control','profile')]
        ratios.append(b['nodes']/a['nodes']);belief_differences+=a['belief']!=b['belief']
    result=dict(at=now(),rows=rows,search_wall=wall,main_thread_cpu=sum(r['profile']['cpu'] for r in profiles),
        target_turn_wall=sum(r['target_turn_wall'] for r in profiles),buckets=categories,
        instrumentation=dict(median_profiled_node_ratio=statistics.median(ratios),ratios=ratios,changed_belief_counts=belief_differences),
        fixed_work_serial_bounds=dict(eliminate_solver_and_strategy=1/(1-f),halve_stockfish_call_wall=1/(1-.5*sf)),
        actor_inputs=8,legal_choices=16,course_frames=sum(c['ply']+1 for c in plan['cases']),
        preserved_function_bodies=json.loads((OUT/'build.json').read_text())['preserved_original_function_bodies'],
        decision='Cost attribution only. No candidate, strength claim, reopened254gate or automatic benchmark.',
        scope=plan['scope'],plan_sha256=sha(OUT/'plan.json'),receipt_sha256=sha(OUT/'execution.json'))
    write(OUT/'review.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('rows','scope')},indent=2),flush=True)


if __name__=='__main__':globals()[sys.argv[1]]()
