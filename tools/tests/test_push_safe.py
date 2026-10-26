"""Unattended pushes select a scoped credential without changing gh accounts."""
import json
import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize("explicit,diverged", [(False, False), (True, False), (False, True)])
def test_scoped_credentials_and_non_force_push(tmp_path, explicit, diverged):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    git = bindir / "git"
    git.write_text('''#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
with open(os.environ['CALL_LOG'], 'a') as f:
    f.write(json.dumps({'tool':'git','args':a})+'\\n')
if a == ['rev-parse','--show-toplevel']: print(os.environ['FAKE_ROOT'])
elif a[:2] == ['remote','get-url']:
    print('https://github.com/'+('henryatharvard' if a[-1]=='harvard' else 'htansetiawan')+'/iamavirus.git')
elif a[:1] == ['merge-base']: sys.exit(int(os.environ['DIVERGED']))
elif a[:1] in (['fetch'],['push']):
    expected = 'fake-private' if a[-2:] == ['harvard','main'] else os.environ['EXPECTED_ORIGIN_TOKEN']
    if os.environ.get('GH_TOKEN') != expected: sys.exit(31)
elif a[:1] == ['log']: print('fake-commit')
''')
    gh = bindir / "gh"
    gh.write_text('''#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
with open(os.environ['CALL_LOG'], 'a') as f:
    f.write(json.dumps({'tool':'gh','args':a})+'\\n')
if a == ['auth','token','--user','htansetiawan']: print('fake-owner')
elif a == ['auth','token','--user','henryatharvard']: print('fake-private')
else: sys.exit(32)
''')
    git.chmod(0o755)
    gh.chmod(0o755)
    env = os.environ.copy()
    env.pop('GH_TOKEN', None)
    env.update(PATH=str(bindir) + os.pathsep + env['PATH'], FAKE_ROOT=str(tmp_path),
               CALL_LOG=str(tmp_path / 'calls.jsonl'), DIVERGED=str(int(diverged)),
               EXPECTED_ORIGIN_TOKEN='fake-explicit' if explicit else 'fake-owner')
    if explicit:
        env['GH_TOKEN'] = 'fake-explicit'
    script = Path(__file__).resolve().parents[1] / 'push_safe.sh'
    result = subprocess.run(['bash', str(script)], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in (tmp_path / 'calls.jsonl').read_text().splitlines()]
    gh_calls = [r['args'] for r in calls if r['tool'] == 'gh']
    assert (['auth','token','--user','htansetiawan'] in gh_calls) == (not explicit)
    assert all(a[:2] == ['auth', 'token'] for a in gh_calls)
    git_calls = [r['args'] for r in calls if r['tool'] == 'git']
    assert (['rebase','-q','--autostash','origin/main'] in git_calls) == diverged
    assert ['push','-q','origin','main'] in git_calls
    assert ['push','-q','harvard','main'] in git_calls
    assert not any('force' in arg for args in git_calls for arg in args)
    assert 'fake-owner' not in result.stdout + result.stderr
    assert 'fake-explicit' not in result.stdout + result.stderr
