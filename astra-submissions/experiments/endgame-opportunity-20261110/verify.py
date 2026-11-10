"""Independent native board/material scan of the frozen training census."""
import ctypes as C
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/endgame-opportunity-20261110'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encode(s):
    sq=lambda t:ord(t[0])-97+8*(int(t[1])-1)
    return sq(s[:2])|(sq(s[2:4])<<6)|(('pnbrqk'.index(s[4]) if len(s)==5 else 6)<<12)
def classify(text):
    white=''.join(sorted(c for c in text if c.isupper()))
    black=''.join(sorted(c.upper() for c in text if c.islower()))
    labels=[]
    for side,a,b in ((0,white,black),(1,black,white)):
        if b=='K' and a in ('KQ','KR','KRR'):labels.append((side,{'KQ':'QK','KR':'RK','KRR':'RRK'}[a]))
    return labels


def main():
    start=time.monotonic();plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    rows=json.loads((OUT/'games.json').read_text());assert sha(OUT/'games.json')==result['games_sha256']
    fixtures=[('KQk',[(0,'QK')]),('KRk',[(0,'RK')]),('KRRk',[(0,'RRK')]),
              ('Kkq',[(1,'QK')]),('Kkr',[(1,'RK')]),('Kkrr',[(1,'RRK')]),
              ('KQPk',[]),('KQkp',[]),('Kk',[]),('KQRk',[])]
    for text,wanted in fixtures:assert classify(text)==wanted
    binary=ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110/build/bridge.so'
    old=json.loads(Path(next(p for p in plan['dependencies'] if p.endswith('/capture-fixed-prior-20261110/plan.json'))).read_text())
    assert sha(binary)==old['dependencies'][str(binary)]
    lib=C.CDLL(str(binary),mode=C.RTLD_LOCAL);lib.prior_state.argtypes=[C.c_char_p]*3;lib.prior_step.argtypes=[C.c_uint16]
    lib.fow_init()  # prior_load normally does this; this audit loads no history table.
    buffers=[C.create_string_buffer(65) for _ in range(3)]
    minimum=65;min_at=None;frames=0;broad=[];entered={}
    for g,row in zip(plan['games'],rows):
        assert g['game']==row['game'];lib.prior_start();own=0 if g['white']=='IAmAVirus' else 1;entries={}
        for ply in range(len(g['moves'])+1):
            side=lib.prior_state(*buffers);assert side==ply%2
            board=buffers[0].value.decode();assert len(board)==64 and set(board)<=set('PNBRQKpnbrqk-')
            frames+=1;pieces=sum(c!='-' for c in board)
            if pieces<minimum:minimum=pieces;min_at=dict(game=g['game'],ply=ply,board=board)
            categories=classify(board)
            if categories:broad.append(dict(game=g['game'],ply=ply,labels=categories))
            terminal=ply==len(g['moves']) and row['course_terminal'] is not None
            if side==own and not terminal:
                for strong,family in categories:
                    key=('own' if strong==own else 'opponent')+'-'+family
                    entries.setdefault(key,ply)
            if ply<len(g['moves']):assert lib.prior_step(encode(g['moves'][ply]))>=0
        assert entries=={k:v['ply'] for k,v in row['entries'].items()},g['game']
        entered[g['game']]=entries
    assert frames==result['frames'] and len(rows)==result['games']
    review=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,frames=frames,games=len(rows),
        material_positive_and_negative_fixtures=len(fixtures),native_material_entries_match=True,
        all_turns_including_terminal_material_matches=broad,minimum_total_pieces=minimum,minimum_at=min_at,
        native_library_sha256=sha(binary),review_source_sha256=sha(__file__),seconds=time.monotonic()-start,
        scope='Independent C board replay and sorted-character material labels, not another fit or strength test. Terminal labels remain from the course-referee census.')
    with (OUT/'independent-review.json').open('x') as f:json.dump(review,f,indent=2);f.write('\n')
    print(json.dumps(review,indent=2),flush=True)


if __name__=='__main__':main()
