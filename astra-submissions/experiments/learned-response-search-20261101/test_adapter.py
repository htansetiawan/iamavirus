#!/usr/bin/env python3
"""Actual private replay inputs versus the native model adapter."""
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/learned-response-search-20261101'
NEURAL=HERE.parent/'visible-response-20261101'
sys.path.insert(0,str(NEURAL));import data

def main():
    src=HERE/'build/src';libpath=HERE/'build/adapter.so'
    cmd=['gcc','-O2','-shared','-fPIC','-std=c11','-I'+str(src),str(src/'adapter.c'),str(src/'response.c'),'-lm','-o',str(libpath)]
    subprocess.run(cmd,check=True);lib=ctypes.CDLL(str(libpath))
    u8=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');u16=np.ctypeslib.ndpointer(dtype=np.uint16,flags='C_CONTIGUOUS')
    lib.visible_pack.argtypes=[ctypes.c_char_p,ctypes.c_int,u16,ctypes.c_int,u8,u16]
    games=[g for g in json.loads((data.OUT/'manifest.json').read_text())['games'] if g['split']=='validation'][:20]
    count=promotions=0;colours={0:0,1:0};unknown=empty=0
    for g in games:
        raw=(ROOT/'data/raw/games'/g['game']/'replay.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==g['replay_sha256'];rp=json.loads(raw)
        for side in (0,1):
            for ply,expected,legal,target in data.actor_decisions(rp,side):
                rawmoves=[]
                for move in legal:
                    fr=ord(move[0])-97+8*(int(move[1])-1);to=ord(move[2])-97+8*(int(move[3])-1)
                    pr=' nbrq'.index(move[4]) if len(move)==5 else 6
                    rawmoves.append(fr|(to<<6)|(pr<<12))
                rawmoves=np.array(rawmoves,dtype=np.uint16)
                tokens=np.zeros(64,dtype=np.uint8);encoded=np.zeros(256,dtype=np.uint16)
                view=rp['frames'][ply][('white','black')[side]].encode()
                assert lib.visible_pack(view,side,rawmoves,len(rawmoves),tokens,encoded)==1
                assert np.array_equal(tokens,expected)
                expected_moves=np.array([data.encode_move(m,side) for m in legal],dtype=np.uint16)
                assert np.array_equal(encoded[:len(legal)],expected_moves)
                # Ordering is preserved, including reversed action lists.
                assert lib.visible_pack(view,side,rawmoves[::-1].copy(),len(rawmoves),tokens,encoded)==1
                assert np.array_equal(encoded[:len(legal)],expected_moves[::-1])
                count+=1;colours[side]+=1;promotions+=sum(len(m)==5 for m in legal)
                unknown+=int((tokens==12).sum());empty+=int((tokens==13).sum())
    # Explicit canonical promotion fixtures for both colours, all four types.
    for side in (0,1):
        view=['?']*64;fr=48 if side==0 else 8;to=56 if side==0 else 0;view[fr]='P' if side==0 else 'p'
        moves=np.array([fr|(to<<6)|(p<<12) for p in (1,2,3,4)],dtype=np.uint16)
        tokens=np.zeros(64,dtype=np.uint8);encoded=np.zeros(256,dtype=np.uint16)
        assert lib.visible_pack(''.join(view).encode(),side,moves,4,tokens,encoded)==1
        assert list(encoded[:4])==[48|(56<<6)|(p<<12) for p in (1,2,3,4)]
        for invalid in (0,5,7,15):
            moves[0]=fr|(to<<6)|(invalid<<12)
            assert lib.visible_pack(''.join(view).encode(),side,moves,4,tokens,encoded)==0
    result=dict(replay_games=len(games),actual_actor_queries=count,by_colour=colours,
                legal_promotion_candidates=promotions,hidden_tokens_checked=unknown,empty_tokens_checked=empty,
                explicit_promotions=8,invalid_promotion_fixtures=8,action_reversal_checks=count,
                native_python_encoding='exact',compiler=cmd)
    (OUT/'adapter-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
