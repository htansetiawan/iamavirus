"""Trace and independently review one early v38 inference update for teaching."""
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
NAME='presentation-belief-weights-20261111'
BUILD=ROOT/'astra-submissions/experiments'/NAME
OUT=ROOT/'astra-submissions/analysis'/NAME
PRIVATE=ROOT/'data/astra-spool'/NAME
SOURCE=ROOT/'astra-submissions/experiments/presentation-real-decision-20261111/control/src'
HISTORY=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren/data/history.bin'
REPLAY=ROOT/'data/astra-spool/v38-mist-wins-20261111/c8ozqj0m.json'

def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def save(p,d):
    with p.open('x') as s:s.write(json.dumps(d,indent=2,allow_nan=False)+'\n')
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]

def stage():
    OUT.mkdir(exist_ok=False);PRIVATE.mkdir(exist_ok=False)
    previous=read(ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/plan.json')
    paths=[SOURCE/n for n in ('board.c','belief.c','belief.h','fow.h','movemodel.c','movemodel.h')]
    for p in paths:assert sha(p)==previous['source_members']['src/'+p.name]
    assert sha(HISTORY)==previous['dependencies'][str(HISTORY)]
    assert sha(REPLAY)==previous['dependencies'][str(REPLAY)]
    frames=read(REPLAY)['frames'];(PRIVATE/'views.txt').write_text(frames[1]['white']+'\n'+frames[2]['white']+'\n')
    command=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-I'+str(SOURCE),str(BUILD/'probe.c'),str(SOURCE/'board.c'),str(SOURCE/'movemodel.c'),'-lm','-o',str(BUILD/'probe')]
    done=subprocess.run(command,capture_output=True,text=True,timeout=90)
    save(OUT/'build.json',dict(command=command,code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    paths += [Path(__file__),BUILD/'probe.c',BUILD/'probe',HISTORY,REPLAY,PRIVATE/'views.txt',ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/plan.json']
    plan=dict(at=datetime.now(timezone.utc).isoformat(),call_limit=1,timeout=60,core=6,output_byte_cap=1024**2,
              selection='The intermediate 14-world stage of the existing 375 teaching prefix, before Bf4. Keep the existing third-decision result unchanged.',
              dependencies={str(p):sha(p) for p in paths},
              information_boundary='The C updater receives only the recorded White views after own d4 and after the first opponent move. No actual opponent move or truth input.',
              scope='Fixed-parameter inference arithmetic demonstration. No search, Stockfish, game, fit, candidate, performance or calibration test, package, commit, push or deployment.')
    save(OUT/'plan.json',plan);print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),build_code=done.returncode)),flush=True)

def run():
    plan=read(OUT/'plan.json')
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))};env['MIST_HISTORY_TABLE']=str(HISTORY)
    done=subprocess.run([str(BUILD/'probe'),str(PRIVATE/'views.txt')],env=env,capture_output=True,text=True,timeout=plan['timeout'])
    for suffix,text in [('stdout',done.stdout),('stderr',done.stderr)]:
        with (PRIVATE/suffix).open('x') as s:s.write(text)
    save(OUT/'execution.json',dict(at=datetime.now(timezone.utc).isoformat(),code=done.returncode,plan_sha256=sha(OUT/'plan.json'),stdout_sha256=sha(PRIVATE/'stdout'),stderr_sha256=sha(PRIVATE/'stderr')))
    assert done.returncode==0 and len(done.stdout.encode())+len(done.stderr.encode())<=plan['output_byte_cap']
    print(json.dumps(dict(code=done.returncode,lines=len(done.stdout.splitlines()))),flush=True)

