"""Measure the retained teacher on CPU; no model or gate changes."""
import json
from pathlib import Path
import sys
import time
import statistics

import numpy as np
import torch
from torch import nn
import onnxruntime as ort

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'astra-submissions/experiments/native-fow-value-20261102'
sys.path.insert(0,str(SOURCE))
from data import OUT,sha,now,write_new
from models import Teacher


class ExportTeacher(nn.Module):
    def __init__(self,model):super().__init__();self.model=model
    def forward(self,x,half):
        m=self.model
        z=m.piece(x[:,:,0])+m.vision(x[:,:,1]+2*x[:,:,2])+m.castle(x[:,:,3])+m.ep(x[:,:,4])
        z=z+m.square(torch.arange(64,device=x.device))[None,:,:]
        # Symbolic batch dimension instead of Python len used by training code.
        global_=m.global_token.expand(x.shape[0],-1,-1)+m.half_projection(half[:,None,None]/100)
        z=m.transformer(torch.cat([global_,z],dim=1))
        return m.head(z[:,0]).squeeze(-1)


def main():
    torch.set_num_threads(2);torch.backends.mha.set_fastpath_enabled(False)
    path=SOURCE/'work/training/teacher.pt';selected=json.loads((OUT/'selection.json').read_text())
    assert sha(path)==selected['teacher']['sha256']
    m=Teacher().eval();m.load_state_dict(torch.load(path,map_location='cpu',weights_only=True));wrapper=ExportTeacher(m).eval()
    with np.load(SOURCE/'work/dataset/data.npz') as d:x=d['x'][:64].astype(np.int64);h=d['half'][:64].astype(np.float32)
    with torch.no_grad():
        original=m(torch.from_numpy(x),torch.from_numpy(h)).numpy()
        exported=wrapper(torch.from_numpy(x),torch.from_numpy(h)).numpy()
    assert np.array_equal(original,exported)
    dest=SOURCE/'work/training/teacher.onnx';assert not dest.exists()
    torch.onnx.export(wrapper,(torch.from_numpy(x[:2]),torch.from_numpy(h[:2])),str(dest),
        input_names=['board_tokens','halfmove'],output_names=['logit'],
        dynamic_axes={'board_tokens':{0:'batch'},'halfmove':{0:'batch'},'logit':{0:'batch'}},
        opset_version=17,dynamo=False)
    options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
    options.graph_optimization_level=ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    begin=time.perf_counter();session=ort.InferenceSession(str(dest),options,providers=['CPUExecutionProvider']);loadtime=time.perf_counter()-begin
    samples={};errors={}
    for n in (1,32,64):
        inp={'board_tokens':x[:n],'halfmove':h[:n]}
        for _ in range(3):out=session.run(None,inp)[0]
        errors[n]=float(np.max(np.abs(out-original[:n])));assert errors[n]<2e-5
        times=[]
        for _ in range(20):
            begin=time.perf_counter();session.run(None,inp);times.append(1e6*(time.perf_counter()-begin))
        samples[n]=dict(batch_microseconds_median=statistics.median(times),
            per_position_microseconds_median=statistics.median(times)/n,all_batch_microseconds=times)
    result=dict(at=now(),onnx_bytes=dest.stat().st_size,onnx_sha256=sha(dest),teacher_sha256=sha(path),
        onnxruntime=ort.__version__,load_seconds=loadtime,threads=2,samples=samples,
        max_logit_error_by_batch=errors,source_sha256=sha(__file__),
        scope='First64training inputs, CPU-only dynamic-batch export and timing. Exact model weights; export-only symbolic batch wrapper equals training forward. No quality tuning, new gate, search integration or playing result. Does not include board encoding or engine scheduling.')
    write_new(OUT/'teacher-runtime.json',result);print(json.dumps(result))


if __name__=='__main__':main()
