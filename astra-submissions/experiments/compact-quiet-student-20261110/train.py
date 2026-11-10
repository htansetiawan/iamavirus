"""One compact opponent-prior development fit with a matched hard-label arm."""
from contextlib import contextmanager
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import torch

from student import CompactQuietPrior, quiet_kl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ATTENTION = HERE.parent/'world-quiet-attention-20261110'
REFERENCE = HERE.parent/'quiet-teacher-reference-20261110'
ANALYSIS = ROOT/'astra-submissions/analysis'
OUT = ANALYSIS/HERE.name
ORIGINAL_FIT = ANALYSIS/'world-quiet-fit-20261110/plan.json'
CONFIRMATION = ANALYSIS/'prospective-quiet-teacher-20261110'
STORE = ROOT/'data/astra-spool'/HERE.name
OWNER = 'astra-'+HERE.name
sys.path[:0] = [str(ATTENTION),str(REFERENCE)]
from fit import Dataset, ScalarResidual, WorldQuietTeacher, bootstrap, evaluate, quiet_logp
from reference import forward as teacher_forward


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def normalize(batch, residual):
    return quiet_logp(batch['base'],residual,batch['valid'],batch['capture'],batch['counts'],batch['history_n'])


def freeze():
    proof = read(CONFIRMATION/'terminal-verification.json')
    result = read(CONFIRMATION/'result.json')
    assert proof['conditions_passed']==12 and result['decision']=='distillation_design_allowed'
    assert proof['result_sha256']==sha(CONFIRMATION/'result.json')
    old = read(ORIGINAL_FIT)
    confirmed = read(CONFIRMATION/'plan.json')
    assert all(sha(path)==confirmed['dependencies'][path] for path in confirmed['weights'].values())
    deps = [Path(__file__),HERE/'student.py',ATTENTION/'fit.py',ATTENTION/'data.py',ATTENTION/'model.py',
        REFERENCE/'reference.py',ORIGINAL_FIT,CONFIRMATION/'result.json',CONFIRMATION/'terminal-verification.json',
        CONFIRMATION/'plan.json',*map(Path,confirmed['weights'].values())]
    for folder,names in ((Path(old['state_cache']),('manifest.json','records.bin','games.json')),
                         (Path(old['feature_cache']),('manifest.json','contexts.bin','candidates.bin'))):
        deps.extend(folder/name for name in names)
    deps.extend(ROOT/'astra-submissions/tools'/name for name in ('reconstructed_cache.py','prior_training_cache.py','experience_index.py'))
    deps.append(HERE.parent/'capture-fixed-prior-20261110/model.py')
    plan = dict(at=now(), rank=16, seed=3401110, epochs=12, batch=256, learning_rate=.001,
        weight_decay=.0001, teacher_weight=.75, cores=[2,3], fit_seconds=900,
        max_gpu_bytes=8*1024**3, max_private_bytes=128*1024**2,
        teacher_weights=confirmed['weights']['teacher'], teacher_architecture=confirmed['architecture'],
        comparator_weights={name:confirmed['weights'][name] for name in ('quadratic','production')},
        gates=dict(native_gain=.075,quadratic_gain=.03,production_gain=.03,
            primary_min=5000,priority_games_min=20,numeric_tolerance=.0001),
        reused_training_games=len(old['split']['train']), reused_development_games=len(old['split']['development']),
        scope='One paired development fit on the old 3500/500 split. Fixed 326 teacher and controls. The sealed future cohort is reserved as prior teacher evidence.',
        dependencies={str(path):sha(path) for path in deps})
    OUT.mkdir(exist_ok=False)
    save(OUT/'plan.json', plan)
    print(json.dumps(dict(pins=len(deps),plan_sha256=sha(OUT/'plan.json'))),flush=True)


def load_plan():
    plan = read(OUT/'plan.json')
    for path,digest in plan['dependencies'].items():
        assert sha(path)==digest, path
    return plan


def preflight():
    plan = load_plan()
    torch.set_num_threads(2)
    torch.manual_seed(plan['seed'])
    dataset = Dataset(read(ORIGINAL_FIT),'cpu')
    batch = dataset.batch(dataset.indices['train'][:128])
    model = CompactQuietPrior(plan['rank'])
    initial = normalize(batch,model(batch))
    assert torch.equal(initial,normalize(batch,torch.zeros_like(batch['base'])))
    for table in (model.source,model.target,model.promotion,model.move_features):
        torch.nn.init.normal_(table.weight,std=.02)
    value = model(batch)
    order = torch.randperm(batch['moves'].shape[1])
    shuffled = dict(batch, moves=batch['moves'][:,order],x=batch['x'][:,order])
    assert torch.allclose(model(shuffled),value[:,order],atol=1e-6,rtol=0)
    piece, visibility, castle, ep, halfmove, side = batch['board']
    reverse = torch.arange(64)^56
    pieces = torch.where(piece==0,0,(piece+5)%12+1)
    views = ((visibility&1)<<1) | (visibility>>1)
    reflected = dict(batch, board=[pieces[:,reverse],views[:,reverse],castle[:,reverse],ep[:,reverse],halfmove,side^1],
                     moves=batch['moves']^(56|(56<<6)))
    assert torch.equal(model(reflected),value)
    lp = normalize(batch,value)
    capture = batch['valid'] & batch['capture']
    assert torch.equal(lp[capture],initial[capture])
    loss = quiet_kl(initial,lp,batch['valid'] & ~batch['capture'])
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    result = dict(passed=True,contexts=128,parameters=sum(p.numel() for p in model.parameters()),
        capture_checks=int(capture.sum()),zero_residual_identity=True,candidate_order_parity=True,color_reflection_parity=True,
        finite_gradients=True,plan_sha256=sha(OUT/'plan.json'))
    save(OUT/'preflight.json',result)
    print(json.dumps(result),flush=True)


