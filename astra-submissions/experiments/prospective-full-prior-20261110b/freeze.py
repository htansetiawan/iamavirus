"""Prepare/pin the full-only confirmation before any eligible game exists."""
from datetime import datetime, timedelta, timezone
import json
import sys
from protocol import ROOT, HERE, OUT, OLD, OLD_OUT, TEAMS, PRIORITY, now, instant, sha, write
sys.path.insert(0,str(OLD))
import numpy as np
import torch
from prepare import library
from model import COLUMNS


def main():
    cutoff = '2026-11-10T12:00:00Z'
    assert datetime.now(timezone.utc) < instant(cutoff)-timedelta(minutes=20)
    OUT.mkdir(exist_ok=True)
    old_plan = json.loads((OLD_OUT/'plan.json').read_text())
    old_result = json.loads((OLD_OUT/'result.json').read_text())
    assert old_result['decision'] == 'close_capture_fixed_configuration'
    assert old_result['modes']['22']['conditions']['gain']
    assert not old_result['modes']['14']['conditions']['matched_linear']
    failed = ROOT/'astra-submissions/analysis/prospective-full-prior-20261110'
    assert json.loads((failed/'execution.json').read_text())['status'] == 'failed'
    assert not any((failed/n).exists() for n in ('cohort.json','scoring.json','result.json','decisions.jsonl.gz'))
    original_confirmation = json.loads((failed/'plan.json').read_text())
    original_local_pins = {p:h for p,h in original_confirmation['dependencies'].items()
                           if not p.startswith('/media/henrytan/seagate/')}
    for p,h in original_local_pins.items():
        assert sha(p)==h, 'changed original local dependency: '+p
    closed_path = ROOT/'astra-submissions/analysis/storage-incident-20261110/closed-prefix-exclusions.json'
    closed = json.loads(closed_path.read_text())
    assert len(closed['games']) == 196
    previous = [dict(game=g['game'],sequence_sha256=g['sequence_sha256']) for g in old_plan['games']]
    previous += [dict(game=g['game'],sequence_sha256=g['sequence_sha256']) for g in closed['games']]
    assert len(previous) == len({g['sequence_sha256'] for g in previous}) == 4996
    exclusions = OUT/'previous-exclusions.json'
    write(exclusions,dict(games=previous,old_fit_plan_sha256=sha(OLD_OUT/'plan.json'),
                         closed_prefix_sha256=sha(closed_path),no_closed_prefix_predictions=True),exclusive=True)
    archive = ROOT/'data/astra-spool/prospective-full-prior-20261110b'
    archive.parent.mkdir(parents=True,exist_ok=True)
    assert archive.resolve().is_relative_to(ROOT) and not archive.exists()
    assert __import__('os').stat(archive.parent).st_dev == __import__('os').stat(ROOT).st_dev
    lib = library()
    rng = np.random.default_rng(2951110)
    x = rng.uniform(0,1,(37,26)).astype(np.float32)
    x[:,0] = np.arange(37)%3 == 0
    base = rng.normal(size=37).astype(np.float32)
    zero,zeroq = np.zeros(22,np.float32),np.zeros((22,22),np.float32)
    baseline = np.empty(37,np.float32)
    lib.quiet_logp(x,base,37,22,zero,zeroq,baseline)
    native = []
    for kind in ('linear','quadratic'):
        model = json.loads((OLD_OUT/f'22-{kind}-model.json').read_text())
        assert model['features'] == 22 and model['kind'] == kind
        lin,q = np.array(model['linear'],np.float32),np.array(model['quadratic'],np.float32)
        out = np.empty_like(baseline)
        lib.quiet_logp(x,base,37,22,lin,q,out)
        quiet = x[:,0] == 0
        assert np.array_equal(out[~quiet],baseline[~quiet])
        v = x[:,COLUMNS].astype(float)
        d = v@lin.astype(float)+np.einsum('ni,ij,nj->n',v,q.astype(float),v)
        before,after = base[quiet].astype(float),base[quiet].astype(float)+d[quiet]
        correction=before.max()+np.log(np.exp(before-before.max()).sum())-after.max()-np.log(np.exp(after-after.max()).sum())
        ref = baseline.astype(float)
        ref[quiet] += d[quiet]+correction
        error = float(abs(out-ref).max())
        assert error < 2e-5
        native.append(dict(kind=kind,capture_bitwise=True,scalar_logp_error=error,
                           model_sha256=sha(OLD_OUT/f'22-{kind}-model.json')))
    deps = [p for p in HERE.glob('*.py')]
    deps += [OLD_OUT/n for n in ('plan.json','result.json','22-linear-model.json','22-quadratic-model.json')]
    deps += [OLD/n for n in ('train.py','prepare.py','model.py','bridge.c','quiet.h')]
    deps += [ROOT/'learning'/n for n in ('api_client.py','ingest.py','rules.py','histories.py','_native.py')]
    # The old training exports are provenance, not inputs to this frozen-head
    # execution. They are offline with the failed drive. Keep their original
    # hashes, but never substitute or rebuild them to make a model test run.
    archived = {p:h for p,h in old_plan['dependencies'].items() if p.startswith('/media/henrytan/seagate/')}
    assert len(archived)==2 and {__import__('pathlib').Path(p).name for p in archived}=={'manifest.json','games.jsonl'}
    deps += [__import__('pathlib').Path(p) for p in old_plan['dependencies'] if p not in archived]
    deps += [exclusions,closed_path,failed/'plan.json',failed/'execution.json',
             ROOT/'astra-submissions/experiments/cohort-integrity-20261110/audit.py']
    deps += [ROOT/'build/librules.so',ROOT.parent/'fow-starter/referee.py']
    plan = dict(at=now(),cutoff=cutoff,data_deadline='2026-11-11T00:00:00Z',games=300,
                teams=TEAMS,priority=PRIORITY,seed=2951110,bootstrap_draws=2000,cores=[0,1],
                poll_seconds=1200,page_cap=30,request_cap=1500,wall_seconds=13*3600,
                replay_bytes_cap=4*1024*1024,archive_bytes_cap=128*1024*1024,
                archive=str(archive),archive_storage='Bounded primary working archive on the root SSD; external mirroring is a separate post-run action when storage is stable.',
                shared_raw=str(ROOT/'data/raw'),previous_plan=str(exclusions),
                owner_fallback_on_store_loss=True,
                cache_policy='Owner-first cache. Ordinary own-game cache misses defer while the shared store is healthy. If the shared store is unavailable or its file read raises OSError, fetch that completed replay into the private SSD archive, logging the fallback. No shared writes, persistent replacement replay watcher or later-game skip.',
                archival_training_export_hashes=archived,
                archival_provenance_note='Original fit-export hashes are retained from the immutable293 plan; those exports are not read by collection, fixed inference or review. All actually used local source/native/history/model dependencies are verified below.',
                gate=dict(primary_min=5000,full_gain=.05,matched_linear_gain=.02,
                          surprise_min=100,priority_games_min=20),
                dependencies={str(p):sha(p) for p in sorted(set(deps))},
                selection='Earliest completion timestamp, then ID; first300 unique fow-v1 trajectories with>=4plies, at least one frozen reference ID. '
                          'Exclude all4800 trajectories from293, all196 unscored closed295 trajectories, and duplicates within this cohort. All outcomes, colors and versions; no score-based selection. '
                          'Require complete cursor snapshot coverage back to cutoff and exact nanosecond order. Owner-first cache with the explicitly declared store-loss fallback.',
                primary='All reference-team decisions after eight own moves, excluding demonstrated moves that leave the mover king capturable, as in293. '
                        'All-move nonregression includes the excluded opening/fatal decisions. Game-cluster bootstrap2000draws.',
                models='Frozen293 full22-feature quadratic versus its frozen matched linear and native baseline/history. Cheap branch unchanged. No fit/epoch/temperature/feature/threshold changes.',
                scope='Fresh execution of the same frozen full-only hypothesis after295 infrastructure interruption.295 remains closed/inconclusive without scores;293 combined-gate failure stays failed. '
                      'New cutoff/population with4996 exclusions, bounded SSD primary, explicit cache-loss fallback and exact timestamps; no model/gate/feature/fit changes. '
                      'This confirmation can reject post-selection optimism; it cannot retroactively turn293 or295 into a pass. '
                      'Predictive scoring of hypothetical full-parent features, not an observation-only opponent policy or an Elo experiment.',
                next='Only all conditions plus independent audit allow a separately designed native-cost and sequential-posterior experiment. '
                     'No automatic runtime integration, match, archive/version reservation, arena change, refit or GPU use. '
                     'Insufficient data or collection failure closes this run without moving cutoff/extending cohort.')
    assert plan['gate']==original_confirmation['gate'], 'predictive gates must remain unchanged'
    write(OUT/'preflight.json',dict(at=now(),passed=True,native=native,
          original_local_dependencies_unchanged=len(original_local_pins),
          unchanged_gate=plan['gate']==original_confirmation['gate'],
          no_future_sources_opened=True,no_fit=True,old_combined_gate_preserved=old_result['decision']),exclusive=True)
    write(OUT/'plan.json',plan,exclusive=True)
    print(json.dumps(dict(prepared=True,cutoff=cutoff,pins=len(plan['dependencies']),models=native)),flush=True)


if __name__=='__main__':
    main()
