#!/usr/bin/env python3
"""Post-gate truth-only review; never feed counterfactual truth to a bot."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/learned-response-search-20261101'
sys.path.insert(0,str(ROOT))
from learning import ingest

def main():
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    rows=json.loads((OUT/'labelled.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    lib=ctypes.CDLL(str(HERE/'build/adapter.so'))
    u8=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS');u16=np.ctypeslib.ndpointer(dtype=np.uint16,flags='C_CONTIGUOUS')
    dp=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.visible_pack.argtypes=[ctypes.c_char_p,ctypes.c_int,u16,ctypes.c_int,u8,u16]
    lib.astra_response_load.argtypes=[ctypes.c_char_p];lib.astra_response_load.restype=ctypes.c_void_p
    lib.astra_response_probs.argtypes=[ctypes.c_void_p,u8,u16,ctypes.c_int,dp]
    model=Path(plan['model']);assert hashlib.sha256(model.read_bytes()).hexdigest()==plan['model_sha256']
    weights=lib.astra_response_load(str(model).encode());assert weights
    cache={};review=[]
    for row in rows:
        if len({a['move'] for a in row['arms'].values()})==1:continue
        if row['game'] not in cache:
            rp=json.loads((ROOT/'data/raw/games'/row['game']/'replay.json').read_text())
            states,errors=ingest.validate_replay(rp);assert not errors;cache[row['game']]=states
        state=cache[row['game']][row['ply']];item={k:row[k] for k in ['name','opponent','recorded_move_tags']}
        item.update(board=state.board.board_string(),our_view=state.board.observation(state.board.side),safe_moves=len(row['safe_moves']),arms={})
        for arm,record in row['arms'].items():
            child=state.copy();child.push(record['move']);report=dict(move=record['move'],label=record['label'])
            if child.outcome() is None:
                side=child.board.side;view=child.board.observation(side);legal=child.board.legal_moves()
                native=[]
                for m in legal:
                    fr=ord(m[0])-97+8*(int(m[1])-1);to=ord(m[2])-97+8*(int(m[3])-1)
                    pr=' nbrq'.index(m[4]) if len(m)==5 else 6;native.append(fr|(to<<6)|(pr<<12))
                native=np.array(native,dtype=np.uint16);tokens=np.zeros(64,dtype=np.uint8);encoded=np.zeros(256,dtype=np.uint16);q=np.zeros(len(legal))
                assert lib.visible_pack(view.encode(),side,native,len(native),tokens,encoded)==1
                assert lib.astra_response_probs(weights,tokens,encoded,len(native),q)==1
                ranking=sorted(range(len(q)),key=lambda i:-q[i])
                report['top_predicted_replies']=[dict(move=legal[i],p=float(q[i])) for i in ranking[:5]]
                capture=record['label'].get('worst_capture')
                if capture:
                    idx=legal.index(capture);report['diagnostic_punishing_capture']=dict(move=capture,p=float(q[idx]),rank=ranking.index(idx)+1)
            item['arms'][arm]=report
        review.append(item)
    result=dict(scope='Post-fit, true-world counterfactual response predictions for changed choices; not the sampled solver posterior or a causal diagnosis.',
                model_sha256=plan['model_sha256'],cases=review)
    (OUT/'changed-choice-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'changed_cases':len(review),'output':str(OUT/'changed-choice-review.json')}))

if __name__=='__main__':main()
