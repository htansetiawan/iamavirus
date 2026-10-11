from pathlib import Path
from datetime import datetime,timezone
import subprocess,sys,os,json,hashlib,time
root=Path('/media/henrytan/seagate/iamavirus/astra/ssl-transfer-20261011');code=Path(__file__).parent
lease=Path('/tmp/gpu_queue/claimed_by');owner='astra ssl-transfer-20261011 '+datetime.now(timezone.utc).isoformat()
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();mem,util=map(int,gpu.split(','))
if mem>2048 or util>5:raise RuntimeError('GPU is no longer idle: '+gpu)
with lease.open('x') as f:f.write(owner+'\n')
(root/'executed-launch.py').write_bytes(Path(__file__).read_bytes())
env=dict(os.environ,PYTHONPATH=str(code/'astra-submissions')+':'+str(code),OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
python='/home/henrytan/git/iamavirus/.venv/bin/python';status={'owner':owner,'pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),'arms':[],'state':'running'}
def save():(root/'pair-status.json').write_text(json.dumps(status,indent=2)+'\n')
save()
try:
 for name,extra in [('ssl-plus-1000',['--steps','1000','--initialize','/media/henrytan/seagate/iamavirus/astra/representations/v3-seed253/attention-ssl-pilot-v2/step-001000.pt']),('supervised-2500',['--steps','2500','--resume'])]:
  cmd=[python,'-m','learning_experiments.run','--manifest',str(code/'manifest.json'),'--variant','attention','--phase','supervised','--device','cuda','--threads','2','--seed','253','--window','32','--batch','4','--validation-games','64','--evaluate-every','250','--output',str(root/name)]+extra
  start=time.monotonic();record={'name':name,'command':cmd,'started_at':datetime.now(timezone.utc).isoformat()};status['arms'].append(record);save()
  with (root/(name+'.log')).open('w') as log:
   p=subprocess.Popen(cmd,cwd=code,env=env,stdout=log,stderr=subprocess.STDOUT);record['pid']=p.pid;save();code_status=p.wait(timeout=1800)
  record.update(returncode=code_status,wall_seconds=time.monotonic()-start);save();print(json.dumps(record),flush=True)
  if code_status:raise RuntimeError(name+' failed, see retained log')
 status['state']='complete'
except BaseException as e:
 status.update(state='failed',error=str(e));raise
finally:
 status['ended_at']=datetime.now(timezone.utc).isoformat();save()
 if lease.exists() and lease.read_text().strip()==owner:lease.unlink()