@contextmanager
def reservation(cores):
    path = ROOT/'chatroom/cores.json'
    def change(take):
        with Path('/tmp/iamavirus-cores-json.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert all(not set(cores)&set(row['cores']) for row in state['allocation'])
                state['allocation'].append(dict(owner=OWNER,cores=cores,pid=os.getpid(),at=now(),
                    purpose='bounded compact prior training and CPU comparison'))
            else:
                state['allocation'] = [row for row in state['allocation'] if row['owner']!=OWNER]
            state['updated'] = now()
            save(path,state)
    with Path('/tmp/iamavirus-gpu.lock').open('a') as gpu:
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for attempt in range(2):
            snapshot = subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu',
                '--format=csv,noheader,nounits'],text=True,timeout=15).strip().splitlines()
            assert len(snapshot)==1
            used,busy = map(int,snapshot[0].split(','))
            clients = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid',
                '--format=csv,noheader'],text=True,timeout=15).strip()
            assert used<2000 and busy==0 and not clients, 'GPU is occupied'
            if attempt==0:
                time.sleep(2)
        change(True)
        try:
            yield
        finally:
            change(False)


@torch.no_grad()
def teacher_targets(plan, dataset):
    teacher = WorldQuietTeacher(**plan['teacher_architecture']).to(dataset.device).eval()
    teacher.load_state_dict(torch.load(plan['teacher_weights'],map_location='cpu',weights_only=True))
    targets = torch.empty((len(dataset.context),len(dataset.offsets)),device=dataset.device)
    for start in range(0,len(dataset.context),plan['batch']):
        indices = np.arange(start,min(start+plan['batch'],len(dataset.context)))
        batch = dataset.batch(indices)
        lp = normalize(batch,teacher_forward(teacher,*batch['board'],batch['moves'],batch['x']))
        capture = batch['valid'] & batch['capture']
        assert torch.equal(lp[capture],normalize(batch,torch.zeros_like(batch['base']))[capture])
        targets[start:start+len(indices)] = lp
    return targets


def train_arm(plan, dataset, targets, mode, baseline, primary):
    torch.manual_seed(plan['seed'])
    generator = torch.Generator().manual_seed(plan['seed'])
    model = CompactQuietPrior(plan['rank']).to(dataset.device)
    optimizer = torch.optim.AdamW(model.parameters(),lr=plan['learning_rate'],weight_decay=plan['weight_decay'])
    train = dataset.indices['train']
    development = dataset.indices['development']
    best = {key:value.detach().cpu().clone() for key,value in model.state_dict().items()}
    best_loss = -baseline[primary].mean()
    best_epoch = 0
    curve = []
    weight = plan['teacher_weight'] if mode=='distilled' else 0.
    for epoch in range(1,plan['epochs']+1):
        model.train()
        shuffled = train[torch.randperm(len(train),generator=generator).numpy()]
        for start in range(0,len(shuffled),plan['batch']):
            indices = shuffled[start:start+plan['batch']]
            batch = dataset.batch(indices)
            lp = normalize(batch,model(batch))
            loss = -(1-weight)*lp.gather(1,batch['y'][:,None]).mean()
            if weight:
                wanted = targets[torch.as_tensor(indices,device=dataset.device)]
                loss = loss + weight*quiet_kl(wanted,lp,batch['valid'] & ~batch['capture'])
            assert torch.isfinite(loss)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
            optimizer.step()
        values,_ = evaluate(dataset,development,'student',model,plan['batch'])
        current = float(-values[primary].mean())
        if current<best_loss:
            best_loss,best_epoch = current,epoch
            best = {key:value.detach().cpu().clone() for key,value in model.state_dict().items()}
        curve.append(dict(epoch=epoch,primary_nll=current))
        print(json.dumps(dict(arm=mode,epoch=epoch,primary_nll=current)),flush=True)
        assert torch.cuda.max_memory_allocated()<=plan['max_gpu_bytes']
    path = STORE/(mode+'.pt')
    torch.save(best,path)
    model.load_state_dict(best)
    values,checks = evaluate(dataset,development,'student',model,plan['batch'])
    cpu = CompactQuietPrior(plan['rank']).eval()
    cpu.load_state_dict(best)
    model.eval()
    max_error = 0.
    with torch.no_grad():
        for start in range(0,len(development),plan['batch']):
            batch = dataset.batch(development[start:start+plan['batch']])
            copy = {k:(v.cpu() if k!='board' else [item.cpu() for item in v]) for k,v in batch.items()}
            expected = normalize(copy,cpu(copy))
            actual = normalize(batch,model(batch)).cpu()
            valid = copy['valid']
            max_error = max(max_error,float((expected[valid]-actual[valid]).abs().max()))
    return values,dict(best_epoch=best_epoch,nll=float(best_loss),curve=curve,
        checkpoint_sha256=sha(path),exact_capture_checks=checks,max_cpu_gpu_error=max_error)


