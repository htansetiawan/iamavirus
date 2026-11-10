"""Freeze a new constrained architecture on later, sequence-disjoint games."""
from datetime import datetime,timezone
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import numpy as np
import torch
from model import synthetic_checks,COLUMNS,mask

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110';BUILD=HERE/'build'
BASE=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
GEN=Path('/media/henrytan/seagate/git/iamavirus-data/derived/moves/arena-latest-generations/gen-800092857d6f4c6082f4b2a06a2b971c')
TEAMS=['Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','Crimson Fog','Instructors','Mist Opportunities','duck','HYPOTHERMIA']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def library():
    lib=ctypes.CDLL(str(BUILD/'bridge.so'));nd=lambda t:np.ctypeslib.ndpointer(dtype=t,flags='C_CONTIGUOUS')
    lib.prior_load.argtypes=[ctypes.c_char_p];lib.prior_state.argtypes=[ctypes.c_char_p]*3;lib.prior_step.argtypes=[ctypes.c_uint16]
    lib.quiet_features.argtypes=[nd(np.uint16),nd(np.float32),nd(np.float32),nd(np.float32),nd(np.uint32),ctypes.POINTER(ctypes.c_uint),nd(np.uint8)]
    lib.quiet_logp.argtypes=[nd(np.float32),nd(np.float32),ctypes.c_int,ctypes.c_int,nd(np.float32),nd(np.float32),nd(np.float32)]
    assert lib.prior_load(str(BASE/'data/history.bin').encode());return lib

