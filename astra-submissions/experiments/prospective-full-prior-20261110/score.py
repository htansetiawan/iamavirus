"""Score all frozen models once, only after the prospective cohort is sealed."""
import gzip
import json
import os
import signal
import sys
import time
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from protocol import ROOT, OUT, OLD, OLD_OUT, PRIORITY, now, sha, write, check_pins, gate_result
sys.path.insert(0, str(OLD))
import numpy as np
import torch
from prepare import library
from train import collect, native_score, bootstrap


def summarize(meta, prediction, checks, plan):
    primary = np.array([m['primary'] for m in meta])
    capture = np.array([m['capture'] for m in meta])
    surprise = primary & np.array([m['surprise'] for m in meta])
    assert primary.any()
    gain = prediction['quadratic'] - prediction['base']
    linear = prediction['quadratic'] - prediction['linear']
    pm = [m for m, selected in zip(meta, primary) if selected]
    priorities = {}
    for team in PRIORITY:
        mask = primary & np.array([m['team_id'] == team for m in meta])
        priorities[team] = dict(games=len({m['game'] for m, selected in zip(meta, mask) if selected}),
                                decisions=int(mask.sum()), gain=float(gain[mask].mean()) if mask.any() else 0.)
    return dict(primary=int(primary.sum()), nll={k:float(-p[primary].mean()) for k,p in prediction.items()},
                gain=float(gain[primary].mean()),
                interval95=bootstrap(pm, gain[primary], plan['seed'], plan['bootstrap_draws']),
                matched_linear_gain=float(linear[primary].mean()), all_move_gain=float(gain.mean()),
                surprise_captures=int(surprise.sum()),
                capture_target_error=float(abs(gain[capture]).max(initial=0)),
                capture_action_error=max(v['capture_logp_error'] for v in checks.values()),
                priority=priorities)


def main():
    started = time.monotonic()
    plan = json.loads((OUT / 'plan.json').read_text())
    cohort = json.loads((OUT / 'cohort.json').read_text())
    state = json.loads((OUT / 'execution.json').read_text())
    assert state['status'] == 'complete' and state['phase'] == 'sealed'
    assert state['cohort_sha256'] == sha(OUT / 'cohort.json')
    assert cohort['no_models_or_predictions_opened']
    assert len(cohort['games']) == plan['games']
    assert not (OUT / 'result.json').exists(), 'no repeat scoring/selection'
    check_pins(plan)
    os.sched_setaffinity(0, set(plan['cores']))
    torch.set_num_threads(2)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('30-minute scoring bound')))
    signal.alarm(1800)
    receipt = dict(started_at=now(), status='running', cohort_sha256=sha(OUT / 'cohort.json'))
    write(OUT / 'scoring.json', receipt, exclusive=True)
    try:
        data, meta, data_receipt = collect(dict(games=cohort['games']), library(), 'future', False)
        write(OUT / 'future-data.json', data_receipt, exclusive=True)
        games = {g['game']:g for g in cohort['games']}
        for m in meta:
            g = games[m['game']]
            m['team_id'] = g[('white_id','black_id')[m['ply'] % 2]]
        models = {kind:json.loads((OLD_OUT / f'22-{kind}-model.json').read_text())
                  for kind in ('linear','quadratic')}
        models['base'] = dict(linear=[0.]*22, quadratic=np.zeros((22,22)).tolist())
        predictions, checks = {}, {}
        lib = library()
        for kind in ('base','linear','quadratic'):
            predictions[kind], checks[kind], _ = native_score(lib, data, 22, models[kind])
            assert np.isfinite(predictions[kind]).all()
        metrics = summarize(meta, predictions, checks, plan)
        conditions = gate_result(plan, metrics)
        with (OUT / 'decisions.jsonl.gz').open('xb') as handle:
            with gzip.GzipFile(filename='', fileobj=handle, mode='wb', mtime=0) as stream:
                for i, m in enumerate(meta):
                    stream.write((json.dumps(dict(**m, logp={k:float(v[i]) for k,v in predictions.items()}))+'\n').encode())
        result = dict(at=now(), metrics=metrics, conditions=conditions, native_checks=checks,
                      decision='native_cost_and_posterior_design_allowed' if all(conditions.values()) else 'close_frozen_full_only_configuration',
                      plan_sha256=sha(OUT / 'plan.json'), cohort_sha256=sha(OUT / 'cohort.json'),
                      scores_sha256=sha(OUT / 'decisions.jsonl.gz'),
                      scope='Prospective predictive confirmation only. The293combined gate remains failed. No fitting, playing, runtime integration or new version.')
        write(OUT / 'result.json', result, exclusive=True)
        receipt.update(status='complete', decision=result['decision'])
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        receipt.update(status='failed', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        receipt.update(ended_at=now(), seconds=time.monotonic()-started)
        write(OUT / 'scoring.json', receipt)


if __name__ == '__main__':
    main()
