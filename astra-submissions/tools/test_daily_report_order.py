"""Isolated shell integration: a later exporter kill cannot preempt publication."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


class ReportOrder(unittest.TestCase):
    def exercise(self,kill):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in ('tools','bin','.venv/bin','data/raw','store/raw-archive','mist/tools'):(root/name).mkdir(parents=True,exist_ok=True)
            (root/'tools/daily_refresh.sh').write_bytes((ROOT/'tools/daily_refresh.sh').read_bytes())
            (root/'data/raw/accepted.jsonl').write_text('{"id":"fixture"}\n')
            (root/'mist/tools/export_moves.py').write_text('# fake exporter\n')
            driver=root/'driver.py'
            driver.write_text('''#!/usr/bin/python3
import json,os,signal,sys,time
from pathlib import Path
root=Path(os.environ['ORDER_ROOT']);args=sys.argv[1:]
with (root/'actions.jsonl').open('a') as f:f.write(json.dumps(args)+'\\n')
if any(s in args for s in ['learning.daily_report','learning.daily_insights','learning.scorecard','astra-submissions/tools/daily_intel_status.py']):
 p=root/'data/reports/daily';p.mkdir(parents=True,exist_ok=True)
 for n in ['2026-11-09.md','2026-11-09.json','latest.md','insights-2026-11-09.md','insights-latest.md','scorecard-2026-11-09.md','scorecard-latest.md','intel-2026-11-09.md','intel-2026-11-09.json','intel-latest.md','intel-latest.json']:(p/n).write_text('fixture\\n')
if any(s.endswith('export_moves.py') for s in args) and os.environ['ORDER_KILL']=='1':
 os.kill(os.getppid(),signal.SIGTERM);time.sleep(.05)
''')
            driver.chmod(0o755)
            (root/'.venv/bin/python').symlink_to(driver);(root/'bin/python3').symlink_to(driver)
            commands={
                'git':'''#!/bin/bash
printf 'git %s\\n' "$*" >>"$ORDER_ROOT/shell-actions"
if [ "$1" = diff ]; then exit 1; fi
exit 0
''',
                'rsync':'''#!/bin/bash
echo rsync >>"$ORDER_ROOT/shell-actions"
''',
                'date':'''#!/bin/bash
case "$*" in *%H*) echo 12:00:00;; *) echo 2026-11-09;; esac
'''}
            for name,text in commands.items():p=root/'bin'/name;p.write_text(text);p.chmod(0o755)
            (root/'tools/push_safe.sh').write_text('''#!/bin/bash
echo '["published"]' >>"$ORDER_ROOT/actions.jsonl"
''')
            env=dict(os.environ,PATH=str(root/'bin')+':'+os.environ['PATH'],STORE=str(root/'store'),MIST_C=str(root/'mist'),
                     ORDER_ROOT=str(root),ORDER_KILL='1' if kill else '0')
            result=subprocess.run(['bash',str(root/'tools/daily_refresh.sh')],env=env,capture_output=True,text=True,timeout=10)
            actions=[json.loads(line) for line in (root/'actions.jsonl').read_text().splitlines()]
            published=actions.index(['published']);export=next(i for i,a in enumerate(actions) if any(s.endswith('export_moves.py') for s in a))
            self.assertLess(published,export)
            for name in ['learning.daily_report','learning.daily_insights','learning.scorecard']:
                self.assertLess(next(i for i,a in enumerate(actions) if name in a),published)
            self.assertTrue((root/'data/reports/daily/latest.md').exists())
            if kill:
                self.assertIn(result.returncode,(-15,143))
                self.assertFalse(any('learning.dataset' in a for a in actions))
            else:
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertTrue(any('learning.dataset' in a for a in actions))
                self.assertTrue(any('tools/mirror_raw.py' in a for a in actions))

    def test_exporter_terminates_service_after_publication(self):self.exercise(True)
    def test_successful_run_publishes_then_exports_and_archives(self):self.exercise(False)


if __name__=='__main__':unittest.main()
