"""Freeze new prospective weights/selection/gates; no API or predictions."""
from datetime import datetime,timezone
import ast
import hashlib
import json
from pathlib import Path
import sys
import torch
from protocol import ROOT,OUT,HERE,TEAMS,PRIORITY,now,sha,write


def main():
    assert not (OUT/'plan.json').exists()
    fit=ROOT/'astra-submissions/analysis/world-quiet-fit-20261110'
    sources=[ROOT/'astra-submissions/analysis/prospective-full-prior-20261110b/previous-exclusions.json',
        ROOT/'astra-submissions/analysis/class-rank-holdout-20261110/cohort.json',ROOT/'astra-submissions/analysis/prospective-full-prior-20261110b/cohort.json']
    prior={}
    for path in sources:
        for game in json.loads(path.read_text())['games']:
            prior.setdefault(game['sequence_sha256'],dict(game=game['game'],sequence_sha256=game['sequence_sha256']))
    assert len(prior)==5376
    exclusions=OUT/'previous-exclusions.json'
    write(exclusions,dict(games=sorted(prior.values(),key=lambda g:g['sequence_sha256']),sources={str(p):sha(p) for p in sources}),exclusive=True)
    weights={kind:str(fit/(kind+'-best.pt')) for kind in ('teacher','linear','quadratic')}
    weights['production']=str(ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/22-quadratic-model.json')
    for source in HERE.glob('*.py'):ast.parse(source.read_text())
    # Loading shapes/weights verifies checkpoint plumbing only, no scored data.
    from score import load_models
    models=load_models(dict(weights=weights,architecture=dict(width=128,latents=8)))
    assert sum(p.numel() for p in models['teacher'].parameters())==587649
    del models
    deps=[*sorted(HERE.glob('*.py')),exclusions,*map(Path,weights.values()),*sources,
        ROOT/'astra-submissions/analysis/quiet-teacher-reference-20261110/independent-review.json',
        ROOT/'astra-submissions/experiments/quiet-teacher-reference-20261110/reference.py',
        ROOT/'astra-submissions/experiments/world-quiet-attention-20261110/model.py',
        ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110/prepare.py',
        ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110/model.py',
        ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110/bridge.c',
        ROOT/'astra-submissions/experiments/capture-fixed-prior-20261110/build/bridge.so',
        ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so',
        ROOT/'astra-submissions/experiments/reconstructed-train-20261110/build.py',
        ROOT/'astra-submissions/experiments/cohort-integrity-20261110/audit.py',
        ROOT/'astra-submissions/experiments/deployed-prior-comparison-20261102/prior.c',
        ROOT/'astra-submissions/tools/prior_training_cache.py',ROOT/'astra-submissions/tools/reconstructed_cache.py',ROOT/'astra-submissions/tools/experience_index.py',
        ROOT/'learning/api_client.py',ROOT/'learning/ingest.py',ROOT.parent/'fow-starter/referee.py',
        ROOT/'astra-submissions/analysis/v38-metadata-20261110T1803Z/leaderboard.json',
        ROOT/'.venv/lib/python3.12/site-packages/torch/nn/functional.py',ROOT/'.venv/lib/python3.12/site-packages/torch/nn/modules/transformer.py',ROOT/'.venv/lib/python3.12/site-packages/torch/version.py',
        ROOT/'data/astra-spool/ragged-train-20261110/manifest.json',ROOT/'data/astra-spool/reconstructed-train-20261110/manifest.json']
    base=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
    deps+=[base/'data/history.bin',*sorted((base/'src').glob('*'))]
    archive=ROOT/'data/astra-spool/prospective-quiet-teacher-20261110'
    plan=dict(at=now(),cutoff='2026-11-10T19:15:00Z',data_deadline='2026-11-11T03:15:00Z',games=300,teams=TEAMS,priority=PRIORITY,
        previous_plan=str(exclusions),archive=str(archive),poll_seconds=1200,request_cap=1800,page_cap=60,
        replay_bytes_cap=4*1024**2,archive_bytes_cap=512*1024**2,private_bytes_cap=256*1024**2,
        wall_seconds=34200,pipeline_wall_seconds=40500,core_wait_seconds=1800,cores=[2,3],gpu=False,
        weights=weights,architecture=dict(width=128,latents=8),models=['base','linear','quadratic','production','teacher'],batch=256,
        native_state_library=str(ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so'),
        torch_version=torch.__version__,torch_git=torch.version.git_version,seed=3261110,bootstrap_draws=2000,gate=dict(primary_min=5000,native_gain=.1,quadratic_gain=.03,surprise_min=100,priority_games_min=20,numeric_tolerance=1e-4),
        selection='First300unique eligible whole trajectories with one of11fixed target IDs, ordered exact completion nanoseconds thenID, starting atcutoff. Exclude5376prior trajectories, non-fow-v1 and<4plies only. No result/version/color/prediction selection; all declared reference-side decisions included. Firstcompletefixedcursor snapshot throughcutoff must cover them; no skipping early unavailable records. Public-only boundedSSDcopy duringknownsharedstore outage, no failed-mount access or replacementwatcher.',
        primary='Reference-side decisions after8ownmoves, excluding actual moves that leave moverkingcapturable, matching generative updater continued-state pruning; all-move results include them. IDs/versions/outcomes/target index are evaluation metadata only, never neural inputs. Parent board/bothviews/castle/EP/halfmove/side and native features/candidate/history are privileged conditional-prior inputs, not an actor policy.',
        statistical='Pooled primary meanlogp gain, whole-game clustered2000bootstrap draws seeds3261110/11/12 for native/matchedquad/production contrasts. Bothsides clusterwithin game. Require+.10over native,+.03over EACHmatched and4000gamequad; lower95CI>0over native andproduction, allmove>=0, eachpriority>=20gamesandgain>=0,>=5000primary and100surprisecaptures, exactsame-Torch-backendcaptureentries. Alloldnumeric nativecontrolsagree<1e-4, reportmaxerror; do not claimCbitidentity fromTorch. Auditallsource/inputs/rawbatchtarget/capture/statistics plusfirst64fixedfutureFP64residual check<1e-4. All-gate failure closesfixedcorrectedteacher withoutcohortextension/seed/opponent/batch/threshold/refitrescue.',
        scope='326 new future action-prediction confirmation of325corrected explicit-erf/math teacher with320epoch11weights, same3500game controls plus2934000gamequad. No old320review retry/reclassification, no fit/GPU/student/native/posterior/playing/ZIP/version/arena action. Source,weights,cutoff,300games/gatesfrozenandbothmirrorsverifiedbeforelaunch. Collectorloadsnomodels orcomputespredictions, and sourceauditmustpassbeforefirstscores. One original boundedpipeline, publicGETspacing1.2s/retrybackoff and20minpolls; source/scoring/review useexclusive2-3coresafterseal. Rawtensors/perrowpredictionsremainlocalignored after324exportreview; explicit code/plan/aggregate/hash/auditpublication only. Qualityallpass+independentaudit onlyearnsa separatelyfrozenstudent-distillationdesign, notteacherplayingstrengthoranynewfitautomatically.',
        dependencies={str(p):sha(p) for p in sorted(set(deps))})
    assert datetime.now(timezone.utc)<datetime.fromisoformat(plan['cutoff'].replace('Z','+00:00'))
    write(OUT/'plan.json',plan,exclusive=True)
    (OUT/'.gitignore').write_text('# Per-row numerical data lives in ignored data/astra-spool; aggregate publication only.\nprivate/\n')
    print(json.dumps(dict(prepared=True,pins=len(plan['dependencies']),exclusions=len(prior),cutoff=plan['cutoff'],deadline=plan['data_deadline'],plan_sha256=sha(OUT/'plan.json')),indent=2))


if __name__=='__main__':main()
