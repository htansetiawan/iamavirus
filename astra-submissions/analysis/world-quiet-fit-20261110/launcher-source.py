from pathlib import Path
from datetime import datetime,timezone
import fcntl,json,os,signal,subprocess,time,uuid
ROOT=Path('/home/henrytan/git/iamavirus');OUT=ROOT/'astra-submissions/analysis/world-quiet-fit-20261110';HERE=ROOT/'astra-submissions/experiments/world-quiet-attention-20261110'
CORES=ROOT/'chatroom/cores.json';LOCK=Path('/tmp/iamavirus-cores-json.lock');lease=uuid.uuid4().hex
now=lambda:datetime.now(timezone.utc).isoformat()
def save(path,value):
    temp=path.with_name('.'+path.name+'-'+lease);temp.write_text(json.dumps(value,indent=2)+'\n');os.replace(temp,path)
def probe():
    gpu=subprocess.run(['nvidia-smi','--id=0','--query-gpu=name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    apps=subprocess.run(['nvidia-smi','--id=0','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    name,memory,util=[v.strip() for v in gpu.split(',')]
    record=dict(at=now(),name=name,memory_mib=int(memory),util_percent=int(util),compute_apps=apps)
    record['free']=record['memory_mib']<2048 and record['util_percent']<10 and not apps
    return record
def reserve(remove=False):
    with LOCK.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX);state=json.loads(CORES.read_text())
        if remove:state['allocation']=[r for r in state['allocation'] if r.get('lease')!=lease]
        else:
            assert not any(set(r.get('cores',[]))&{2,3} for r in state['allocation'])
            state['allocation'].append(dict(owner='astra',cores=[2,3],gpu=0,lease=lease,purpose='320 fixed development fit and one full CPU checkpoint review'))
        state['updated']=now();save(CORES,state)
assert not (OUT/'execution.json').exists() and not (OUT/'runner-execution.json').exists()
checks=[probe()]
if checks[0]['free']:
    time.sleep(5);checks.append(probe())
save(OUT/'gpu-admission.json',dict(checks=checks,services_stopped=False))
if len(checks)!=2 or not all(v['free'] for v in checks):
    print(json.dumps(dict(status='deferred_gpu_busy',model_fit_attempted=False,checks=checks)),flush=True);raise SystemExit(0)
reserve();state=dict(status='running',started_at=now(),pid=os.getpid(),lease=lease,source_publication='f993c81d89eda2b9aa55f01d0a32033a5008c69d',stages=[],services_stopped=False)
save(OUT/'runner-execution.json',state);started=time.monotonic()
try:
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
    for stage,bound in [('fit',1220),('verify_fit',620)]:
        state['phase']=stage;save(OUT/'runner-execution.json',state);tick=time.monotonic()
        with (OUT/(stage+'.stdout')).open('x') as output,(OUT/(stage+'.stderr')).open('x') as error:
            child=subprocess.Popen(['taskset','-c','2,3',str(ROOT/'.venv/bin/python'),str(HERE/(stage+'.py'))],cwd=ROOT,env=env,stdout=output,stderr=error,start_new_session=True)
            try:code=child.wait(timeout=bound)
            except BaseException:
                if child.poll() is None:
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                raise
        record=dict(stage=stage,code=code,seconds=time.monotonic()-tick);state['stages'].append(record);save(OUT/'runner-execution.json',state);print(json.dumps(record),flush=True)
        assert code==0,stage+' failed; no automatic retry'
    assert json.loads((OUT/'independent-review.json').read_text())['passed']
    state.update(status='complete',phase='reviewed')
except BaseException as error:
    state.update(status='failed',error=repr(error));raise
finally:
    reserve(remove=True);state.update(ended_at=now(),seconds=time.monotonic()-started,own_lease_released=True);save(OUT/'runner-execution.json',state)
print(json.dumps(state,indent=2),flush=True)
