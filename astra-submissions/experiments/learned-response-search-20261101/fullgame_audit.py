#!/usr/bin/env python3
"""Read-only post-match response audit; never changes frozen bench dependencies."""
import ctypes
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/learned-response-search-20261101/full-games'
sys.path.insert(0,str(ROOT))
from learning import ingest

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    plan=json.loads((OUT/'plan.json').read_text())
    jobs=[j for j in plan['jobs'] if j['phase']=='h2h']
    assert len(jobs)==8 and all((OUT/'jobs'/j['id']/'result.json').exists() for j in jobs)
    model=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
    assert sha(model)==plan['model_sha256']
    adapter=HERE/'build/adapter.so'
    proof=HERE.parent/'observable-response-audit-20261101/build/proof.so'
    proof_plan=json.loads((OUT.parents[1]/'observable-response-audit-20261101/plan.json').read_text())
    assert sha(proof)==proof_plan['library_sha256']
    lib=ctypes.CDLL(str(adapter));pr=ctypes.CDLL(str(proof));pr.fow_init()
    u8=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS')
    u16=np.ctypeslib.ndpointer(dtype=np.uint16,flags='C_CONTIGUOUS')
    dp=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.visible_pack.argtypes=[ctypes.c_char_p,ctypes.c_int,u16,ctypes.c_int,u8,u16]
    lib.astra_response_load.argtypes=[ctypes.c_char_p];lib.astra_response_load.restype=ctypes.c_void_p
    lib.astra_response_probs.argtypes=[ctypes.c_void_p,u8,u16,ctypes.c_int,dp]
    pr.observable_fatal.argtypes=[u8,u16,ctypes.c_int,u8,u8]
    weights=lib.astra_response_load(str(model).encode());assert weights
    records=[];games=[];proofs=0;frames=0;values={'p':1,'n':3,'b':3,'r':5,'q':9,'k':0}
    for job in jobs:
        directory=OUT/'jobs'/job['id'];receipt=json.loads((directory/'result.json').read_text())
        assert not receipt['faults'] and sha(directory/'replay.json')==receipt['replay_sha256']
        replay=json.loads((directory/'replay.json').read_text());states,errors=ingest.validate_replay(replay)
        assert not errors;frames+=len(states)
        ourside=0 if job['side']=='white' else 1;side=1-ourside
        def net(frame):
            return sum(values[c.lower()]*(1 if c.isupper()==(ourside==0) else -1)
                       for c in frame['board'] if c!='-')
        losses=[]
        for ply in range(ourside,len(states)-3,2):
            change=net(replay['frames'][ply+3])-net(replay['frames'][ply])
            if change<=-3:
                losses.append(dict(ply=ply,moves=[replay['frames'][ply+i]['move'] for i in (1,2,3)],net_change=change))
        games.append(dict(job=job['id'],score=receipt['score'],plies=receipt['plies'],
                          material_before_final_move=net(replay['frames'][-2]),three_ply_material_drops=losses,
                          result_sha256=sha(directory/'result.json'),replay_sha256=receipt['replay_sha256']))
        for ply in range(side,len(states)-1,2):
            state=states[ply];legal=state.board.legal_moves();target=replay['frames'][ply+1]['move']
            native=[]
            for move in legal:
                fr=ord(move[0])-97+8*(int(move[1])-1);to=ord(move[2])-97+8*(int(move[3])-1)
                promo=' nbrq'.index(move[4]) if len(move)==5 else 6
                native.append(fr|(to<<6)|(promo<<12))
            native=np.array(native,dtype=np.uint16);tokens=np.zeros(64,dtype=np.uint8)
            encoded=np.zeros(len(legal),dtype=np.uint16);q=np.zeros(len(legal))
            fatal=np.zeros(len(legal),dtype=np.uint8);witness=np.zeros(len(legal),dtype=np.uint8)
            assert lib.visible_pack(state.board.observation(side).encode(),side,native,len(legal),tokens,encoded)
            assert lib.astra_response_probs(weights,tokens,encoded,len(legal),q)
            assert pr.observable_fatal(tokens,encoded,len(legal),fatal,witness)
            for a in np.flatnonzero(fatal):
                assert state.board.move_loses_king(legal[a]),(job['id'],ply,legal[a]);proofs+=1
            a=legal.index(target);mass=float(q[fatal.astype(bool)].sum())
            conditioned=q.copy();safe=float(q[~fatal.astype(bool)].sum())
            applied=bool(fatal.any() and not fatal.all() and safe>0)
            if applied:conditioned[fatal.astype(bool)]=0;conditioned/=safe
            records.append(dict(job=job['id'],ply=ply,opponent_move=target,actions=len(legal),
                                probability=float(q[a]),projected_probability=float(conditioned[a]),
                                proven_actions=int(fatal.sum()),proven_mass=mass,
                                chosen_proven=bool(fatal[a]),chosen_true_fatal=bool(state.board.move_loses_king(target)),
                                projected=applied,uniform_nll=math.log(len(legal))))
    def nll(field):
        return sum(-math.log(r[field]) for r in records)/len(records) if all(r[field]>0 for r in records) else None
    summary=dict(scope='Post-match true-world response audit. Does not show which worlds were searched or prove a causal explanation of losses.',
                 model_sha256=sha(model),adapter_sha256=sha(adapter),proof_sha256=sha(proof),source_sha256=sha(Path(__file__)),
                 games=games,validated_frames=frames,decisions=len(records),positive_proofs_verified=proofs,
                 selected_proven_loss=sum(r['chosen_proven'] for r in records),selected_true_loss=sum(r['chosen_true_fatal'] for r in records),
                 mean_proven_mass=sum(r['proven_mass'] for r in records)/len(records),
                 raw_nll=nll('probability'),projected_nll=nll('projected_probability'),
                 uniform_nll=sum(r['uniform_nll'] for r in records)/len(records),
                 material_scope='Historical three-ply net drops include both sides at the same frames; longer exchanges and compensation are not assessed.')
    with (OUT/'response-audit-decisions.jsonl').open('x') as f:
        for row in records:f.write(json.dumps(row)+'\n')
    summary['decisions_sha256']=sha(OUT/'response-audit-decisions.jsonl')
    with (OUT/'response-audit.json').open('x') as f:json.dump(summary,f,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in summary.items() if k!='games'},indent=2))

if __name__=='__main__':main()