def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False);torch.set_num_threads(2)
    cmd=['gcc','-O3','-std=c11','-shared','-fPIC','-pthread','-I'+str(BASE/'src'),str(HERE/'bridge.c'),
         str(BASE/'src/board.c'),str(BASE/'src/movemodel.c'),'-lm','-o',str(BUILD/'bridge.so')]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    unit=['gcc','-O1','-g','-std=c11','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(HERE/'unit.c'),'-lm','-o',str(BUILD/'unit')]
    r=subprocess.run(unit,capture_output=True,text=True,timeout=30);assert r.returncode==0,r.stderr
    # LSan cannot run under this environment's ptrace monitor; full host unit
    # is separately required before any fit. ASan/UBSan run here without LSan.
    r=subprocess.run([str(BUILD/'unit')],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),timeout=20)
    assert r.returncode==0,r.stderr
    lib=library();rng=np.random.default_rng(2931100);native=[]
    for F in (14,22):
        x=rng.normal(size=(37,26)).astype(np.float32);x[:,0]=(np.arange(37)%3==0);b=rng.normal(size=37).astype(np.float32)
        lin=rng.normal(0,.1,F).astype(np.float32);q=rng.normal(0,.1,(F,F)).astype(np.float32)*mask(F).numpy();out=np.empty(37,np.float32);z=np.zeros_like(lin);zq=np.zeros_like(q);original=np.empty_like(out)
        lib.quiet_logp(x,b,37,F,z,zq,original);lib.quiet_logp(x,b,37,F,lin,q,out)
        assert np.array_equal(out[x[:,0]>0],original[x[:,0]>0])
        v=x[:,COLUMNS[:F]].astype(float);d=v@lin.astype(float)+np.einsum('ni,ij,nj->n',v,q.astype(float),v)
        quiet=x[:,0]==0;old=np.exp(b[quiet].astype(float)).sum();new=np.exp(b[quiet].astype(float)+d[quiet]).sum()
        reference=original.astype(float);reference[quiet]+=d[quiet]+np.log(old/new)
        error=float(abs(out-reference).max());assert error<2e-6,error
        native.append(dict(features=F,capture_bitwise=True,scalar_reference_error=error))
    metadata=[json.loads(line) for line in (GEN/'games.jsonl').read_text().splitlines()]
    windows={'train':('2026-11-02T06:00','2026-11-08',4000),'validation':('2026-11-08','2026-11-09',400),'test':('2026-11-09','2026-11-10',400)}
    seen=set();games=[];excluded=[];inventory={}
    for split,(low,high,cap) in windows.items():
        candidates=[r for r in metadata if low<=r['createdAt']<high and any(r.get(c) in TEAMS for c in ('white','black'))]
        inventory[split]=len(candidates);candidates.sort(key=lambda r:hashlib.sha256(('capture-fixed293:'+r['id']).encode()).digest());count=0
        for row in candidates:
            p=ROOT/'data/raw/games'/row['id']/'replay.json';raw=p.read_bytes();rp=json.loads(raw)
            sig=hashlib.sha256(' '.join(f['move'] for f in rp['frames'][1:]).encode()).hexdigest()
            assert sig==row['moves_sha256']
            if sig in seen or rp.get('rulesVersion')!='fow-v1':
                excluded.append(dict(game=row['id'],split=split,reason='sequence duplicate or rules'));continue
            seen.add(sig)
            plies=[i for i in range(len(rp['frames'])-1) if rp[('white','black')[i%2]] in TEAMS]
            if split=='train':plies=sorted(sorted(plies,key=lambda i:hashlib.sha256(f"capture-fixed293:{row['id']}:{i}".encode()).digest())[:24])
            games.append(dict(game=row['id'],split=split,created_at=rp['createdAt'],white=rp['white'],black=rp['black'],
                              white_version=rp.get('whiteVersion'),black_version=rp.get('blackVersion'),selected_plies=plies,
                              replay_sha256=hashlib.sha256(raw).hexdigest(),sequence_sha256=sig,frames=len(rp['frames'])))
            count+=1
            if count==cap:break
        assert count==cap,(split,count,inventory)
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,commands=[cmd,unit],
          unit_stdout=r.stdout,native=native,torch=synthetic_checks(),inventory=inventory,
          scope='Synthetic/math checks and cohort preparation only; no fit, validation or test scoring. Full host leak-sanitizer unit required before fit.'))
    deps=[HERE/n for n in ('prepare.py','bridge.c','quiet.h','model.py','unit.c','train.py','review.py')]
    deps+=[BUILD/'bridge.so',BUILD/'unit',GEN/'manifest.json',GEN/'games.jsonl',BASE/'data/history.bin',
           HERE.parent/'deployed-prior-comparison-20261102/prior.c',ROOT.parent/'fow-starter/referee.py']+list((BASE/'src').glob('*'))
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),games=games,sequence_exclusions=excluded,windows=windows,teams=TEAMS,
          generation=str(GEN),generation_sha256=sha(GEN/'manifest.json'),dependencies={str(p):sha(p) for p in deps},
          seed=2931110,cores=[0,1],epochs=12,batch=512,learning_rate=.03,ridge=.001,max_seconds=1800,bootstrap_draws=2000,
          gate=dict(full_gain=.05,cheap_gain=.03,matched_linear_gain=.02,surprise_min=100,all_move_nonregression=True,capture_logp_tolerance=2e-5),
          models=['capture-fixed linear','capture-fixed quadratic'],
          scope='New constrained conditional prior architecture; existing capture probabilities and total capture mass fixed while quiet odds are learned. '
                'Quiet means non-capturing, not observation-silent. Native features/base coefficients/history table fixed; no identities as model inputs. '
                'True parent public replay features are the same representation the belief prior uses per hypothesis, not an information-set-realizable opponent policy. '
                'Fresh chronological fit splits relative to old Nov2 predictors; late evaluation may overlap previously curated taxonomy, so not pristine prospective confirmation. '
                'Matched constrained linear isolates interactions from recency; no old model/test is reclassified as passed.',
          next='Only all predictive gates permit a separately frozen prospective/posterior design. Capture-likelihood preservation is not sequential-belief or king-safety preservation. '
               'No automatic fit sweep, old-test threshold changes, games, runtime integration, GPU use, release or arena action.'))
    print(json.dumps(dict(prepared=True,games=len(games),inventory=inventory,pins=len(set(map(str,deps))))),flush=True)
if __name__=='__main__':main()
