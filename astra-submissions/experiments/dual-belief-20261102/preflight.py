from pathlib import Path
import json,os,subprocess
from run import HERE,OUT,sha,write

def main():
 records=[]
 env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
 env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
 for name in ('check','check-san'):
  p=HERE/'build'/name;r=subprocess.run([str(p)],capture_output=True,text=True,timeout=120,env=env)
  rec=dict(binary_sha256=sha(p),name=name,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr);records.append(rec)
  if r.returncode:
   write(OUT/'preflight-failure.json',dict(records=records));raise RuntimeError(rec)
 write(OUT/'native-checks.json',dict(passed=True,records=records,build_sha256=sha(OUT/'build.json')))
 print(json.dumps(dict(passed=True,checks=[json.loads(r['stdout']) for r in records])))
if __name__=='__main__':main()
