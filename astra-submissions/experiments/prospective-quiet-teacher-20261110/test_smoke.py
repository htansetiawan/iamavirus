"""Full negative pipeline on a synthetic replay/zero models; no API/trained NN."""
from contextlib import redirect_stdout
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest
import torch

from protocol import ROOT,TEAMS,sha
sys.path.insert(0,str(ROOT))
from learning.histories import replay_from_moves
from score import WorldQuietTeacher,ScalarResidual
import score,source_audit
spec=importlib.util.spec_from_file_location('confirmation_review_smoke',Path(__file__).with_name('review.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


class SyntheticPipeline(unittest.TestCase):
    def test_complete_negative_run_and_independent_review(self):
        torch.set_num_threads(2)
        with tempfile.TemporaryDirectory(prefix='astra-teacher-confirm-smoke-') as folder:
            out=Path(folder);archive=out/'archive';game_dir=archive/'games'/'fixture0';game_dir.mkdir(parents=True)
            paths={name:out/(name+'.pt') for name in ('teacher','linear','quadratic')}
            torch.save(WorldQuietTeacher(width=16,latents=2).state_dict(),paths['teacher'])
            for kind in ('linear','quadratic'):torch.save(ScalarResidual(kind).state_dict(),paths[kind])
            production=out/'production.json';production.write_text(json.dumps(dict(linear=[0.]*22,quadratic=[[0.]*22 for _ in range(22)])))
            weights={k:str(p) for k,p in paths.items()};weights['production']=str(production)
            moves='e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3 d7d6 c2c3 e8g8 h2h3 c6b8 d2d4 b8d7'.split()
            at='2026-11-10T17:00:01Z';team=next(iter(TEAMS))
            rp=replay_from_moves('fixture0',moves,'1-0','fixture result','Ref','Other')
            rp.update(createdAt=at,rulesVersion='fow-v1',whitePlayerId=team,blackPlayerId='other',whiteVersion=1,blackVersion=1)
            replay_path=game_dir/'replay.json';replay_path.write_text(json.dumps(rp))
            (game_dir/'fetch.json').write_text(json.dumps(dict(sha256=sha(replay_path),synthetic_fixture=True)))
            r=dict(id='fixture0',createdAt=at,result='1-0',plies=20,white='Ref',black='Other',whitePlayerId=team,blackPlayerId='other',whiteVersion=1,blackVersion=1)
            old=dict(r,id='old00000',createdAt='2026-11-10T16:59:59Z')
            page=dict(sort='played',order='desc',games=[r,old],nextCursor=None)
            (archive/'page-000-00.json').write_text(json.dumps(dict(page=page,fetch=dict(url='https://6s890.lids.mit.edu/api/games?sort=played&order=desc&limit=100',synthetic_fixture=True))))
            (archive/'tick-000.json').write_text(json.dumps(dict(pages=1)))
            exclusions=out/'exclusions.json';exclusions.write_text(json.dumps(dict(games=[])))
            from protocol import cohort_game
            g,reason=cohort_game(r,rp,sha(replay_path),set());self.assertIsNone(reason)
            plan=dict(torch_version=torch.__version__,torch_git=torch.version.git_version,games=1,teams=TEAMS,cutoff='2026-11-10T17:00:00Z',data_deadline='2026-11-10T17:00:02Z',
                previous_plan=str(exclusions),archive=str(archive),weights=weights,architecture=dict(width=16,latents=2),models=['base','linear','quadratic','production','teacher'],
                native_state_library=str(ROOT/'astra-submissions/experiments/observed-class-20261110/build/producer.so'),
                batch=8,cores=[2,3],private_bytes_cap=1024**2,seed=3261110,bootstrap_draws=20,
                gate=dict(primary_min=5000,native_gain=.1,quadratic_gain=.03,priority_games_min=20,surprise_min=100,numeric_tolerance=1e-4),
                dependencies={str(p):sha(p) for p in [*paths.values(),production]})
            (out/'plan.json').write_text(json.dumps(plan))
            (out/'cohort.json').write_text(json.dumps(dict(games=[g],collection_tick=0,no_parameters_loaded_or_predictions_computed=True,sealed_at='2026-11-10T17:00:02Z')))
            (out/'execution.json').write_text(json.dumps(dict(status='complete',phase='sealed',started_at='2026-11-10T16:59:00Z',cohort_sha256=sha(out/'cohort.json'))))
            previous={m:m.OUT for m in (source_audit,score,review)}
            try:
                for module in previous:module.OUT=out
                with redirect_stdout(io.StringIO()):
                    source_audit.main();score.main();review.main()
            finally:
                for module,path in previous.items():module.OUT=path
            result=json.loads((out/'result.json').read_text());audit=json.loads((out/'independent-review.json').read_text())
            self.assertTrue(audit['passed']);self.assertEqual(result['decision'],'close_corrected_teacher_confirmation')
            self.assertEqual(result['metrics']['gain'],0.)
            self.assertFalse(result['conditions']['native_gain']);self.assertFalse(result['conditions']['primary'])
            self.assertLess(audit['fp64_max_residual_error'],1e-4)


if __name__=='__main__':unittest.main()
