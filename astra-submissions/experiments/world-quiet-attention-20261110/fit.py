"""One frozen development fit with matched controls; not an arena candidate."""
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

import numpy as np
import torch
from torch import nn

from data import Dataset, ROOT
from model import WorldQuietTeacher, quiet_logp

OUT = ROOT / 'astra-submissions/analysis/world-quiet-fit-20261110'
OLD = ROOT / 'astra-submissions/experiments/capture-fixed-prior-20261110/model.py'
spec = importlib.util.spec_from_file_location('original293model', OLD)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)


def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def save(p, value):
    p = Path(p); temporary = p.with_name('.' + p.name + '-tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n'); os.replace(temporary, p)


class ScalarResidual(nn.Module):
    def __init__(self, kind):
        super().__init__()
        self.linear = nn.Parameter(torch.zeros(22))
        self.quadratic = nn.Parameter(torch.zeros(22, 22), requires_grad=kind == 'quadratic')
        self.register_buffer('mask', old.mask(22))

    def forward(self, batch):
        x = batch['x'][:, :, old.COLUMNS]
        return x @ self.linear + ((x @ (self.quadratic * self.mask)) * x).sum(-1)


def prediction(kind, model, batch):
    if kind == 'base': residual = torch.zeros_like(batch['base'])
    elif kind == 'teacher': residual = model(*batch['board'], batch['moves'], batch['x'])
    else: residual = model(batch)
    return quiet_logp(batch['base'], residual, batch['valid'], batch['capture'], batch['counts'], batch['history_n'])


@torch.no_grad()
def evaluate(dataset, indices, kind, model, batch_size=256):
    if model is not None: model.eval()
    values = []; capture_actions = 0
    for start in range(0, len(indices), batch_size):
        batch = dataset.batch(indices[start:start + batch_size])
        lp = prediction(kind, model, batch)
        original = prediction('base', None, batch)
        capture = batch['valid'] & batch['capture']
        assert torch.equal(lp[capture], original[capture]), 'capture likelihood changed'
        capture_actions += int(capture.sum())
        target = lp.gather(1, batch['y'][:, None]).squeeze(1)
        assert torch.isfinite(target).all()
        values.append(target.cpu().numpy().astype(float))
    return np.concatenate(values), capture_actions


def bootstrap(meta, delta, seed, draws):
    grouped = {}
    for row, value in zip(meta, delta):
        item = grouped.setdefault(row['game'], [0., 0]); item[0] += float(value); item[1] += 1
    values = np.array([grouped[k] for k in sorted(grouped)])
    rng = np.random.default_rng(seed); output = []
    for _ in range(draws):
        sample = values[rng.integers(len(values), size=len(values))]
        output.append(sample[:, 0].sum() / sample[:, 1].sum())
    return np.quantile(output, [.025, .975]).tolist()


def summarize(plan, meta, predictions):
    primary = np.array([r['primary'] for r in meta]); capture = np.array([r['capture'] for r in meta])
    gain = predictions['teacher'] - predictions['base']
    quadratic_gain = predictions['teacher'] - predictions['quadratic']
    selected = [r for r, keep in zip(meta, primary) if keep]
    priority = {}
    for name in plan['priority']:
        mask = primary & np.array([r['team'] == name for r in meta])
        priority[name] = dict(games=len({r['game'] for r, keep in zip(meta, mask) if keep}),
                              decisions=int(mask.sum()), gain=float(gain[mask].mean()) if mask.any() else 0.)
    metrics = dict(primary=int(primary.sum()), capture_targets=int(capture.sum()),
                   nll={k: float(-v[primary].mean()) for k, v in predictions.items()},
                   gain=float(gain[primary].mean()), matched_quadratic_gain=float(quadratic_gain[primary].mean()),
                   interval95_vs_quadratic=bootstrap(selected, quadratic_gain[primary], plan['seed'], plan['bootstrap_draws']),
                   all_move_gain=float(gain.mean()), capture_target_error=float(abs(gain[capture]).max(initial=0)), priority=priority)
    gate = plan['gate']
    conditions = dict(primary_count=metrics['primary'] >= gate['primary_min'],
                      native_gain=metrics['gain'] >= gate['native_gain'],
                      matched_quadratic=metrics['matched_quadratic_gain'] >= gate['quadratic_gain'],
                      confidence=metrics['interval95_vs_quadratic'][0] > 0,
                      all_moves=metrics['all_move_gain'] >= 0,
                      capture_identity=metrics['capture_target_error'] == 0,
                      capture_coverage=metrics['capture_targets'] >= gate['capture_min'],
                      priority_coverage=all(v['games'] >= gate['priority_games'] for v in priority.values()),
                      priority_nonregression=all(v['gain'] >= 0 for v in priority.values()))
    return metrics, conditions


