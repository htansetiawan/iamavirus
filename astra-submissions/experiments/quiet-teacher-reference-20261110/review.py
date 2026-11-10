"""Independent raw-array, source, traversal and arithmetic audit. No inference."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/quiet-teacher-reference-20261110'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    plan=json.loads((OUT/'plan.json').read_text());result=json.loads((OUT/'result.json').read_text())
    for path,expected in plan['dependencies'].items():assert sha(path)==expected,path
    fit=json.loads(Path(plan['fit_plan']).read_text());world=Path(fit['state_cache']);prior=Path(fit['feature_cache'])
    games=json.loads((world/'games.json').read_text());train=set(fit['split']['train'])
    context=list(struct.Struct('<QIIHHHBB').iter_unpack((prior/'contexts.bin').read_bytes()))
    indices=np.array([i for i,r in enumerate(context) if games[r[5]]['game'] in train],dtype=np.int64)
    assert len(indices)==plan['train_contexts']==result['train_contexts']
    assert hashlib.sha256(indices.astype('<i8').tobytes()).hexdigest()==plan['train_context_indices_sha256']
    private=OUT/'private';receipts=json.loads((private/'batch-receipts.json').read_text())
    assert sha(private/'batch-receipts.json')==result['batch_receipts_sha256']
    assert sha(private/'canonical.npy')==result['canonical_sha256']
    canonical=np.load(private/'canonical.npy',mmap_mode='r',allow_pickle=False)
    dtype=np.dtype([('x','<f4',(26,)),('base','<f4',(2,)),('history','<u4'),('move','<u2'),('surprise','u1'),('reserved','u1')])
    rows=np.memmap(prior/'candidates.bin',dtype=dtype,mode='r');assert dtype.itemsize==120
    maxima={k:0. for k in ('cpu_gpu_residual','cpu_gpu_logp','batch_residual','batch_logp')}
    counts={};caps={};receipt_index=0;scalar_values=0
    for width in plan['full_pass_batch_sizes']+[1]:
        selected=indices if width!=1 else indices[np.asarray(plan['singleton_offsets'])]
        name='b'+str(width);counts[name]=0;caps[name]=0
        for index,start in enumerate(range(0,len(selected),width)):
            expected=selected[start:start+width];receipt=receipts[receipt_index];receipt_index+=1
            assert (receipt['name'],receipt['index'],receipt['contexts'])==(name,index,len(expected))
            path=private/receipt['file'];assert sha(path)==receipt['sha256']
            with np.load(path,allow_pickle=False) as raw:
                assert np.array_equal(raw['indices'],expected)
                positions=np.concatenate([np.arange(context[i][0],context[i][0]+context[i][4]) for i in expected])
                assert np.array_equal(raw['positions'],positions)
                assert receipt['actions']==len(positions)
                capture=rows['x'][positions,0]>0
                assert np.array_equal(raw['cpu_capture'],capture) and np.array_equal(raw['cuda_capture'],capture)
                for device in ('cpu','cuda'):
                    assert np.array_equal(raw[device+'_logp'][capture],raw[device+'_baseline'][capture])
                for column,kind in enumerate(('residual','logp')):
                    a=raw['cpu_'+kind].astype(np.float64);b=raw['cuda_'+kind].astype(np.float64)
                    assert a.shape==b.shape==(len(positions),) and np.isfinite(a).all() and np.isfinite(b).all()
                    # Independently compute max through separate reductions.
                    maximum=float(max((a-b).max(initial=0),(b-a).max(initial=0)))
                    maxima['cpu_gpu_'+kind]=max(maxima['cpu_gpu_'+kind],maximum)
                    old=canonical[positions,column].astype(np.float64);assert np.isfinite(old).all()
                    if width==plan['full_pass_batch_sizes'][0]:assert np.array_equal(a,old)
                    else:maxima['batch_'+kind]=max(maxima['batch_'+kind],float(abs(a-old).max(initial=0)))
                    scalar_values+=len(positions)
                counts[name]+=len(positions);caps[name]+=int(capture.sum())
    assert receipt_index==len(receipts)==result['private_files']
    assert counts==result['actions'] and caps==result['capture_actions']
    for key,value in maxima.items():assert value==result['maximum_errors'][key] and value<plan['tolerance'],key
    assert result['float64_grad_reference_error']<plan['float64_tolerance']
    assert all(v<plan['tolerance'] for k,v in result['maximum_errors'].items() if k.startswith('diagnostic'))
    assert result['unchanged_checkpoint'] and result['global_mha_flag_unchanged']
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,source_pins=len(plan['dependencies']),
        train_contexts=len(indices),raw_batch_files=len(receipts),scalar_values_per_side_verified=scalar_values,
        maximum_errors=maxima,actions=counts,capture_actions=caps,result_sha256=sha(OUT/'result.json'),
        limitation='Independent decoding/traversal, stored-array comparisons, scalar maxima, source hashes and capture checks; no independent attention implementation or new inference. Grad-FP64 and operator assertions come from the original run. Private arrays remain local and are excluded from publication.')
    with (OUT/'independent-review.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
