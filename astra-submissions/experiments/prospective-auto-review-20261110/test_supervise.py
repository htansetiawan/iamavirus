"""Real child-process checks for stop-on-failure and receipt enforcement."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from supervise import claim,release,execute_pipeline,check_lease


class ContinuationChecks(unittest.TestCase):
    def test_failed_audit_never_starts_scoring(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'out';study=root/'study';out.mkdir();study.mkdir()
            sentinel=root/'score-started'
            commands=[('source-audit',[sys.executable,'-c','raise SystemExit(9)'],10),
                      ('score',[sys.executable,'-c',f'from pathlib import Path;Path({str(sentinel)!r}).touch()'],10)]
            with self.assertRaisesRegex(AssertionError,'exited 9'):
                execute_pipeline(out,study,commands,lambda:None)
            self.assertFalse(sentinel.exists())
            self.assertEqual(json.loads((out/'stages.json').read_text())[0]['exit_code'],9)

    def test_zero_exit_without_sealed_receipt_never_scores(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'out';study=root/'study';out.mkdir();study.mkdir()
            (out/'sealed-source-audit.json').write_text(json.dumps(dict(passed=True,complete_cohort_verified=False,production_score_absent=True)))
            sentinel=root/'score-started'
            commands=[('source-audit',[sys.executable,'-c','pass'],10),
                      ('score',[sys.executable,'-c',f'from pathlib import Path;Path({str(sentinel)!r}).touch()'],10)]
            with self.assertRaisesRegex(AssertionError,'not ready'):
                execute_pipeline(out,study,commands,lambda:None)
            self.assertFalse(sentinel.exists())

    def test_failed_score_prevents_verification(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'out';study=root/'study';out.mkdir();study.mkdir()
            (out/'sealed-source-audit.json').write_text(json.dumps(dict(passed=True,complete_cohort_verified=True,production_score_absent=True)))
            sentinel=root/'verification-started'
            commands=[('source-audit',[sys.executable,'-c','pass'],10),('score',[sys.executable,'-c','raise SystemExit(4)'],10),
                      ('verify',[sys.executable,'-c',f'from pathlib import Path;Path({str(sentinel)!r}).touch()'],10)]
            with self.assertRaisesRegex(AssertionError,'exited 4'):
                execute_pipeline(out,study,commands,lambda:None)
            self.assertFalse(sentinel.exists())

    def test_negative_model_decision_is_still_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'out';study=root/'study';out.mkdir();study.mkdir()
            (out/'sealed-source-audit.json').write_text(json.dumps(dict(passed=True,complete_cohort_verified=True,production_score_absent=True)))
            def script(files):
                return [sys.executable,'-c','import json;from pathlib import Path;'+''.join(f'Path({str(study/k)!r}).write_text({json.dumps(v)!r});' for k,v in files.items())]
            commands=[('source-audit',[sys.executable,'-c','pass'],10),
                      ('score',script({'scoring.json':{'status':'complete'},'result.json':{'decision':'close_frozen_full_only_configuration'}}),10),
                      ('verify',script({'independent-review.json':{'passed':True}}),10)]
            result=execute_pipeline(out,study,commands,lambda:None)
            self.assertEqual(result['decision'],'close_frozen_full_only_configuration')
            self.assertEqual(len(result['stages']),3)

    def test_release_preserves_another_agents_reservation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);file=root/'cores.json';lock=root/'lock'
            file.write_text(json.dumps({'allocation':[dict(owner='fable',cores=[2,3],lease='other')]}))
            self.assertTrue(claim(file,lock,'ours',[0,1]));check_lease(file,'ours',[0,1])
            self.assertFalse(claim(file,lock,'duplicate',[1,4]))
            release(file,lock,'ours')
            self.assertEqual(json.loads(file.read_text())['allocation'],[dict(owner='fable',cores=[2,3],lease='other')])


if __name__=='__main__':unittest.main()
