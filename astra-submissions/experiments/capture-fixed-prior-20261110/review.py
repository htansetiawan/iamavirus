"""Independent scalar constrained-probability and game-cluster aggregation audit."""
from datetime import datetime,timezone
import ctypes
import gzip
import json
import sys
import time
import numpy as np
import torch
from prepare import ROOT,HERE,OUT,library,sha,write
from train import collect,bootstrap
from model import COLUMNS,mask
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref

def main():
    started=time.monotonic();plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    selection=json.loads((OUT/'selection.json').read_text());lock=json.loads((OUT/'selection-lock.json').read_text())
    assert sha(OUT/'selection.json')==lock['sha256']==result['selection_sha256'] and not selection['test_features_opened']
    assert lock['at']<json.loads((OUT/'test-data.json').read_text())['at']
    groups={s:[g for g in plan['games'] if g['split']==s] for s in ('train','validation','test')}
    assert [len(v) for v in groups.values()]==[4000,400,400]
    all_sequences=[]
    for s,games in groups.items():
        low,high,_=plan['windows'][s]
        for g in games:
            assert low<=g['created_at']<high;all_sequences.append(g['sequence_sha256'])
    assert len(all_sequences)==len(set(all_sequences))
    for key,model in selection['selected'].items():
        curves=json.loads((OUT/(key+'-curve.json')).read_text());best=min(curves,key=lambda r:r['validation_nll'])
        assert best['epoch']==model['epoch'] and best['validation_nll']==model['validation_nll']
        q=np.array(model['quadratic']);assert np.array_equal(q,q*mask(model['features']).numpy())
    torch.set_num_threads(2);lib=library();data,meta,receipt=collect(plan,lib,'test',False)
    original=json.loads((OUT/'test-data.json').read_text());assert receipt['unpacked_sha256']==original['unpacked_sha256']
    rows=[json.loads(s) for s in gzip.decompress((OUT/'decisions.jsonl.gz').read_bytes()).splitlines()]
    assert len(rows)==len(meta) and sha(OUT/'decisions.jsonl.gz')==result['scores_sha256']
    worst=0.;captures=0;action_checks=0
    for i,m in enumerate(meta):
        assert all(rows[i][k]==v for k,v in m.items());n=m['n'];x=data['x'][i,:n].numpy().astype(float)
        for F in (14,22):
            base=data['base'][i,:n,0 if F==14 else 1].numpy();top=base.max()
            old_z=np.float32(top+np.float32(np.log(np.exp((base-top).astype(float)).sum())))
            lp0=(base-old_z).astype(float);quiet=x[:,0]==0
            for kind in ('base','linear','quadratic'):
                if kind=='base':lp=lp0.copy()
                else:
                    model=selection['selected'][f'{F}-{kind}'];v=x[:,COLUMNS[:F]];lin=np.array(model['linear'],np.float32).astype(float);q=np.array(model['quadratic'],np.float32).astype(float)
                    d=v@lin+np.einsum('ni,ij,nj->n',v,q,v);lp=lp0.copy()
                    if quiet.sum()>1:
                        before=base[quiet].astype(float);after=before+d[quiet]
                        correction=before.max()+np.log(np.exp(before-before.max()).sum())-after.max()-np.log(np.exp(after-after.max()).sum())
                        lp[quiet]+=d[quiet]+correction
                assert np.array_equal(lp[~quiet],lp0[~quiet]);captures+=int((~quiet).sum());action_checks+=n
                value=lp[m['target']];N=m['history_n'];h=float(data['counts'][i,m['target']])
                if N>=3:value=np.logaddexp(np.log(h) if h else -np.inf,np.log(4.)+value)-np.log(N+4)
                error=abs(value-rows[i]['logp'][str(F)][kind]);worst=max(worst,error);assert error<plan['gate']['capture_logp_tolerance'],(i,F,kind,error)
    frame_checks=0
    buffers=[ctypes.create_string_buffer(65) for _ in range(3)]
    for g in groups['test']:
        board=ref.FowBoard();lib.prior_start()
        for ply in range(len(g['moves'])+1):
            if ply:
                text=g['moves'][ply-1];move=ref.chess.Move.from_uci(text);assert move in ref.fow_moves(board);board.push(move)
                from train import encoded
                assert lib.prior_step(encoded(text))>=0
            side=lib.prior_state(*buffers);assert side==ply%2
            actual=''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
            assert actual==buffers[0].value.decode() and ref.observation(board,True)==buffers[1].value.decode() and ref.observation(board,False)==buffers[2].value.decode();frame_checks+=1
    primary=np.array([r['primary'] for r in rows]);surprise=primary & np.array([r['surprise'] for r in rows]);capture=np.array([r['capture'] for r in rows])
    for F in ('14','22'):
        p={k:np.array([r['logp'][F][k] for r in rows]) for k in ('base','linear','quadratic')}
        gain=p['quadratic']-p['base'];linear=p['quadratic']-p['linear'];saved=result['modes'][F]
        assert np.array_equal(gain[capture],np.zeros(int(capture.sum())))
        for key,value in [('gain',gain[primary].mean()),('matched_linear_gain',linear[primary].mean()),('all_move_gain',gain.mean()),('surprise_gain',gain[surprise].mean())]:assert abs(saved[key]-value)<1e-12
        ci=bootstrap([m for m,ok in zip(meta,primary) if ok],gain[primary],plan['seed'],plan['bootstrap_draws'])
        assert np.allclose(ci,saved['interval95'],rtol=0,atol=1e-12)
    decision='prospective_posterior_design_allowed' if all(c for r in result['modes'].values() for c in r['conditions'].values()) else 'close_capture_fixed_configuration'
    assert decision==result['decision']
    write(OUT/'independent-review.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,scalar_action_checks=action_checks,
          scalar_capture_checks=captures,max_scalar_native_logp_error=worst,course_frames=frame_checks,selection_and_splits_verified=True,
          aggregation_and_bootstraps_verified=True,decision=decision,seconds=time.monotonic()-started,
          scope='Independent NumPy scalar equation, separate course rules over immutable recorded move sequences and result aggregation; '
                'not a new full raw-replay read, independent refit or playing-strength estimate.'))
    print(json.dumps(dict(passed=True,decision=decision,action_checks=action_checks,course_frames=frame_checks,worst=worst)),flush=True)
if __name__=='__main__':main()
