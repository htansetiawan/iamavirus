#!/usr/bin/env python3
"""Complete missing measurements after a verified terminal failure; never erase it."""
import hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=Path(sys.argv[1]);plan=json.loads((out/'plan.json').read_text());pins=json.loads((out/'pins.json').read_text())
    assert pins['state']=='failed' and sha(HERE/'build/libtemporal.so')==pins['library_sha256']
    for p,h in pins['sources'].items():assert sha(Path(p))==h
    have={(r['game'],r['arm']) for r in pins['completed']}
    receipt={'startedAt':datetime.now(timezone.utc).isoformat(),'state':'running','original_failed_receipt_sha256':sha(out/'pins.json'),
             'promotion_blocked':'Unresolved original SIGSEGV; retries do not erase a runtime failure.','completed':[]}
    path=out/'diagnostic-completion.json';assert not path.exists();deadline=time.monotonic()+600
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    try:
        for i,case in enumerate(plan['cases']):
            names=list(plan['arms']);order=names[i%3:]+names[:i%3]
            for arm in order:
                if (case['id'],arm) in have:continue
                dest=out/'runs'/f"{case['id']}-{arm}.json"
                if dest.exists():
                    # The failed process wrote a full trace before dying. Keep
                    # that first output, never replace it with a successful retry.
                    assert case['id']=='ze9rzvsl' and arm=='static_context'
                    data=json.loads(dest.read_text());reference=json.loads((out/'debug/optimized-0.json').read_text())
                    assert len(data['decisions'])==case['decisions']
                    assert [r['checksum'] for r in data['updates']]==[r['checksum'] for r in reference['updates']]
                    clean=lambda rows:[{k:v for k,v in r.items() if k!='elapsed_updates'} for r in rows]
                    assert clean(data['decisions'])==clean(reference['decisions'])
                    receipt['completed'].append({'game':case['id'],'arm':arm,'sha256':sha(dest),
                        'update_seconds':data['total_update_seconds'],'wall_seconds':None,'exit_code':-11,
                        'retained_failed_exit_output':True,'note':'Complete original output agrees with the diagnostic repeat; original runtime failure remains.'})
                    path.write_text(json.dumps(receipt,indent=2)+'\n');continue
                cmd=[sys.executable,str(HERE/'trace.py'),'--input',str(out/(case['id']+'.input.json')),
                     '--truth',str(out/(case['id']+'.truth.json')),'--out',str(dest)]
                left=deadline-time.monotonic()
                if left<=0:raise TimeoutError('diagnostic wall cap')
                start=time.monotonic();r=subprocess.run(cmd,env=env|pins['env']|plan['arms'][arm]|{'PYTHONFAULTHANDLER':'1'},capture_output=True,text=True,timeout=min(120,left))
                (out/'runs'/f"{case['id']}-{arm}.completion.stderr").write_text(r.stderr)
                if r.returncode:raise RuntimeError((case['id'],arm,r.returncode,r.stderr))
                data=json.loads(dest.read_text());assert len(data['decisions'])==case['decisions']
                receipt['completed'].append({'game':case['id'],'arm':arm,'sha256':sha(dest),'update_seconds':data['total_update_seconds'],'wall_seconds':time.monotonic()-start})
                path.write_text(json.dumps(receipt,indent=2)+'\n')
                print(case['id'],arm,'diagnostic completed',flush=True)
        receipt['state']='complete'
    except BaseException as e:receipt['state']='failed';receipt['error']=repr(e);raise
    finally:
        receipt['finishedAt']=datetime.now(timezone.utc).isoformat();path.write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
