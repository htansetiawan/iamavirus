"""Exercise295 selection/scoring/review in an isolated SYNTHETIC test namespace.

Only existing293 TRAIN moves are used. Real future state/data are never written
or scored. This is software correctness, not an additional model experiment.
"""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'astra-submissions/analysis/prospective-pipeline-smoke-20261110'
PRODUCTION=ROOT/'astra-submissions/experiments/prospective-full-prior-20261110'
REAL_OUT=ROOT/'astra-submissions/analysis/prospective-full-prior-20261110'
sys.path[:0]=[str(PRODUCTION),str(ROOT)]
from protocol import PRIORITY, TEAMS, now, sha, write
from collect import snapshot, seal_candidates
from learning.histories import replay_from_moves
from learning.ingest import validate_replay


def main():
    start=time.monotonic()
    OUT.mkdir(exist_ok=False)
    assert not(REAL_OUT/'cohort.json').exists(), 'this preflight never opens future data'
    assert not(REAL_OUT/'result.json').exists()
    real_plan_hash=sha(REAL_OUT/'plan.json')
    old_path=ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110/plan.json'
    old=json.loads(old_path.read_text())
    selected=[g for g in old['games'] if g['split']=='train' and len(g['moves'])>=50][:3]
    assert len(selected)==3
    # This table is fixed by existing training order/length, not model scores.
    fixture_manifest=[dict(original_train_game=g['game'],moves=g['moves'][:40],
                           original_sequence_sha256=g['sequence_sha256']) for g in selected]
    write(OUT/'fixtures.json',dict(type='SYNTHETIC CORRECTNESS FIXTURES ONLY',
          old_plan_sha256=sha(old_path),fixtures=fixture_manifest),exclusive=True)
    tmp=tempfile.TemporaryDirectory(prefix='astra-prospective-pipeline-smoke-')
    work=Path(tmp.name)
    try:
        archive=work/'archive';archive.mkdir()
        test_out=work/'output';test_out.mkdir()
        shared=work/'shared'
        template=json.loads((REAL_OUT/'plan.json').read_text())
        previous=work/'empty-previous.json';write(previous,dict(games=[]))
        # Test-only metadata differs so3known training traces can traverse the
        # pipeline. All production numerical gates and frozen weights remain.
        plan={**template,'games':3,'cutoff':'2000-01-01T00:00:00Z',
              'data_deadline':'2000-01-01T12:00:00Z','archive':str(archive),
              'shared_raw':str(shared),'previous_plan':str(previous),
              'type':'SYNTHETIC SOFTWARE TEST; NOT PRODUCTION CONFIRMATION'}
        listings=[]
        frames=0
        for i,g in enumerate(selected):
            white_id,black_id=PRIORITY[i],PRIORITY[(i+1)%3]
            game=f'smok{i:04d}'
            rp=replay_from_moves(game,g['moves'][:40],'1-0','Opponent crashed',TEAMS[white_id],TEAMS[black_id])
            rp.update(createdAt=f'2000-01-01T00:0{i+1}:00Z',whitePlayerId=white_id,blackPlayerId=black_id,
                      whiteVersion=1,blackVersion=1,rulesVersion='fow-v1')
            assert not validate_replay(rp)[1]
            directory=shared/'games'/game;directory.mkdir(parents=True)
            write(directory/'replay.json',rp,exclusive=True)
            listings.append({k:rp[k] for k in ('id','createdAt','white','black','whitePlayerId','blackPlayerId',
                                             'whiteVersion','blackVersion','result')})
            listings[-1]['plies']=40
            frames+=len(rp['frames'])
        oldest={**listings[0],'id':'oldr0000','createdAt':'1999-12-31T23:59:59Z'}
        class OfflineClient:
            requests=0
            def games_page(self,params,cursor):
                assert cursor is None
                self.requests+=1
                page=dict(games=list(reversed(listings))+[oldest],sort='played',order='desc',
                          nextCursor=None,summary=None,playing=[])
                class Record:
                    def __init__(self):self.url='https://fixture.invalid/api/games?sort=played&order=desc&limit=100'
                return page,Record()
            def get_bytes(self,*args):
                raise AssertionError('NETWORK DISABLED FOR SOFTWARE TEST')
        client=OfflineClient()
        rows,pages=snapshot(client,plan['cutoff'],archive,0,30)
        games,decisions,pending=seal_candidates(rows,client,plan,archive,set())
        assert not pending and len(games)==3 and pages==1
        write(test_out/'plan.json',plan)
        cohort=dict(sealed_at=now(),cutoff=plan['cutoff'],publication_commit='0'*40,
                    plan_sha256=sha(test_out/'plan.json'),games=games,exclusions=decisions,
                    collection_tick=0,source_archive=str(archive),no_models_or_predictions_opened=True,
                    type='SYNTHETIC SOFTWARE TEST')
        write(test_out/'cohort.json',cohort)
        write(test_out/'execution.json',dict(status='complete',phase='sealed',
              started_at='1999-12-31T23:00:00Z',cohort_sha256=sha(test_out/'cohort.json')))
        # Real modules, but all mutable output paths point at the test namespace.
        import score,verify
        assert score.OUT==verify.OUT==REAL_OUT
        score.OUT=verify.OUT=test_out
        with (OUT/'pipeline.stdout').open('x') as stdout,(OUT/'pipeline.stderr').open('x') as stderr:
            with redirect_stdout(stdout),redirect_stderr(stderr):
                score.main()
                verify.main()
        result=json.loads((test_out/'result.json').read_text())
        audit=json.loads((test_out/'independent-review.json').read_text())
        assert audit['passed'] and audit['course_frames']==frames
        assert result['decision']=='close_frozen_full_only_configuration'
        assert not result['conditions']['primary_count']
        assert not result['conditions']['priority_coverage']
        assert result['metrics']['capture_target_error']==result['metrics']['capture_action_error']==0
        assert sha(REAL_OUT/'plan.json')==real_plan_hash
        assert not(REAL_OUT/'cohort.json').exists() and not(REAL_OUT/'result.json').exists()
        receipt=dict(at=now(),passed=True,scope='Software fixture correctness only; not a predictive/strength result.',
                     games=3,course_frames=audit['course_frames'],
                     scalar_action_checks=audit['scalar_action_checks'],
                     scalar_capture_checks=audit['scalar_capture_checks'],
                     max_scalar_logp_error=audit['max_scalar_logp_error'],
                     correctly_rejected_small_cohort=True,network_requests=0,
                     live_plan_sha256_unchanged=real_plan_hash,
                     live_future_cohort_absent=True,live_future_scores_absent=True,
                     original_source_sha256={str(p):sha(p) for p in [Path(__file__),*PRODUCTION.glob('*.py')]},
                     frozen_model_sha256={n:sha(ROOT/'astra-submissions/analysis/capture-fixed-prior-20261110'/n)
                                          for n in ('22-linear-model.json','22-quadratic-model.json')},
                     seconds=time.monotonic()-start)
        write(OUT/'receipt.json',receipt,exclusive=True)
        # Preserve independently verified fixture artifacts with explicit names.
        for name in ('independent-review.json','future-data.json','scoring.json'):
            write(OUT/('fixture-'+name),json.loads((test_out/name).read_text()),exclusive=True)
        print(json.dumps(receipt,indent=2),flush=True)
    finally:
        tmp.cleanup()


if __name__=='__main__':
    main()
