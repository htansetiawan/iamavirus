from collections import defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np
from settings import ROOT,OUT,now,sha,unique,position_tuple,StateKey
from extract_augmented import collect
from bound import uci
from learning import rules


def independent_floor(row,geometry,parent_local=False):
    # Alternate representation: tuples of integer float bit patterns, canonical
    # normalizer IDs and math.fsum with per-group scaling. No partition() call.
    tokens=[]
    for j in range(len(row['base'])):
        token=tuple(map(int,row['x'][j].view(np.uint32)))+(int(row['base'][j].view(np.uint32)),)
        if geometry:token+=(int(row['moves'][j]),)
        tokens.append(token)
    normalizers={};parent_ids=[]
    for p in range(len(row['u'])):
        signature=tuple(sorted(tokens[j] for j in np.flatnonzero(row['a_parent']==p)))
        if signature not in normalizers:normalizers[signature]=len(normalizers)
        parent_ids.append(normalizers[signature])
    buckets=defaultdict(list)
    for j in np.flatnonzero(row['valid']):
        p=int(row['a_parent'][j]);n=int(row['hn'][p]);n=n if n>=3 else 0
        key=(p if parent_local else parent_ids[p],n,tokens[j],int(row['counts'][j]) if n else 0)
        buckets[key].append((float(row['u'][p]),bool(row['positive'][j])))
    best=-math.inf
    for group in buckets.values():
        positive=[v for v,is_positive in group if is_positive]
        if not positive:continue
        all_values=[v for v,_ in group];amax=max(all_values);pmax=max(positive)
        log_all=amax+math.log(math.fsum(math.exp(v-amax) for v in all_values))
        log_positive=pmax+math.log(math.fsum(math.exp(v-pmax) for v in positive))
        best=max(best,log_positive-log_all)
    return max(0.,-best)


def main():
    os.sched_setaffinity(0,{2,3});plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    assert sha(OUT/'bounds.jsonl.gz')==result['bounds_sha256']
    records=[json.loads(s) for s in gzip.open(OUT/'bounds.jsonl.gz','rt')]
    cases=collect(plan,'validation',receipt_name='review-data.json');assert len(cases)==len(records)
    h=hashlib.sha256();worst=0.
    for row,r in zip(cases,records):
        assert row['meta']==r['metadata']
        for name in ('moves','successor_keys','parent_rows'):h.update(row[name].tobytes())
        for geometry,local,key in ((False,False,'features'),(True,False,'geometry'),(False,True,'parent_local'),(True,True,'geometry_parent_local')):
            error=abs(independent_floor(row,geometry,local)-r[key]['nll_floor']);worst=max(worst,error);assert error<1e-10
    assert h.hexdigest()==result['extra_export_sha256']
    original=json.loads((OUT/'validation-data.json').read_text());repeated=json.loads((OUT/'review-data.json').read_text())
    assert original['features_sha256']==repeated['features_sha256'] and original['games']==repeated['games']
    witnesses=json.loads((OUT/'witnesses.json').read_text());transitions=0
    for w in witnesses:
        path=ROOT/w['path'];assert sha(path)==w['sha256']
        with np.load(path,allow_pickle=False) as z:row={k:z[k] for k in z.files}
        rp=json.loads((ROOT/'data/raw/games'/w['metadata']['game']/'replay.json').read_text())
        view=rp['frames'][w['metadata']['ply']][('white','black')[w['metadata']['us']]]
        chosen=[w['true_edge']]+[a['edge'] for a in w['alternatives']]
        for edge in chosen:
            p=int(row['a_parent'][edge]);native=row['parent_rows'][p]
            board=rules.Board.from_board_string(*position_tuple(native));board.halfmove_clock=int(native['halfmove'])
            move=uci(row['moves'][edge]);assert move in board.legal_moves()
            child=board.copy();child.push(move)
            assert not child.mover_lost() and child.observation(w['metadata']['us'])==view
            key=StateKey()(child.board_string(),child.side,child.castling,child.en_passant)
            assert key==int(row['successor_keys'][edge]);transitions+=1
        assert row['actor_edge'][w['true_edge']] and row['positive'][w['true_edge']]
        assert all(not row['positive'][a['edge']] for a in w['alternatives'])
    for name,pick in {'all':lambda r:True,'primary':lambda r:r['primary'],'late':lambda r:r['primary'] and r['late'],'surprise':lambda r:r['primary'] and r['surprise']}.items():
        bucket=defaultdict(list)
        for r in records:
            if pick(r['metadata']):bucket[r['metadata']['game']].append(r)
        for key,field in (('features','feature_floor'),('geometry','geometry_floor'),('parent_local','parent_local_floor'),('geometry_parent_local','geometry_parent_local_floor')):
            mean=float(np.mean([np.mean([r[key]['nll_floor'] for r in group]) for group in bucket.values()])) if bucket else None
            assert mean==result['metrics'][name][field] or abs(mean-result['metrics'][name][field])<1e-12
    checked=dict(at=now(),cases=len(cases),independent_bound_max_error=worst,
        witness_games=len(witnesses),independent_witness_transitions=transitions,source_and_replay_pins_verified=True,
        augmented_export_reconstruction_exact=True,result_sha256=sha(OUT/'result.json'))
    unique(OUT/'independent-review.json',checked);print(json.dumps(checked),flush=True)


if __name__=='__main__':main()
