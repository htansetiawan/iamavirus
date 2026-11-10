"""Verify own-input privacy, source patches and every saved weight/key cutoff."""
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import struct
import sys

import numpy as np
from prepare import ROOT,HERE,OUT,BUILD,sha,write,patched
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref


def main():
    plan=json.loads((OUT/'plan.json').read_text());done=json.loads((OUT/'completion.json').read_text())
    assert done['error'] is None and done['completed']==8
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    parent=Path(plan['parent'])
    for p in (BUILD/'src').iterdir():
        original=(parent/'src'/p.name).read_text()
        assert p.read_text()==(patched(original) if p.name=='belief.c' else original),p
    rows=[];frames=0;events=[];total_bytes=0
    for case,receipt in zip(plan['cases'],done['results']):
        folder=OUT/case['id'];assert receipt['sha256']==sha(folder/'result.json')
        row=json.loads((folder/'result.json').read_text());assert row['case']==case
        assert row['exit_code']==0 and not row['timed_out'] and not row['live_members']
        for name,digest in row['files'].items():assert sha(folder/name)==digest,name
        replay=json.loads(Path(case['replay_path']).read_text());b=ref.FowBoard()
        side=['white','black'].index(case['side']);feed=['fow',f"{'w' if side==0 else 'b'} 180 2"];moves=[]
        for ply,frame in enumerate(replay['frames'][:case['ply']+1]):
            if ply:
                move=ref.chess.Move.from_uci(frame['move']);assert move in ref.fow_moves(b);b.push(move)
            assert ref.observation(b,True)==frame['white'] and ref.observation(b,False)==frame['black']
            assert ''.join(b.piece_at(i).symbol() if b.piece_at(i) else '-' for i in range(64))==frame['board']
            feed.append(frame[case['side']])
            if ply%2==side:
                feed.append(str(frame['clocks'][side]));move=ref.chess.Move.from_uci(replay['frames'][ply+1]['move'])
                assert move in ref.fow_moves(b);moves.append(move.uci())
            frames+=1
        assert (folder/'input.txt').read_text()=='\n'.join(feed)+'\n'
        assert re.findall(r'^move (\S+)$',(folder/'stdout.txt').read_text(),re.M)==moves
        stderr=(folder/'stderr.txt').read_text();assert 'nodes=' not in stderr and 'stockfish ready' not in stderr
        logged=[json.loads(s) for s in re.findall(r'^astra-cap-mass: (.*)$',stderr,re.M)]
        assert logged==row['events'] and len(logged)==len(row['snapshots'])
        for e in logged:
            saved=row['snapshots'][e['stage']+'.bin'];path=Path(saved['path'])
            assert sha(path)==saved['sha256'] and path.stat().st_size==saved['bytes']==e['bytes']
            raw=path.read_bytes();n,k,t,top=struct.unpack_from('<QQdd',raw)
            assert n==e['n'] and k==e['keep'] and 0<k<n and len(raw)==32+12*n+4*k<=plan['max_snapshot_bytes']
            lw=np.frombuffer(raw,dtype='<f4',offset=32,count=n).astype(float)
            keys=np.frombuffer(raw,dtype='<f8',offset=32+4*n,count=n)
            idx=np.frombuffer(raw,dtype='<u4',offset=32+12*n,count=k)
            assert np.all(np.isfinite(lw)) and np.all(np.isfinite(keys))
            assert len(np.unique(idx))==k and int(idx.max())<n and top==lw.max()==e['max_logw']
            assert t==np.partition(keys,k)[k]==e['cutoff']
            assert keys[idx].max()<=t and keys[idx].min()<t
            below=np.flatnonzero(keys<t)
            assert np.all(np.isin(below,idx)) and len(below)<=k
            w=np.exp(lw-top);total=float(w.sum());kept=float(w[idx].sum());discarded=1-kept/total
            d=lw[idx]+t;assert d.min()>-700
            with np.errstate(over='ignore'):q=-np.expm1(-np.exp(d))
            corrected=float((w[idx]/q).sum()/total);ess=total*total/float(w@w)
            for got,want in [(total,e['scaled_total']),(kept,e['scaled_retained']),(discarded,e['discarded_fraction']),
                             (corrected,e['corrected_fraction']),(ess,e['effective_size'])]:
                assert abs(got-want)<1e-9*max(1,abs(want)),(case['id'],got,want)
            events.append(dict(game=case['game'],id=case['id'],stage=e['stage'],n=n,keep=k,
                   discarded_fraction=discarded,corrected_fraction=corrected,effective_size=ess,
                   observer_seconds=e['observer_seconds'],snapshot_sha256=saved['sha256']))
            total_bytes+=len(raw)
        rows.append(dict(id=case['id'],events=len(logged),seconds=row['seconds']))
    supported=len(events)>=4 and len({e['game'] for e in events})>=3 and any(e['discarded_fraction']>=.01 for e in events)
    write(OUT/'audit.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,source_frames=frames,cases=rows,
          events=events,total_snapshot_bytes=total_bytes,measure_design_worth_review=supported,
          plan_sha256=sha(OUT/'plan.json'),auditor_sha256=sha(Path(__file__)),scope=plan['scope']))
    print(json.dumps(dict(passed=True,events=len(events),frames=frames,measure_design_worth_review=supported)),flush=True)


if __name__=='__main__':main()
