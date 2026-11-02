"""Recover hashed teacher outputs; no fitting and no TEST-fold examples."""
from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/multipv-distillation-20261102'
OLD=HERE.parent/'native-fow-value-20261102/work/dataset'
sys.path.insert(0,str(ROOT))
from learning import ingest


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def salt(s):return hashlib.sha256(s.encode()).hexdigest()


def write(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')


def encode(board):
    side=board.side; raw=board.board_string(); flip=56 if side else 0
    pieces=np.array(['-PNBRQKpnbrqk'.index(raw[s^flip].swapcase() if side else raw[s]) for s in range(64)],np.uint8)
    castle=np.array([bool(board.castling&(1<<(s^flip))) for s in range(64)],np.uint8)
    ep=64 if board.en_passant<0 else board.en_passant^flip
    half=min(board.halfmove_clock,100)
    key=salt((pieces.tobytes()+castle.tobytes()+bytes([ep,half])).hex())
    return pieces,castle,ep,half,key


def action(move,side):
    def square(text):return ((ord(text[0])-97)+8*(int(text[1])-1))^(56 if side else 0)
    return [square(move[:2]),square(move[2:4]),' nbrq'.index(move[4]) if len(move)==5 else 0]


def prepare():
    os.sched_setaffinity(0,{0,1});started=time.monotonic()
    work=HERE/'work';work.mkdir(exist_ok=False)
    prior=json.loads((ROOT/'astra-submissions/analysis/native-fow-value-20261102/dataset-receipt.json').read_text())
    for name in ('native.jsonl.gz','rows.jsonl.gz'):
        assert sha(OLD/name)==prior['artifacts'][name], 'teacher artifact changed'
    records={};folds={'train':set(),'validation':set()}
    with gzip.open(OLD/'rows.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line)
            if r['fold'] not in folds:continue
            folds[r['fold']].add(r['game']);records[r['id']]=r
    selected={fold:set(sorted(ids,key=lambda g:salt('249-game:'+g))[:n]) for (fold,ids),n in zip(folds.items(),(3000,500))}
    assert len(selected['train'])==3000 and len(selected['validation'])==500
    assert not selected['train']&selected['validation']
    source_pins={str(p.relative_to(ROOT)):sha(p) for p in (OLD/'native.jsonl.gz',OLD/'rows.jsonl.gz',HERE/'README.md',HERE/'model.py',Path(__file__),ROOT/'learning/ingest.py',ROOT/'learning/rules.py')}
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),selected_games={f:sorted(v) for f,v in selected.items()},
          sources=source_pins,selection='salted game IDs; training and development validation only; no outcome/score selection',
          optimization=dict(seed=2491102,epochs=32,batch=256,lr=.001,decay=.0001,kl_weight=.02,temperature=.2,gpu_seconds=1200),
          gate=dict(mae_max=.08,teacher_regret_max=.05,regret_over_half_rate_max=.01)))
    targets={k:r for k,r in records.items() if r['game'] in selected[r['fold']]}
    native={}
    with gzip.open(OLD/'native.jsonl.gz','rt') as f:
        for line in f:
            # The saved teacher file includes old TEST rows; never parse or score them.
            prefix=line.split(',',1)[0]
            ident=json.loads(prefix+'}')['id']
            if ident in targets:native[ident]=json.loads(line)
    assert set(native)==set(targets)
    by_game={}
    for ident,r in targets.items():by_game.setdefault(r['game'],[]).append(ident)
    rows=[];seen=set();counts=Counter();missing=0;frames=0
    for fold in ('train','validation'):
        for gid in sorted(selected[fold]):
            ids=sorted(by_game[gid],key=lambda x:int(x.split(':')[1]))
            rp=ROOT/f'data/raw/games/{gid}/replay.json'
            assert sha(rp)==targets[ids[0]]['replay_sha256']
            replay=json.loads(rp.read_text());states,errors=ingest.validate_replay(replay)
            assert not errors;frames+=len(states)
            for ident in ids:
                r=targets[ident];n=native[ident];parent=states[r['ply']-1].board
                p,c,ep,half,key=encode(parent)
                if key in seen:counts['duplicate_parent']+=1;continue
                seen.add(key)
                acts=[];values=[]
                for a in n['actions']:
                    if not a['found']:missing+=1;continue
                    assert abs(-a['value']-np.tanh(a['cp']/400))<1e-12
                    assert a['move'] in parent.legal_moves()
                    acts.append(action(a['move'],parent.side));values.append(-a['value'])
                if len(acts)<2:counts['fewer_than_two_scored']+=1;continue
                assert len(set(map(tuple,acts)))==len(acts) and len(acts)<=256
                rows.append(dict(id=ident,game=gid,fold=fold,piece=p,castle=c,ep=ep,half=half,
                                 actions=acts,y=values,key=key,replay_sha256=sha(rp)))
                counts[fold]+=1
            if len(rows)%500==0:print(json.dumps(dict(games=gid,parents=len(rows),seconds=time.monotonic()-started)),flush=True)
            if time.monotonic()-started>600:raise TimeoutError('ten-minute data cap')
    N=len(rows);M=max(len(r['actions']) for r in rows)
    a=np.zeros((N,M,3),np.uint8);y=np.zeros((N,M),np.float32);mask=np.zeros((N,M),bool)
    for i,r in enumerate(rows):
        size=len(r['actions']);a[i,:size]=r['actions'];y[i,:size]=r['y'];mask[i,:size]=True
    gids=sorted({r['game'] for r in rows});lookup={g:i for i,g in enumerate(gids)}
    np.savez(work/'data.npz',piece=np.stack([r['piece'] for r in rows]),castle=np.stack([r['castle'] for r in rows]),
             ep=np.array([r['ep'] for r in rows],np.uint8),half=np.array([r['half'] for r in rows],np.uint8),
             actions=a,y=y,mask=mask,game=np.array([lookup[r['game']] for r in rows]),
             fold=np.array([r['fold']=='validation' for r in rows],np.uint8))
    with gzip.open(OUT/'rows.jsonl.gz','wt') as f:
        for r in rows:f.write(json.dumps({k:r[k] for k in ('id','game','fold','key','replay_sha256')})+'\n')
    write(OUT/'data-receipt.json',dict(passed=True,counts=dict(counts),parents=N,actions=int(mask.sum()),max_actions=M,
          excluded_unscored=missing,checked_frames=frames,seconds=time.monotonic()-started,
          data_sha256=sha(work/'data.npz'),rows_sha256=sha(OUT/'rows.jsonl.gz'),plan_sha256=sha(OUT/'plan.json')))
    print(json.dumps(dict(prepared=True,parents=N,actions=int(mask.sum()),counts=dict(counts),seconds=time.monotonic()-started)),flush=True)


if __name__=='__main__':prepare()
