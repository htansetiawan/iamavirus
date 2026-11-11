"""Join existing fit receipts to the deployed coefficients; do not refit.

This verifies serialized weights, source versions and saved summary arithmetic.
It does not recover/hash the original training corpus or recompute predictions.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RECEIPTS = ROOT / 'fable-submissions/analysis/refit-all-20261101'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def vector(source, name):
    found = re.search(r'theta_' + name + r'\[MM_FEATURES\]\s*=\s*\{([^}]+)\}', source)
    assert found
    result = [float(s.strip().rstrip('f')) for s in found.group(1).split(',')]
    assert len(result) == 28
    return result


def audit(engine_repo, history_copy):
    archive = ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
    older = ROOT / 'fable-submissions/iamavirus-v35-mist-c-v14.zip'
    with zipfile.ZipFile(archive) as zipped:
        deployed = zipped.read('src/movemodel.c').decode()
        history_sha = hashlib.sha256(zipped.read('data/history.bin')).hexdigest()
    with zipfile.ZipFile(older) as zipped:
        baseline = zipped.read('src/movemodel.c').decode()
    rows = []
    for arm in ('full', 'cheap'):
        fit = read(RECEIPTS / ('fit-all-' + arm + '.json'))
        old_receipt = fit if arm == 'full' else read(RECEIPTS / 'refit-eval-v35cheap.json')
        assert vector(deployed, arm) == fit['final']['theta']
        assert vector(baseline, arm) == old_receipt['initial']['theta']
        assert fit['facts'] == 28 and fit['skip_mover'] == 'IAmAVirus'
        assert all(fit['final']['theta'][i] == 0 for i in fit['fixed'])
        initial = old_receipt['initial']['test']['all_but_skipped']
        final = fit['final']['test']['all_but_skipped']
        assert initial['positions'] == final['positions'] == 1734620
        assert all(p['train']['positions'] == 9901850 for p in fit['passes'])
        per = fit['final']['test']['per_mover']
        counts = sum(v['positions'] for k, v in per.items() if k != fit['skip_mover'])
        # The original fitter reports only the 30 largest mover groups.
        # Their means cannot reconstruct the global saved score.
        assert len(per) == 30 and counts < final['positions']
        rows.append(dict(arm=arm, coefficients_matched=28, baseline_coefficients_matched=28,
                         recorded_optimizer_passes=len(fit['passes']), fixed_slots=fit['fixed'],
                         train_positions=9901850, heldout_positions=final['positions'],
                         per_mover_groups_reported=len(per), per_mover_positions_listed=counts,
                         heldout_other_positions_unlisted=final['positions'] - counts,
                         old_metrics=initial, new_metrics=final,
                         rounded_nats_gain=final['nats_over_uniform'] - initial['nats_over_uniform'],
                         geometric_likelihood_ratio_from_rounded_gain=math.exp(final['nats_over_uniform'] - initial['nats_over_uniform']),
                         rounded_top1_percentage_point_gain=100 * (final['top1'] - initial['top1']),
                         input_mode='streamed command' if str(fit['train']).startswith('cmd:') else 'binary feature file',
                         cheap_initial_is_v35_baseline=arm != 'cheap' or fit['initial']['theta'] == old_receipt['initial']['theta']))
    trainers = {}
    for revision in ('a1bd043', 'd262253'):
        raw = subprocess.check_output(['git', '-C', str(engine_repo), 'show', revision + ':tools/fit_move_model_stream.py'])
        assert b'rows[:30]' in raw
        trainers[revision] = hashlib.sha256(raw).hexdigest()
    saved_history = None
    if history_copy.is_file():
        saved_history = sha(history_copy)
        assert saved_history == history_sha
    inputs = [RECEIPTS / n for n in ('result.md', 'fit-all-full.json', 'fit-all-cheap.json', 'refit-eval-v35cheap.json')]
    return dict(at=datetime.now(timezone.utc).isoformat(), deployed_archive_sha256=sha(archive),
                baseline_archive_sha256=sha(older), source_receipts={str(p.relative_to(ROOT)): sha(p) for p in inputs},
                trainer_git_objects=trainers, model_records=rows, history_sha256=history_sha,
                saved_history_copy_sha256=saved_history, saved_history_copy_matches_archive=saved_history == history_sha,
                reported_split=dict(total_games=174386,train_games=148357,test_games=26029,seed=7,test_fraction=.15,
                                    unit='game',independently_recensused=False),
                caveats=['Original input dataset membership/hashes not recertified; no fitting or prediction re-evaluation.',
                         'Reported metrics are rounded saved outputs, not independently recomputed scores.',
                         'Per-mover metrics list only the top30 groups; 2418 held-out other moves are not itemized.',
                         'The cheap fit initial vector is not the v35 cheap baseline; its separate baseline receipt is required.',
                         'The historical report describes storage failures/restarted cheap fitting and replayed local-game attempts.',
                         'The history table used the complete export; a coefficient holdout is not an end-to-end bot holdout.'],
                scope='Read-only lineage join of Fable original receipts, committed trainer objects, old/deployed weights and optional saved history copy. No new model, experiment, match, strength claim or arena change.')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--engine-repo', type=Path, default=ROOT.parent / 'fowsearch-c')
    parser.add_argument('--history-copy', type=Path, default=Path('/home/henrytan/fable-persist/suite/history-all-20261101.bin'))
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit(args.engine_repo, args.history_copy)
    if args.out:
        with args.out.open('x') as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('model_records', 'trainer_git_objects', 'saved_history_copy_matches_archive')}, indent=2))
