from pathlib import Path
from datetime import datetime,timezone
import fcntl,json,os,signal,subprocess,time,uuid
ROOT=Path('/home/henrytan/git/iamavirus');OUT=ROOT/'astra-submissions/analysis/quiet-prior-sequential-20261110';HERE=ROOT/'astra-submissions/experiments/quiet-prior-sequential-20261110';CORES=ROOT/'chatroom/cores.json';LOCK=Path('/tmp/iamavirus-cores-json.lock');lease=uuid.uuid4().hex
now=lambda:datetime.now(timezone.utc).isoformat()
def save(path,obj):
    temp=path.with_name('.'+path.name+'-'+lease);temp.write_text(json.dumps(obj,indent=2)+'\n');os.replace(temp,path)
def reserve(remove=False):
    with LOCK.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX);obj=json.loads(CORES.read_text())
        if remove:obj['allocation']=[r for r in obj['allocation'] if r.get('lease')!=lease]
        else:
            assert not any(set(r.get('cores',[]))&{2,3} for r in obj['allocation'])
            obj['allocation'].append(dict(owner='astra',cores=[2,3],lease=lease,purpose='323 one fixed48-game/2seed original-zero-learned sequential study and independent raw audit'))
        obj['updated']=now();save(CORES,obj)
assert not (OUT/'execution.json').exists() and not (OUT/'runner-execution.json').exists()
reserve();state=dict(status='running',started_at=now(),namespace_pid=os.getpid(),pid_scope='exec sandbox namespace; original tool handle is authoritative',source_publication='7fbcb96386b24241a7019ea94a97763b0ed95c7c',lease=lease,stages=[]);save(OUT/'runner-execution.json',state);started=time.monotonic()
try:
    for stage,bound in [('run',2720),('review',600)]:
        state['phase']=stage;save(OUT/'runner-execution.json',state);tick=time.monotonic()
        with (OUT/(stage+'.stdout')).open('x') as output,(OUT/(stage+'.stderr')).open('x') as error:
            child=subprocess.Popen(['taskset','-c','2,3',str(ROOT/'.venv/bin/python'),str(HERE/(stage+'.py'))],cwd=ROOT,stdout=output,stderr=error,start_new_session=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
            try:code=child.wait(timeout=bound)
            except BaseException:
                if child.poll() is None:
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                raise
        item=dict(stage=stage,code=code,seconds=time.monotonic()-tick);state['stages'].append(item);save(OUT/'runner-execution.json',state);print(json.dumps(item),flush=True)
        assert code==0,stage+' failed; no automatic retry'
    assert json.loads((OUT/'independent-review.json').read_text())['passed']
    state.update(status='complete',phase='reviewed',decision=json.loads((OUT/'result.json').read_text())['decision'])
except BaseException as error:
    state.update(status='failed',error=repr(error));raise
finally:
    reserve(remove=True);state.update(ended_at=now(),seconds=time.monotonic()-started,own_lease_released=True);save(OUT/'runner-execution.json',state)
print(json.dumps(state,indent=2),flush=True)
