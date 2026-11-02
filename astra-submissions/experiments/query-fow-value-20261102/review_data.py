"""Independent array/provenance/dedup review and six full referee trajectories."""
from collections import Counter
import gzip
import importlib.util
import json
import math
import numpy as np
from common import HERE, ROOT, OUT, OLD, OLDOUT, digest, now, sha, write_new
from data import load


def main():
    plan,games=load();target=HERE/'work/holdout'
    receipt=json.loads((OUT/'holdout-receipt.json').read_text());assert receipt['status']=='complete'
    for name,h in receipt['artifacts'].items():assert sha(target/name)==h
    with np.load(target/'data.npz') as archive:d={k:archive[k] for k in archive.files}
    n=len(d['y']);assert all(len(v)==n for v in d.values())
    previous=set()
    for path in (OLD/'work/dataset/data.npz',OLD/'work/pilot/data.npz'):
        with np.load(path) as a:x=a['x'];half=a['half']
        previous.update(digest(row.tobytes()+bytes([int(h)])) for row,h in zip(x,half))
    oldgames=json.loads((OLDOUT/'games.json').read_text())
    assert not {g['row']['id'] for g in games}&{g['row']['id'] for g in oldgames}
    assert not {g['row']['moves_sha256'] for g in games}&{g['row']['moves_sha256'] for g in oldgames}
    assert len({g['row']['moves_sha256'] for g in games})==len(games)
    seen=set();groups=Counter();bygame=Counter();rows={};native={};threats=Counter()
    with gzip.open(target/'rows.jsonl.gz','rt') as f,gzip.open(target/'native.jsonl.gz','rt') as v:
        count=0
        for i,(line,value) in enumerate(zip(f,v,strict=True)):
            row=json.loads(line);state=json.loads(value);count+=1;g=games[int(d['game'][i])]
            assert row['id']==state['id'] and row['game']==g['row']['id'] and row['replay_sha256']==g['sha256']
            assert row['group']==g['group']==('older_unused','new_date')[d['group'][i]]
            key=digest(d['x'][i].tobytes()+bytes([int(d['half'][i])]))
            assert key==row['feature_sha256'] and key not in previous and key not in seen;seen.add(key)
            expected=np.zeros((64,5),dtype=np.uint8);side=state['side']
            own=state['white' if side==0 else 'black'];other=state['black' if side==0 else 'white']
            for sq in range(64):
                piece=state['board'][sq];piece=piece.swapcase() if side else piece
                expected[sq^(56 if side else 0)]=['-PNBRQKpnbrqk'.index(piece),own[sq]!='?',other[sq]!='?',
                    bool(int(state['castle'],16)&(1<<sq)),state['ep']==sq]
            assert np.array_equal(expected,d['x'][i]) and d['half'][i]==min(state['halfmove'],100)
            assert (expected[:,0]==6).sum()==1 and (expected[:,0]==12).sum()==1
            result=g['row']['result'];label=.5 if result=='1/2-1/2' else float((result=='1-0')==(side==0))
            assert label==row['label']==d['y'][i]
            assert abs(float(d['sf'][i])-(state['value']+1)/2)<3e-8 and not state['terminal']
            groups[row['group']]+=1;bygame[row['game']]+=1
            if d['hidden_threat'][i]:threats[row['group']]+=1
            rows[row['id']]=i;native[row['id']]=state
    assert count==n and max(bygame.values())<=8
    path=ROOT.parent/'fow-starter/referee.py';spec=importlib.util.spec_from_file_location('review_referee',path)
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    sample=[g for group in ('older_unused','new_date') for g in [g for g in games if g['group']==group][:3]]
    frames=0;positions=0;actions=0
    for g in sample:
        replay=json.loads((ROOT/g['path']).read_text());b=ref.FowBoard();history=Counter({ref.position_key(b):1})
        for i,frame in enumerate(replay['frames']):
            parent=b.copy(stack=False)
            if i:
                assert frame['move'] in {m.uci() for m in ref.fow_moves(b)}
                b.push_uci(frame['move']);history[ref.position_key(b)]+=1
            f=ref.make_frame(b,[0,0]);assert all(f[k]==frame[k] for k in ('board','white','black'));frames+=1
            ident=f"{g['row']['id']}:{i}"
            if ident not in rows:continue
            ix=rows[ident];state=native[ident];assert all(f[k]==state[k] for k in ('board','white','black'))
            assert state['ep']==(-1 if b.ep_square is None else b.ep_square)
            assert int(state['castle'],16)==b.clean_castling_rights() and state['halfmove']==b.halfmove_clock
            hidden=False
            for color in (True,False):
                king=b.king(not color);view=f['black' if color else 'white']
                hidden|=any(view[sq]=='?' for sq in b.attackers(color,king))
            assert bool(d['hidden_threat'][ix])==hidden
            legal={m.uci():m for m in ref.fow_moves(parent)};assert set(legal)=={a['move'] for a in state['actions']}
            for a in state['actions']:
                q=parent.copy(stack=False);q.push(legal[a['move']]);mover=not q.turn
                expectation=None
                if q.king(q.turn) is None:expectation=-1.
                elif q.king(mover) is None or q.is_attacked_by(q.turn,q.king(mover)):expectation=1.
                elif not ref.fow_moves(q):expectation=-1.
                elif a['found']:expectation=-math.tanh(a['cp']/400)
                if expectation is not None:assert abs(a['value']-expectation)<1e-12
                actions+=1
            positions+=1
        actual=ref.outcome(b,history)
        assert actual==(replay['result'],replay['reason']) or (replay['reason']=='Move limit reached' and len(replay['frames'])==1001)
    report=dict(at=now(),passed=True,positions=n,games_with_positions=len(bygame),groups=dict(groups),hidden_threat=dict(threats),
        all_rows_feature_label_native_alignment=True,all_prior_feature_and_trajectory_disjoint=True,
        independent_referee=dict(games=[g['row']['id'] for g in sample],frames=frames,positions=positions,actions=actions,sha256=sha(path)),
        source_sha256=sha(__file__),data_sha256=sha(target/'data.npz'),
        scope='All rows/provenance/feature and trajectory disjointness; six deterministic complete referee trajectories with baseline action checks. No model scores.')
    write_new(OUT/'holdout-review.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':main()