def review():
    plan=read(OUT/'plan.json');execution=read(OUT/'execution.json')
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert execution['code']==0 and execution['plan_sha256']==sha(OUT/'plan.json')
    for name in ('stdout','stderr'):assert sha(PRIVATE/name)==execution[name+'_sha256']
    rows=[json.loads(s) for s in (PRIVATE/'stdout').read_text().splitlines()]
    parent=next(r for r in rows if r['kind']=='parent');actions=[r for r in rows if r['kind']=='action']
    retained=[r for r in rows if r['kind']=='retained'];samples=[r for r in rows if r['kind']=='sample']
    summary=next(r for r in rows if r['kind']=='summary')
    assert len(actions)==parent['actions']==20 and summary['worlds']==len(retained)==len(samples)==14 and not summary['capped']
    assert summary['lookups']==summary['hits']==1
    table=HISTORY.read_bytes();assert table[:8]==b'MISTHIST'
    version,n=struct.unpack_from('<II',table,8);assert version==1 and len(table)==16+16*n
    history=int(parent['history'],16);counts={}
    for key,move,count in struct.iter_unpack('<QII',table[16:]):
        if key==history:counts[move]=count
    assert sum(counts.values())==parent['history_total']
    text=(SOURCE/'movemodel.c').read_text();body=re.search(r'theta_full\[MM_FEATURES\] = \{([^}]+)\}',text).group(1)
    theta=[f32(float(x.strip().removesuffix('f'))) for x in body.split(',')];assert len(theta)==28
    def near(a,b,tolerance=2e-6):assert math.isclose(a,b,rel_tol=tolerance,abs_tol=tolerance),(a,b)
    for a in actions:
        assert a['count']==counts.get(a['encoded'],0) and len(a['features'])==28
        logit=0.0
        for w,x in zip(theta,a['features'],strict=True):logit=f32(logit+f32(w*f32(x)))
        near(logit,a['logit'],1e-7)
    top=max(a['logit'] for a in actions);z=sum(math.exp(a['logit']-top) for a in actions)
    for a in actions:
        model=math.exp(a['logit']-top)/z;near(model,a['model'])
        blend=(a['count']+parent['n0']*model)/(parent['history_total']+parent['n0']);near(blend,a['blend'])
    assert parent['history_total']>=parent['minimum']
    surviving=[a for a in actions if a['survives']];assert len(surviving)==14
    mass=sum(a['blend']**parent['temperature'] for a in surviving)
    boards={a['board']:a for a in surviving};assert len(boards)==14
    assert {r['board'] for r in retained}==set(boards)
    for row in retained:near(row['weight'],boards[row['board']]['blend']**parent['temperature']/mass)
    near(sum(r['weight'] for r in retained),1,1e-12)
    for row in samples:near(row['weight'],retained[row['index']]['weight'],1e-12)
    source_rows=read(REPLAY)['frames'];assert (PRIVATE/'views.txt').read_text().splitlines()==[source_rows[1]['white'],source_rows[2]['white']]
    # The complete independent course enumeration of these same views is already
    # frozen by 375. Verify its identity and all 14 move names here.
    old_plan=read(ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/plan.json')
    old=read(ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/result.json')
    assert old['plan_sha256']==sha(ROOT/'astra-submissions/analysis/presentation-real-decision-20261111/plan.json')
    assert old_plan['dependencies'][str(REPLAY)]==sha(REPLAY)
    assert sorted(a['move'] for a in surviving)==old['opponent_moves_consistent_with_received_views']['2']
    for a in actions:
        a['retained_weight']=next((r['weight'] for r in retained if r['board']==a['board']),0)
    truth=next(a for a in surviving if a['board']==source_rows[2]['board'])
    # Algebraic counterexample to exact untempering AFTER board-history merging.
    merged_tempered=[.25**2+.25**2,.5**2];untemper=[math.sqrt(x) for x in merged_tempered]
    untemper=[x/sum(untemper) for x in untemper]
    result=dict(at=datetime.now(timezone.utc).isoformat(),status='complete',plan_sha256=sha(OUT/'plan.json'),
        parent=parent,actions=actions,retained=retained,summary=summary,unmatched_history_count=sum(c for m,c in counts.items() if m not in {a['encoded'] for a in actions}),
        model_observation_mass=sum(a['model'] for a in surviving),blend_observation_mass=sum(a['blend'] for a in surviving),powered_observation_mass=mass,
        model_pseudocount_share=parent['n0']/(parent['history_total']+parent['n0']),truth_move=truth['move'],truth_retained_weight=truth['retained_weight'],
        merge_example=dict(path_probabilities=[.25,.25,.5],linear_board_probabilities=[.5,.5],tempered_board_weights=[1/3,2/3],sqrt_of_merged_weights=untemper),
        verification=['All frozen inputs, original inference sources, coefficients, binary and raw outputs match.',
                      'Independent history.bin decoding matches all counts and denominator.',
                      'All 20 feature-dot logits, softmax and history blends reconcile.',
                      'The 14 surviving moves match the earlier independent course enumeration.',
                      'All 14 native posterior weights match powered likelihood and observation filtering; default sampler includes all 14.',
                      'Square-root-after-merge algebra differs from the untempered board sum.'],scope=plan['scope'])
    save(OUT/'result.json',result)
    print(json.dumps({k:result[k] for k in ('status','parent','model_observation_mass','blend_observation_mass','model_pseudocount_share','truth_move','truth_retained_weight','merge_example')},indent=2))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('stage','run','review')
    # Short fixed calculation, with no timed playing lane. Respect the core lease.
    owner='astra-'+NAME;path=ROOT/'chatroom/cores.json'
    def lease(take):
        with open('/tmp/iamavirus-cores-json.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);value=read(path)
            if take:
                assert not any(6 in r['cores'] for r in value['allocation'])
                value['allocation'].append(dict(owner=owner,cores=[6],pid=os.getpid(),at=datetime.now(timezone.utc).isoformat()))
            else:value['allocation']=[r for r in value['allocation'] if not (r['owner']==owner and r.get('pid')==os.getpid())]
            value['updated']=datetime.now(timezone.utc).isoformat();temp=path.with_suffix('.weights-tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)
    lease(True)
    try:globals()[sys.argv[1]]()
    finally:lease(False)
