from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, sys, time
root=Path('/home/henrytan/git/iamavirus');sys.path.insert(0,str(root))
from learning.compare_archives import kill_tree
out=root/'astra-submissions/analysis/posterior-fit-20261102'
start=time.monotonic()
with (out/'run.stdout').open('x') as stdout,(out/'run.stderr').open('x') as stderr:
 p=subprocess.Popen([str(root/'.venv/bin/python'),'-u',str(root/'astra-submissions/experiments/posterior-fit-20261102/run.py')],cwd=root,stdout=stdout,stderr=stderr,start_new_session=True)
 receipt={'at':datetime.now(timezone.utc).isoformat(),'parent_pid':os.getpid(),'pid':p.pid,'published_commit':'de827f52b0f36e7f9158e4b93843238b8be6fb3e','proc_start_ticks':Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21]}
 with (out/'launch.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps(receipt),flush=True)
 try:p.wait(timeout=2760)
 except BaseException:
  kill_tree(p.pid);p.wait();raise
 receipt.update(exit=p.returncode,elapsed=time.monotonic()-start,ended=datetime.now(timezone.utc).isoformat())
 with (out/'launcher-terminal.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps(receipt),flush=True)
 sys.exit(p.returncode)
