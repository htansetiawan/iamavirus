from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess

root=Path('/home/henrytan/git/iamavirus');out=root/'astra-submissions/analysis/native-fow-value-20261102'
assert json.loads((out/'dataset-review.json').read_text())['passed']
assert json.loads((out/'training-preflight.json').read_text())['training_started'] is False
assert not (root/'astra-submissions/experiments/native-fow-value-20261102/work/training').exists()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
assert not apps, 'GPU occupied; do not start'
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
now=datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cores=root/'chatroom/cores.json';d=json.loads(cores.read_text())
assert not any(a['owner']!='astra' and set(a['cores'])&{2,3} for a in d['allocation'])
d['allocation']=[a for a in d['allocation'] if not(a['owner']=='astra' and a['task'].startswith('237'))]
d['allocation'].append({'owner':'astra','cores':[2,3],'task':'237 one bounded teacher/direct-student/distilled-student training run','until':'release only after original training handle terminal','gpu':'RTX PRO 5000 exclusively; fresh probe found no compute processes; internal3600s/external3700s cap'})
d['updated']=now;cores.write_text(json.dumps(d,indent=2)+'\n')
with (out/'gpu-start.json').open('x') as f:json.dump({'at':now,'free_compute_device':True,'competing_compute_apps':apps,'gpu':gpu,'plan_sha256':sha(out/'plan.json'),'data_review_sha256':sha(out/'dataset-review.json'),'publication_before_extraction':'33b41cce7a35d11cdf39f62d58f02cad1290ba83','launcher_pid':os.getpid(),'no_existing_service_stopped':True},f,indent=2)
env=dict(os.environ);env['OMP_NUM_THREADS']='2';env['MKL_NUM_THREADS']='2'
os.execve('/usr/bin/timeout',['timeout','--signal=TERM','--kill-after=10s','3700s','/usr/bin/taskset','-c','2,3',str(root/'.venv/bin/python'),str(root/'astra-submissions/experiments/native-fow-value-20261102/train.py')],env)
