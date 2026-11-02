from pathlib import Path
import hashlib,json,os,subprocess,zipfile
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/history-mixture-20261102'
os.sched_setaffinity(0,{0,1})
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=HERE/'build';build.mkdir(exist_ok=True)
archive=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
assert sha(archive)=='41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
with zipfile.ZipFile(archive) as z:
 for name in z.namelist():
  if name.startswith('src/') and not name.endswith('/') or name=='data/history.bin':
   p=build/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(z.read(name))
src=build/'src';common=['gcc','-std=c11','-D_POSIX_C_SOURCE=199309L','-pthread','-I',str(src)]
deps=[str(src/'board.c'),str(src/'movemodel.c')]
commands=[common+['-O2','-shared','-fPIC',str(HERE/'filter.c'),*deps,'-lm','-o',str(build/'filter.so')],
          common+['-O2',str(HERE/'check.c'),*deps,'-lm','-o',str(build/'check')],
          common+['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(HERE/'check.c'),*deps,'-lm','-o',str(build/'check-san')]]
records=[]
for cmd in commands:
 r=subprocess.run(cmd,capture_output=True,text=True);records.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
 assert r.returncode==0,r.stderr
env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))};env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
for name in ('check','check-san'):
 r=subprocess.run([str(build/name)],capture_output=True,text=True,env=env,timeout=120);records.append(dict(command=name,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
 if r.returncode:
  (OUT/'native-check-failure.json').write_text(json.dumps(records,indent=2)+'\n');raise RuntimeError((name,r.returncode,r.stderr))
pins={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'filter.c',HERE/'check.c',Path(__file__),HERE/'README.md',build/'filter.so',build/'data/history.bin']}
(OUT/'native-checks.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),passed=True,records=records,pins=pins),indent=2)+'\n')
print(json.dumps(dict(passed=True,results=[r['stdout'] for r in records if r['stdout']])),flush=True)