def execute(plan):
    old = read(ORIGINAL_FIT)
    dataset = Dataset(old,'cuda:0')
    development = dataset.indices['development']
    metadata = [dataset.meta[index] for index in development]
    primary = np.array([row['primary'] for row in metadata])
    predictions = {}
    predictions['base'],_ = evaluate(dataset,development,'base',None)
    for name,path in plan['comparator_weights'].items():
        model = ScalarResidual('quadratic').to(dataset.device).eval()
        if name=='quadratic':
            model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True))
        else:
            weights = read(path)
            with torch.no_grad():
                model.linear.copy_(torch.tensor(weights['linear']))
                model.quadratic.copy_(torch.tensor(weights['quadratic']))
        predictions[name],_ = evaluate(dataset,development,'quadratic',model)
    targets = teacher_targets(plan,dataset)
    predictions['teacher'] = np.concatenate([
        targets[torch.as_tensor(development[start:start+plan['batch']],device=dataset.device)]
            .gather(1,dataset.batch(development[start:start+plan['batch']])['y'][:,None]).flatten().cpu().numpy()
        for start in range(0,len(development),plan['batch'])])
    receipts = {}
    for mode in ('hard','distilled'):
        predictions[mode],receipts[mode] = train_arm(plan,dataset,targets,mode,predictions['base'],primary)
    nll = {k:float(-v[primary].mean()) for k,v in predictions.items()}
    gains = {k:nll[k]-nll['distilled'] for k in ('base','quadratic','production','hard')}
    difference = predictions['distilled']-predictions['production']
    interval = bootstrap([row for row in metadata if row['primary']],difference[primary],plan['seed'],2000)
    priority = {}
    for name in old['priority']:
        mask = primary & np.array([row['team']==name for row in metadata])
        priority[name] = dict(games=len({row['game'] for row,keep in zip(metadata,mask) if keep}),
            gain=float((predictions['distilled'][mask]-predictions['base'][mask]).mean()) if mask.any() else 0.)
    g = plan['gates']
    conditions = dict(native=gains['base']>=g['native_gain'],quadratic=gains['quadratic']>=g['quadratic_gain'],
        production=gains['production']>=g['production_gain'],hard_label_control=gains['hard']>=0,
        confidence=interval[0]>0,primary=int(primary.sum())>=g['primary_min'],
        all_moves=float((predictions['distilled']-predictions['base']).mean())>=0,
        priorities=all(v['games']>=g['priority_games_min'] and v['gain']>=0 for v in priority.values()),
        numeric=all(r['max_cpu_gpu_error']<g['numeric_tolerance'] for r in receipts.values()))
    np.savez_compressed(STORE/'development-logp.npz',**predictions)
    assert sum(path.stat().st_size for path in STORE.iterdir())<=plan['max_private_bytes']
    return dict(at=now(),primary=int(primary.sum()),nll=nll,gains=gains,priority=priority,
        production_gain_interval95=interval,conditions=conditions,arms=receipts,
        decision='qualify_independent_student_test' if all(conditions.values()) else 'close_student_configuration',
        max_gpu_bytes=torch.cuda.max_memory_allocated(),plan_sha256=sha(OUT/'plan.json'))


def fit():
    plan = load_plan()
    preflight = read(OUT/'preflight.json')
    assert preflight['passed'] and preflight['plan_sha256']==sha(OUT/'plan.json')
    assert not (OUT/'execution.json').exists()
    with reservation(plan['cores']):
        os.sched_setaffinity(0,set(plan['cores']))
        torch.set_num_threads(2)
        torch.set_float32_matmul_precision('highest')
        assert torch.cuda.is_available()
        STORE.mkdir(parents=True,exist_ok=False)
        start = time.monotonic()
        state = dict(status='running',started_at=now(),plan_sha256=sha(OUT/'plan.json'))
        save(OUT/'execution.json',state)
        def deadline(*_):
            raise TimeoutError('compact prior development fit wall cap')
        signal.signal(signal.SIGALRM,deadline)
        signal.alarm(plan['fit_seconds'])
        try:
            result = execute(plan)
            save(OUT/'result.json',result)
            state.update(status='complete',decision=result['decision'])
            print(json.dumps(result),flush=True)
        except BaseException as error:
            state.update(status='failed',error=repr(error))
            raise
        finally:
            signal.alarm(0)
            state.update(ended_at=now(),seconds=time.monotonic()-start)
            save(OUT/'execution.json',state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=('freeze','preflight','fit'))
    globals()[parser.parse_args().action]()
