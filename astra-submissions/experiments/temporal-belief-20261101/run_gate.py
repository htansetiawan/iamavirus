#!/usr/bin/env python3
import argparse,hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);args=ap.parse_args();out=args.directory
    plan=json.loads((out/'plan.json').read_text());runs=out/'runs';runs.mkdir(exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    common={'MIST_MODEL_TEMP':'2','MIST_THREADS':'2','MIST_MODEL_FULL_BELOW':'1000000000'}
    source=[HERE/'trace.py',HERE/'run_gate.py',HERE/'api.c',HERE/'packed.h',HERE/'native/belief.c',HERE/'native/belief.h',HERE.parent/'temporal-prior-20261101/learned.h']
    pins={'startedAt':datetime.now(timezone.utc).isoformat(),'state':'running','pid_namespace_local':os.getpid(),
          'plan_sha256':sha(out/'plan.json'),'library_sha256':sha(HERE/'build/libtemporal.so'),'sources':{str(p):sha(p) for p in source},
          'env':common,'case_count':len(plan['cases']),'arms':plan['arms'],'wall_cap_seconds':3600,'per_arm_cap_seconds':120,'completed':[]}
    (out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n');deadline=time.monotonic()+3600
    try:
        for i,case in enumerate(plan['cases']):
            for suffix in ['input','truth']:assert sha(out/(case['id']+'.'+suffix+'.json'))==case[suffix+'_sha256']
            names=list(plan['arms']);order=names[i%3:]+names[:i%3]
            for arm in order:
                result=runs/f"{case['id']}-{arm}.json"
                cmd=[sys.executable,str(HERE/'trace.py'),'--input',str(out/(case['id']+'.input.json')),
                     '--truth',str(out/(case['id']+'.truth.json')),'--out',str(result),'--cap',str(plan['cap']),'--seed',str(plan['seed'])]
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError('full-panel wall cap')
                start=time.monotonic();r=subprocess.run(cmd,env=env|common|plan['arms'][arm],capture_output=True,text=True,timeout=min(120,remaining))
                (runs/f"{case['id']}-{arm}.stderr").write_text(r.stderr)
                if r.returncode:raise RuntimeError((case['id'],arm,r.returncode,r.stderr))
                data=json.loads(result.read_text());assert len(data['decisions'])==case['decisions']
                item={'game':case['id'],'arm':arm,'wall_seconds':time.monotonic()-start,'update_seconds':data['total_update_seconds'],'sha256':sha(result)}
                pins['completed'].append(item);(out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
            print(json.dumps({'complete_cases':i+1,'game':case['id'],'opponent':case['opponent'],'runs':len(pins['completed'])}),flush=True)
        pins['state']='complete'
    except BaseException as e:
        pins['state']='failed';pins['error']=repr(e);raise
    finally:
        pins['finishedAt']=datetime.now(timezone.utc).isoformat();(out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n')
if __name__=='__main__':main()
