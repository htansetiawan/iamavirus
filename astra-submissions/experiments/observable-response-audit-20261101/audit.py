#!/usr/bin/env python3
"""Measure the frozen response model's mass on provably losing moves."""
import ctypes
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/observable-response-audit-20261101'
SOURCE=HERE.parent/'visible-response-20261101'
sys.path.insert(0,str(SOURCE));import data
from learning import ingest

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def freeze():
    games=[r for r in json.loads((data.OUT/'manifest.json').read_text())['games'] if r['split']=='validation'][:100]
    model=data.OUT/'models/response.bin'
    assert sha(model)=='45a41cf4ecaae9324472ae93a81b349d597cec20364a7c73ef66e513df077c97'
    plan=dict(at_utc=datetime.now(timezone.utc).isoformat(),games=games,model=str(model),model_sha256=sha(model),
              source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'proof.c',HERE/'proof.h',HERE/'test_proof.c',SOURCE/'data.py']},
              library_sha256=sha(HERE/'build/proof.so'),scope='Development audit on previously used validation games, no calibration fit or change to active match configuration.')
    with (OUT/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
    print(json.dumps({'frozen_games':len(games),'model':plan['model_sha256']}))

def run():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['source_sha256'].items():assert sha(ROOT/p)==h,p
    assert sha(Path(plan['model']))==plan['model_sha256'] and sha(HERE/'build/proof.so')==plan['library_sha256']
    lib=ctypes.CDLL(str(HERE/'build/proof.so'));lib.fow_init()
    u8=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');u16=np.ctypeslib.ndpointer(dtype=np.uint16,flags='C_CONTIGUOUS');dp=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.observable_fatal.argtypes=[u8,u16,ctypes.c_int,u8,u8];lib.astra_response_load.argtypes=[ctypes.c_char_p];lib.astra_response_load.restype=ctypes.c_void_p
    lib.astra_response_probs.argtypes=[ctypes.c_void_p,u8,u16,ctypes.c_int,dp]
    w=lib.astra_response_load(plan['model'].encode());assert w
    records=[];proofs=0;frames=0;chosen_proof=[]
    for g in plan['games']:
        path=ROOT/'data/raw/games'/g['game']/'replay.json';assert sha(path)==g['replay_sha256']
        rp=json.loads(path.read_text());states,errors=ingest.validate_replay(rp);assert not errors;frames+=len(states)
        for side,key in enumerate(['white','black']):
            if rp[key] not in data.TEAMS:continue
            for ply,tokens,legal,target in data.actor_decisions(rp,side):
                moves=np.array([data.encode_move(m,side) for m in legal],dtype=np.uint16)
                flags=np.zeros(len(moves),dtype=np.uint8);witness=np.zeros(len(moves),dtype=np.uint8);q=np.zeros(len(moves))
                assert lib.observable_fatal(tokens,moves,len(moves),flags,witness)==1
                assert lib.astra_response_probs(w,tokens,moves,len(moves),q)==1
                for a in np.flatnonzero(flags):
                    assert states[ply].board.move_loses_king(legal[a]),('UNSOUND',g['game'],ply,legal[a],int(witness[a]));proofs+=1
                target_index=legal.index(target);y=int(flags[target_index]);actual=bool(states[ply].board.move_loses_king(target))
                r=dict(game=g['game'],ply=ply,side=side,team=rp[key],actions=len(moves),proven_fatal=int(flags.sum()),
                       predicted_fatal_mass=float(q[flags.astype(bool)].sum()),recorded_proven_fatal=y,recorded_true_fatal=actual,
                       target=target,witness=int(witness[target_index]),recorded_probability=float(q[target_index]))
                records.append(r)
                if y:chosen_proof.append(r)
    def group(rows):
        n=len(rows)
        return dict(decisions=n,predicted_mean=sum(r['predicted_fatal_mass'] for r in rows)/n if n else None,
                    observed_proven_rate=sum(r['recorded_proven_fatal'] for r in rows)/n if n else None,
                    observed_proven_count=sum(r['recorded_proven_fatal'] for r in rows),
                    observed_true_fatal_count=sum(r['recorded_true_fatal'] for r in rows))
    mixed=[r for r in records if 0<r['proven_fatal']<r['actions']]
    result=dict(at_utc=datetime.now(timezone.utc).isoformat(),scope=plan['scope'],games=len(plan['games']),frames_validated=frames,
                positive_proofs_verified=proofs,all=group(records),mixed_choices=group(mixed),
                forced_observable_loss=group([r for r in records if r['proven_fatal']==r['actions']]),
                no_visible_proof=group([r for r in records if r['proven_fatal']==0]),
                by_team={team:group([r for r in mixed if r['team']==team]) for team in data.TEAMS},
                chosen_visible_loss_examples=chosen_proof,
                interpretation='Observable proof is sufficient but incomplete. Rates are developmental and conditional on this selected model-validation subset. No parameter, policy restriction or benchmark changed.')
    with (OUT/'decisions.jsonl').open('x') as f:
        for r in records:f.write(json.dumps(r)+'\n')
    result['decisions_sha256']=sha(OUT/'decisions.jsonl')
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['by_team','chosen_visible_loss_examples']},indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run']);globals()[p.parse_args().command]()
