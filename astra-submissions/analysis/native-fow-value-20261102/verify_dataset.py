"""Audit every exported row against its native state and frozen source metadata."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'astra-submissions/experiments/native-fow-value-20261102'
sys.path.insert(0,str(SOURCE))
from data import load,sha,OUT,write_new


def main():
    plan,games=load();games=[g for g in games if g['row']['id'] not in plan['pilot_games']]
    receipt=json.loads((OUT/'dataset-receipt.json').read_text());target=SOURCE/'work/dataset'
    assert receipt['status']=='complete' and receipt['collector_exit']==0
    for name,h in receipt['artifacts'].items():assert sha(target/name)==h,name
    # NpzFile does not cache members: loading inside the per-row loop would
    # repeatedly read the full 64 MiB feature array. Materialize each once.
    with np.load(target/'data.npz') as archive:d={name:archive[name] for name in archive.files}
    n=len(d['y']);assert all(len(v)==n for v in d.values())
    assert d['x'].shape==(n,64,5);assert set(d['y'].tolist())<={0,.5,1}
    seen=set();byfold=Counter();bygame=Counter();hidden=Counter();skips=Counter();nrows=0
    with gzip.open(target/'rows.jsonl.gz','rt') as rows,gzip.open(target/'native.jsonl.gz','rt') as native:
        for i,(line,value) in enumerate(zip(rows,native,strict=True)):
            row=json.loads(line);v=json.loads(value);nrows+=1
            assert row['id']==v['id'];gi=int(d['game'][i]);g=games[gi]
            assert row['game']==g['row']['id'] and row['game_index']==gi
            assert row['fold']==g['fold']==('train','validation','test')[d['fold'][i]]
            assert row['replay_sha256']==g['sha256']
            key=hashlib.sha256(d['x'][i].tobytes()+bytes([int(d['half'][i])])).hexdigest()
            assert key==row['feature_sha256'] and key not in seen;seen.add(key)
            expected=np.empty((64,5),dtype=np.uint8);side=v['side'];castle=int(v['castle'],16)
            own=v['white' if side==0 else 'black'];other=v['black' if side==0 else 'white']
            for sq in range(64):
                piece=v['board'][sq];piece=piece.swapcase() if side else piece
                expected[sq^(56 if side else 0)]=['-PNBRQKpnbrqk'.index(piece),own[sq]!='?',other[sq]!='?',
                    bool(castle&(1<<sq)),v['ep']==sq]
            assert np.array_equal(expected,d['x'][i]) and d['half'][i]==min(v['halfmove'],100)
            result=g['row']['result'];label=.5 if result=='1/2-1/2' else float((result=='1-0')==(side==0))
            assert label==row['label']==d['y'][i]
            assert abs(float(d['sf'][i])-(v['value']+1)/2)<3e-8
            assert row['native_probability']==(v['value']+1)/2 and not v['terminal']
            assert row['hidden_king_threat']==bool(d['hidden_threat'][i])
            byfold[row['fold']]+=1;bygame[row['game']]+=1
            if row['hidden_king_threat']:hidden[row['fold']]+=1
            if not row['selected_scored']:skips[row['fold']]+=1
    assert nrows==n and dict(byfold)==receipt['positions'];assert max(bygame.values())<=8
    # No full trajectory or game crosses folds; source hash pins precede extraction.
    trajectories=[g['row']['moves_sha256'] for g in games];assert len(set(trajectories))==len(trajectories)
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,positions=n,by_fold=dict(byfold),
        games_with_positions=len(bygame),selected_source_games=len(games),hidden_threat_positions=dict(hidden),
        selected_moves_without_sf_line=dict(skips),unique_canonical_features=len(seen),
        original_extraction_receipt_sha256=sha(OUT/'dataset-receipt.json'),source_sha256=sha(__file__),
        scope='Every row: hash/provenance, canonical feature reconstruction, score label, native baseline, array alignment, trajectory and feature deduplication. Independent course referee covers excluded pilot, not all full-data trajectories; all full trajectories passed existing rules engine validation.')
    write_new(OUT/'dataset-review.json',report);print(json.dumps(report))


if __name__=='__main__':main()
