"""Independent referee/NumPy checks of the excluded three-game data pilot."""
from collections import Counter
import gzip
import importlib.util
import json
import math
import numpy as np

from data import HERE,ROOT,OUT,load,sha,write_new,now


def main():
    plan,games=load();path=ROOT.parent/'fow-starter/referee.py'
    spec=importlib.util.spec_from_file_location('native_value_referee',path);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    target=HERE/'work/pilot';d=np.load(target/'data.npz')
    with gzip.open(target/'rows.jsonl.gz','rt') as f:rows=[json.loads(l) for l in f]
    with gzip.open(target/'native.jsonl.gz','rt') as f:values={r['id']:r for r in map(json.loads,f)}
    boards={};frames=0;actions=0;found=0;terminal=0;maxerror=0
    for g in games:
        if g['row']['id'] not in plan['pilot_games']:continue
        p=ROOT/g['path'];assert sha(p)==g['sha256'];r=json.loads(p.read_text())
        b=ref.FowBoard();history=Counter({ref.position_key(b):1})
        for i,frame in enumerate(r['frames']):
            if i:
                assert frame['move'] in {m.uci() for m in ref.fow_moves(b)}
                b.push_uci(frame['move']);history[ref.position_key(b)]+=1
            f=ref.make_frame(b,frame['clocks']);assert all(f[k]==frame[k] for k in ('board','white','black'))
            boards[f"{r['id']}:{i}"]=b.copy(stack=False);frames+=1
        actual=ref.outcome(b,history)
        assert actual==(r['result'],r['reason']) or (r['reason']=='Move limit reached' and len(r['frames'])==1001)
    for i,row in enumerate(rows):
        b=boards[row['id']];color=b.turn;f=ref.make_frame(b,[0,0]);v=values[row['id']]
        for k in ('board','white','black'):assert f[k]==v[k]
        expected=np.zeros((64,5),dtype=np.uint8)
        own=f['white' if color else 'black'];other=f['black' if color else 'white']
        for sq in range(64):
            canonical=sq if color else sq^56
            piece=f['board'][sq];piece=piece if color else piece.swapcase()
            expected[canonical]=['-PNBRQKpnbrqk'.index(piece),own[sq]!='?',other[sq]!='?',
                                 bool(b.clean_castling_rights()&(1<<sq)),b.ep_square==sq]
        assert np.array_equal(expected,d['x'][i]);assert d['half'][i]==min(100,b.halfmove_clock)
        assert (v['value']+1)/2==row['native_probability']
        assert abs(float(d['sf'][i])-row['native_probability'])<3e-8
        parent=boards[f"{row['game']}:{row['ply']-1}"]
        legal={m.uci():m for m in ref.fow_moves(parent)}
        assert set(legal)=={a['move'] for a in v['actions']}
        for a in v['actions']:
            q=parent.copy(stack=False);q.push(legal[a['move']]);mover=not q.turn
            opposing=q.king(q.turn);moving=q.king(mover)
            expectation=None
            if opposing is None:expectation=-1.
            elif moving is None or q.is_attacked_by(q.turn,moving):expectation=1.
            elif not ref.fow_moves(q):expectation=-1.
            if expectation is not None:terminal+=1
            elif a['found']:expectation=-math.tanh(a['cp']/400);found+=1
            if expectation is not None:
                error=abs(a['value']-expectation);maxerror=max(maxerror,error);assert error<1e-12
            actions+=1
    report=dict(at=now(),passed=True,frames=frames,positions=len(rows),native_actions=actions,
        independent_cp_transforms=found,independent_terminal_overrides=terminal,maximum_error=maxerror,
        plan_sha256=sha(OUT/'plan.json'),source_sha256=sha(__file__),referee_sha256=sha(path),
        scope='Excluded pilot: all replay states, canonical features, all parent action identities, scored-value transforms and terminal overrides. Fallback eval is reused archived code, not independently reimplemented.')
    write_new(OUT/'pilot-review.json',report);print(json.dumps(report))


if __name__=='__main__':main()