def train(plan, dataset, kind, baseline):
    torch.manual_seed(plan['seed'])
    generator = torch.Generator().manual_seed(plan['seed'])
    model = (WorldQuietTeacher(**plan['architecture']) if kind == 'teacher' else ScalarResidual(kind)).to(dataset.device)
    recipe = plan['teacher'] if kind == 'teacher' else plan['scalar']
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = (torch.optim.AdamW(params, lr=recipe['learning_rate'], weight_decay=recipe['weight_decay'])
                 if kind == 'teacher' else torch.optim.Adam(params, lr=recipe['learning_rate']))
    dev = dataset.indices['development']; primary = np.array([dataset.meta[i]['primary'] for i in dev])
    best_nll = float(-baseline[primary].mean()); best_epoch = 0
    best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    curve = [dict(epoch=0, primary_nll=best_nll)]
    started = time.monotonic()
    for epoch in range(1, recipe['epochs'] + 1):
        order = torch.randperm(len(dataset.indices['train']), generator=generator).numpy()
        shuffled = dataset.indices['train'][order]; model.train(); total = count = 0
        for start in range(0, len(shuffled), recipe['batch']):
            batch = dataset.batch(shuffled[start:start + recipe['batch']])
            lp = prediction(kind, model, batch).gather(1, batch['y'][:, None]).squeeze(1)
            loss = -lp.mean()
            if kind != 'teacher':
                loss = loss + recipe['ridge'] * (model.linear.square().sum() + (model.quadratic * model.mask).square().sum())
            assert torch.isfinite(loss)
            optimizer.zero_grad(set_to_none=True); loss.backward()
            assert all(p.grad is None or torch.isfinite(p.grad).all() for p in params)
            if kind == 'teacher': nn.utils.clip_grad_norm_(params, recipe['clip'])
            optimizer.step(); total += float(loss.detach()) * len(lp); count += len(lp)
        values, _ = evaluate(dataset, dev, kind, model, recipe['batch'])
        nll = float(-values[primary].mean())
        if nll < best_nll:
            best_nll = nll; best_epoch = epoch
            best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        row = dict(epoch=epoch, primary_nll=nll, training_objective=total / count, seconds=time.monotonic()-started)
        curve.append(row); save(OUT / (kind + '-curve.json'), curve)
        print(json.dumps(dict(kind=kind, **row)), flush=True)
        assert torch.cuda.max_memory_allocated() <= plan['max_gpu_bytes'], 'GPU allocation bound'
    torch.save(best, OUT / (kind + '-best.pt'))
    assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) <= plan['max_output_bytes'], 'output bound'
    model.load_state_dict(best)
    values, capture_actions = evaluate(dataset, dev, kind, model)
    del model, optimizer
    torch.cuda.empty_cache()
    return values, dict(kind=kind, best_epoch=best_epoch, primary_nll=best_nll,
                        checkpoint_sha256=sha(OUT / (kind + '-best.pt')), capture_actions_verified=capture_actions)


def main():
    plan = read(OUT / 'plan.json')
    assert not (OUT / 'execution.json').exists(), 'fit already attempted'
    for path, expected in plan['dependencies'].items(): assert sha(path) == expected, path
    assert torch.cuda.is_available(), 'GPU unavailable; leave other services alone'
    os.sched_setaffinity(0, set(plan['cores'])); torch.set_num_threads(2)
    torch.set_float32_matmul_precision('highest')
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('20-minute fit cap')))
    signal.alarm(plan['max_seconds'])
    started = time.monotonic()
    execution = dict(status='running', started_at=now(), pid=os.getpid(), plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / 'execution.json', execution)
    try:
        dataset = Dataset(plan, 'cuda:0'); dev = dataset.indices['development']
        meta = [dataset.meta[i] for i in dev]
        predictions = {}; predictions['base'], capture_checks = evaluate(dataset, dev, 'base', None)
        selection = {}
        for kind in ('linear', 'quadratic', 'teacher'):
            execution.update(phase=kind, updated_at=now()); save(OUT / 'execution.json', execution)
            predictions[kind], selection[kind] = train(plan, dataset, kind, predictions['base'])
        save(OUT / 'selection.json', dict(selected=selection, plan_sha256=sha(OUT / 'plan.json')))
        metrics, conditions = summarize(plan, meta, predictions)
        with gzip.open(OUT / 'development-scores.jsonl.gz', 'xt') as stream:
            for i, row in enumerate(meta):
                stream.write(json.dumps(dict(**row, logp={k: float(v[i]) for k, v in predictions.items()})) + '\n')
        result = dict(at=now(), metrics=metrics, conditions=conditions, selection=selection,
                      decision='fresh_confirmation_design_allowed' if all(conditions.values()) else 'close_frozen_world_quiet_teacher',
                      plan_sha256=sha(OUT / 'plan.json'), scores_sha256=sha(OUT / 'development-scores.jsonl.gz'),
                      capture_actions_verified=capture_checks, max_gpu_bytes=torch.cuda.max_memory_allocated(),
                      scope=plan['scope'])
        save(OUT / 'result.json', result); execution.update(status='complete', phase='fit_complete', decision=result['decision'])
        assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) <= plan['max_output_bytes'], 'output bound'
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as error:
        execution.update(status='failed', error=repr(error)); raise
    finally:
        signal.alarm(0); execution.update(ended_at=now(), seconds=time.monotonic()-started)
        save(OUT / 'execution.json', execution)


if __name__ == '__main__': main()
