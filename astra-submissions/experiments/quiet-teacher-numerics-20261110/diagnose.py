"""Read-only operator/model diagnosis; no target labels, fitting or qualification."""
from contextlib import nullcontext
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.attention import SDPBackend, sdpa_kernel

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'astra-submissions/analysis/quiet-teacher-numerics-20261110'
sys.path.insert(0, str(ROOT / 'astra-submissions/experiments/world-quiet-attention-20261110'))
from model import WorldQuietTeacher, quiet_logp
from data import CONTEXT, FRAME, PriorCache, Cache


def now(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def save(path, value):
    with Path(path).open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def probe():
    gpu = subprocess.run(['nvidia-smi', '--id=0', '--query-gpu=name,memory.used,utilization.gpu',
                          '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    apps = subprocess.run(['nvidia-smi', '--id=0', '--query-compute-apps=pid,process_name,used_memory',
                           '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    name, memory, util = [part.strip() for part in gpu.split(',')]
    return dict(at=now(), name=name, memory_mib=int(memory), util_percent=int(util), compute_apps=apps,
                free=int(memory) < 2048 and int(util) < 10 and not apps)


def lease(ident, remove=False):
    path = ROOT / 'chatroom/cores.json'
    with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX); state = json.loads(path.read_text())
        if remove: state['allocation'] = [r for r in state['allocation'] if r.get('lease') != ident]
        else:
            assert not any(set(r.get('cores', [])) & {2, 3} or r.get('gpu') == 0 for r in state['allocation'])
            state['allocation'].append(dict(owner='astra', cores=[2, 3], gpu=0, lease=ident,
                purpose='324 bounded unchanged-weight teacher arithmetic diagnosis; no fit or strength scoring'))
        state['updated'] = now(); temp = path.with_name('.cores-' + ident)
        temp.write_text(json.dumps(state, indent=2) + '\n'); os.replace(temp, path)


def load_inputs(plan):
    """Selected old fit-TRAIN inputs only. Never access target, result or flags."""
    prior = PriorCache(plan['feature_cache']); world = Cache(plan['state_cache'])
    contexts = np.frombuffer(prior.contexts, dtype=CONTEXT)
    frames = np.frombuffer(world.data, dtype=FRAME)
    train = set(plan['split']['train'])
    chosen = [i for i, row in enumerate(contexts) if world.games[int(row['game'])]['game'] in train][:390]
    assert chosen == json.loads((OUT / 'plan.json').read_text())['context_indices']
    selected = contexts[chosen]; source = frames[selected['record']]
    pieces = np.empty((390, 64), np.int64)
    pieces[:, 0::2] = source['board'] & 15; pieces[:, 1::2] = source['board'] >> 4
    squares = np.arange(64, dtype=np.uint64)
    visibility = ((source['white'][:, None] >> squares) & 1) | (((source['black'][:, None] >> squares) & 1) << 1)
    board = [pieces, visibility.astype(np.int64), ((source['castle'][:, None] >> squares) & 1).astype(np.int64),
             (source['ep'][:, None] == np.arange(64)[None]).astype(np.int64),
             source['half'].astype(np.float32), source['side'].astype(np.int64)]
    width = prior.manifest['max_width']; valid = np.arange(width)[None] < selected['count'][:, None]
    positions = selected['start'].astype(np.int64)[:, None] + np.minimum(np.arange(width)[None], selected['count'][:, None] - 1)
    rows = prior.rows[positions]
    result = dict(x=np.array(rows['x']), base=np.array(rows['base'][:, :, 1]),
                  counts=rows['history'].astype(np.float32), moves=rows['move'].astype(np.int64),
                  valid=valid, capture=rows['x'][:, :, 0] > 0, history_n=selected['total'].astype(np.float32), board=board)
    # Content receipt excludes stored target, truth-event flags, names and outcome.
    digest = hashlib.sha256()
    for v in board + [result[k] for k in ('x', 'base', 'counts', 'moves', 'valid', 'capture', 'history_n')]:
        digest.update(np.ascontiguousarray(v).tobytes())
    return result, digest.hexdigest()


def convert(inputs, lo, hi, device, dtype):
    def tensor(v):
        t = torch.from_numpy(np.ascontiguousarray(v[lo:hi])).to(device)
        return t.to(dtype) if t.is_floating_point() else t
    return {k: [tensor(v) for v in a] if k == 'board' else tensor(a) for k, a in inputs.items()}


def mode_model(state, architecture, device, mode):
    dtype = torch.float64 if mode == 'math-erf-f64' else torch.float32
    model = WorldQuietTeacher(**architecture).to(device=device, dtype=dtype)
    model.load_state_dict(state); model.eval()
    if mode == 'math-tanh-f32':
        for module in model.modules():
            if isinstance(module, nn.TransformerEncoderLayer):
                module.activation = lambda x: F.gelu(x, approximate='tanh')
                module.activation_relu_or_gelu = 0
    return model, dtype


def error(a, b):
    diff = a.astype(np.float64) - b.astype(np.float64)
    return dict(maximum=float(abs(diff).max(initial=0)), rms=float(np.sqrt(np.mean(diff * diff))))


@torch.no_grad()
def measure(plan):
    original = json.loads(Path(plan['fit_plan']).read_text())
    inputs, input_digest = load_inputs(original)
    state = torch.load(plan['checkpoint'], map_location='cpu', weights_only=True)
    arrays = {}; report = dict(input_sha256=input_digest, operator_probe={}, comparisons={}, operations={})
    torch.set_float32_matmul_precision('highest'); torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    report['runtime'] = dict(torch=torch.__version__, torch_git=torch.version.git_version,
        cuda=torch.version.cuda, matmul_precision=torch.get_float32_matmul_precision(),
        cuda_tf32=torch.backends.cuda.matmul.allow_tf32, cudnn_tf32=torch.backends.cudnn.allow_tf32,
        initial_mha_fastpath=torch.backends.mha.get_fastpath_enabled(),
        precision_environment={k:v for k,v in os.environ.items() if any(s in k for s in ('TF32','FPMATH','FP32_PRECISION'))})
    # Identity GEMM separates GELU semantics from multiplication roundoff.
    for device in ('cpu', 'cuda'):
        x = torch.linspace(-4, 4, 32768, device=device).reshape(256, 128)
        result = torch.ops.aten._addmm_activation.default(torch.zeros(128, device=device), x,
            torch.eye(128, device=device), use_gelu=True)
        ref = {kind: F.gelu(x, approximate=kind) for kind in ('none', 'tanh')}
        report['operator_probe'][device] = {kind: error(result.cpu().numpy(), v.cpu().numpy()) for kind,v in ref.items()}
        arrays['gelu_' + device] = result.cpu().numpy()
    # Each specified implementation is measured once; no best-backend selection.
    for mode in plan['modes']:
        torch.backends.mha.set_fastpath_enabled(mode == 'default-f32')
        for device in ('cpu', 'cuda'):
            model, dtype = mode_model(state, original['architecture'], device, mode)
            for label, lo, hi in plan['batches']:
                batch = convert(inputs, lo, hi, device, dtype)
                context = nullcontext() if mode == 'default-f32' else sdpa_kernel(SDPBackend.MATH)
                with context:
                    if label == 'b256':
                        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
                            residual = model(*batch['board'], batch['moves'], batch['x'])
                        report['operations'][mode + '_' + device] = sorted({event.key for event in prof.key_averages()})
                    else: residual = model(*batch['board'], batch['moves'], batch['x'])
                lp = quiet_logp(batch['base'], residual, batch['valid'], batch['capture'], batch['counts'], batch['history_n'])
                baseline = quiet_logp(batch['base'], torch.zeros_like(residual), batch['valid'], batch['capture'], batch['counts'], batch['history_n'])
                cap = batch['valid'] & batch['capture']
                assert torch.equal(lp[cap], baseline[cap]), 'within-backend capture identity'
                valid = batch['valid']
                prefix = mode + '_' + device + '_' + label
                arrays[prefix + '_residual'] = residual[valid].cpu().numpy()
                arrays[prefix + '_logp'] = lp[valid].cpu().numpy()
                print(json.dumps(dict(stage=prefix, contexts=hi-lo, actions=int(valid.sum()))), flush=True)
            del model
    for label, _, _ in plan['batches']:
        for mode in plan['modes']:
            prefix = mode + '_'; key = mode + '_' + label
            report['comparisons'][key] = {kind:error(arrays[prefix+'cpu_'+label+'_'+kind], arrays[prefix+'cuda_'+label+'_'+kind])
                                         for kind in ('residual', 'logp')}
        for device in ('cpu', 'cuda'):
            for mode in plan['modes'][:-1]:
                key = mode + '_' + device + '_' + label + '_vs_f64_erf'
                report['comparisons'][key] = {kind:error(arrays[mode+'_'+device+'_'+label+'_'+kind], arrays['math-erf-f64_'+device+'_'+label+'_'+kind])
                                             for kind in ('residual', 'logp')}
    for label, _, _ in plan['batches']:
        for device in ('cpu', 'cuda'):
            for reference in ('math-erf-f32', 'math-tanh-f32'):
                key = 'default_' + device + '_' + label + '_vs_' + reference
                report['comparisons'][key] = {kind:error(arrays['default-f32_'+device+'_'+label+'_'+kind], arrays[reference+'_'+device+'_'+label+'_'+kind])
                                             for kind in ('residual', 'logp')}
    np.savez_compressed(OUT / 'arithmetic-arrays.npz', **arrays)
    report['arrays_sha256'] = sha(OUT / 'arithmetic-arrays.npz')
    report['peak_torch_gpu_bytes'] = torch.cuda.max_memory_allocated()
    assert report['peak_torch_gpu_bytes'] < plan['max_gpu_bytes']
    report['checkpoint_unchanged'] = sha(plan['checkpoint']) == plan['dependencies'][plan['checkpoint']]
    assert report['checkpoint_unchanged']
    report['decision'] = 'diagnostic_only_no_model_qualification_or_old_gate_reclassification'
    report['scope'] = plan['scope']; report['at'] = now()
    save(OUT / 'result.json', report)
    print(json.dumps({k:v for k,v in report.items() if k != 'operations'},indent=2), flush=True)


def main():
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixed five-minute diagnosis bound')))
    signal.alarm(300)
    plan = json.loads((OUT / 'plan.json').read_text())
    assert not (OUT / 'runner-execution.json').exists()
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    checks = [probe()]
    if checks[0]['free']: time.sleep(5); checks.append(probe())
    save(OUT / 'gpu-admission.json', dict(checks=checks, services_stopped=False))
    if len(checks) != 2 or not all(c['free'] for c in checks):
        print('GPU busy; no inference attempted'); return
    ident = uuid.uuid4().hex; lease(ident); started = time.monotonic()
    execution = dict(status='running', started_at=now(), lease=ident, source_publication=os.environ['ASTRA_SOURCE_PUBLICATION'])
    save(OUT / 'started.json', execution)
    try:
        os.sched_setaffinity(0,{2,3}); torch.set_num_threads(2); measure(plan)
        execution.update(status='complete')
    except BaseException as exc:
        execution.update(status='failed', error=repr(exc)); raise
    finally:
        lease(ident, remove=True); execution.update(ended_at=now(), seconds=time.monotonic()-started, own_lease_released=True)
        save(OUT / 'runner-execution.json', execution)
    assert sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()) < plan['max_output_bytes']


if __name__ == '__main__': main()
