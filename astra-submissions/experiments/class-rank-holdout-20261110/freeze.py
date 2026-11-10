"""Publish a fixed retrospective holdout protocol before collecting/scoring."""
import json
from pathlib import Path
from collect import ROOT,HERE,OUT
from protocol import TEAMS,PRIORITY,OWN,now,sha,write


def main():
    OUT.mkdir(exist_ok=False)
    development=ROOT/'astra-submissions/analysis/learned-class-rank-20261110'
    original=json.loads((development/'plan.json').read_text())
    dependencies=dict(original['dependencies'])
    exclusions=ROOT/'astra-submissions/analysis/prospective-full-prior-20261110b/previous-exclusions.json'
    assert len(json.loads(exclusions.read_text())['games'])==4996
    files=list(HERE.glob('*.py'))+[development/'plan.json',development/'result.json',exclusions,
          HERE.parent/'prospective-full-prior-20261110b/protocol.py',ROOT/'learning/api_client.py']
    dependencies.update({str(p):sha(p) for p in files})
    for p,digest in dependencies.items():assert sha(p)==digest,p
    archive=ROOT/'data/astra-spool/class-rank-holdout-20261110'
    assert not archive.exists()
    plan=dict(at=now(),window=['2026-11-10T00:00:00Z','2026-11-10T07:00:00Z'],games=80,
        teams=TEAMS,priority=PRIORITY,own_id=OWN,exclusions=str(exclusions),
        primary_execution=str(ROOT/'astra-submissions/analysis/prospective-full-prior-20261110b/execution.json'),
        selection='Query each priority exact ID with played-desc fixed cursors, cover entire fixed window; merge immutable metadata and sort exact nanoseconds then ID. '
                  'First80 distinct fow-v1 trajectories with>=4plies, excluding4996 whole game IDs/sequences and within-cohort duplicates. '
                  'All outcomes, colors, played versions and opponents; no performance selector. Unexpected rules/metadata/source error closes, not silently skipped.',
        primary='All nine-reference-team movers in the80games after eight own moves whose true transition survives the native king-pruning/observation rules. '
                'Captures are unchanged controls. All reference moves including opening/fatal moves are a separate nonregression control.',
        models='Exactly293 fixed full22-quadratic primary and fixed22-linear comparator. Native/history scalar parity. No fitting, feature/temperature/epoch or threshold selection.',
        mechanism='301 fixed post-history score ranking reassigns existing post-history likelihood values within each same-parent, received-view-consistent noncapturing survivor class. '
                  'All masks/captures unchanged; per-class likelihood spectrum and sum(p^tau) preserved for every positive tau. Native cheap branch untouched.',
        metric='Conditional action log-likelihood improvement at fixed temperature2; denominators cancel under exact permutation. '
               'Not sequential posterior truth probability, calibration, risk, exploitability or Elo.',
        gate=dict(primary_min=1500,changed_min=200,changed_games_min=30,gain=.02,over_linear=.01,priority_games_min=15),
        bootstrap_draws=2000,seed=3131110,scalar_tolerance=1e-4,cores=[2,3],max_seconds=180,
        request_cap=200,pages_per_team=20,collection_seconds=600,
        replay_bytes_cap=4*1024*1024,archive_bytes_cap=64*1024*1024,archive=str(archive),
        transport='Sequential public GET,>=1.2s/request, bounded shared-client retries honoring Retry-After. Wait within120s of primary307 next poll; no primary burst overlap. '
                  'Owner-first shared cache; ordinary healthy own-cache miss closes rather than bypassing owner. Explicit store-loss fallback to private bounded SSD. '
                  'No shared writes, new watcher, GPU, service, drive mount/repair or primary307 source/prediction reads.',
        uncertainty='2000 whole-game cluster bootstrap draws, percentile95% lower bound>0. Every fixed priority needs>=15primary games and nonnegative mean gain. '
                    'No asymptotic independence/Elo claim; residual opponent/version/time dependencies remain.',
        invariants='Every course actual frame/action and all alternate-action class flags must match native; captures/masks exactbits; independent stable-sort permutation and powered sums; '
                   'double-expression model/history scalar tolerance and finite values; independent selection/statistical reconstruction. Any mismatch closes without interpreting strength.',
        scope='Independent retrospective holdout from model fitting and ranking selection, not a prospective or globally unseen arena-data claim. '
              'Window after293 Nov2-9 datasets and before29507:15cutoff; exclude4800original+196unscored closed295. '
              'No source/outcome/model selection from current307 future cohort.293combined failure,295infrastructure closure,307contract and all earlier negative gates remain unchanged. '
              'Parent evidence preservation does not preserve nonlinear fitted-guard normalization after merging, future caps/history/clock, or safety.',
        next='All frozen conditions plus source/course/scalar/aggregate review permit a separate sequential-posterior design only. '
             'Failure closes this fixed ranking configuration; no threshold sweep, favorable-slice rescue, refit, cohort expansion, native integration, match, ZIP/version or arena change.',
        nearest_prior=['228/229 already separate observation/action evidence;231/232 posterior fits closed',
                       '293combined failed;307full-only confirmation separate and untouched',
                       '299generic permutation correct;300native class masks correct',
                       '301reusedTRAIN94examples+.04142nats only earned independent holdout'],
        dependencies=dependencies)
    write(OUT/'plan.json',plan,exclusive=True)
    print(json.dumps(dict(prepared=True,pins=len(dependencies),plan_sha256=sha(OUT/'plan.json'))),flush=True)


if __name__=='__main__':main()
