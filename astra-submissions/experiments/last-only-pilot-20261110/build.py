"""Build a pure playing engine: only reused CFR files and its compile flag differ."""
from datetime import datetime,timezone
import gzip,hashlib,io,json,os
from pathlib import Path
import shutil,subprocess,tarfile,sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/last-only-pilot-20261110'
SHIP=HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
OLD=HERE.parent/'last-only-cfr-20261110'

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
 evidence=ROOT/'astra-submissions/analysis/v38-last-only-cost-20261110'
 decision=json.loads((evidence/'publication-summary.json').read_text());terminal=json.loads((evidence/'terminal-verification.json').read_text())
 assert decision['gate_pass'] and terminal['terminal_exit_code']==0 and terminal['public_summary_sha256']==sha(evidence/'publication-summary.json')
 assert sha(SHIP/'mist')=='14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
 build=HERE/'build';build.mkdir(exist_ok=False);(build/'base').symlink_to(SHIP,target_is_directory=True)
 candidate=build/'candidate';shutil.copytree(SHIP/'src',candidate/'src')
 for name in ('cfr.c','cfr.h'):shutil.copyfile(OLD/f'candidate-{name}',candidate/'src'/name)
 script=(SHIP/'build.sh').read_text();old='FLAGS="-O2 -pthread -D_POSIX_C_SOURCE=199309L"';assert script.count(old)==1
 (candidate/'build.sh').write_text(script.replace(old,'FLAGS="-O2 -pthread -D_POSIX_C_SOURCE=199309L -DASTRA_CFR_LAST_ONLY=1"'))
 shutil.copyfile(SHIP/'run.sh',candidate/'run.sh')
 for name in ('data','bin'):(candidate/name).symlink_to(SHIP/name,target_is_directory=True)
 shutil.copyfile(ROOT.parent/'fow-starter/referee.py',build/'referee.py')
 records=[]
 def run(command,cwd=None):
  result=subprocess.run(list(map(str,command)),cwd=cwd,capture_output=True,text=True,timeout=120)
  records.append(dict(command=list(map(str,command)),cwd=str(cwd) if cwd else None,code=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0,result.stderr
 run(['bash','build.sh'],candidate)
 names=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main'];flags=['-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-DASTRA_CFR_LAST_ONLY=1']
 objects=[];checks=build/'compiler-checks';checks.mkdir()
 for name in names:
  dest=checks/(name+'.o');objects.append(dest);run(['g++','-x','c','-std=c11',*flags,'-c',candidate/'src'/(name+'.c'),'-o',dest])
 run(['g++',*flags,*objects,'-lm','-o',checks/'gpp-c'])
 run(['g++','-x','c++','-std=c++20','-fpermissive','-w',*flags,*[candidate/'src'/(name+'.c') for name in names],'-lm','-o',checks/'gpp-cpp'])
 changed=[]
 for path in (SHIP/'src').iterdir():
  if path.is_file() and path.read_bytes()!=(candidate/'src'/path.name).read_bytes():changed.append('src/'+path.name)
 assert sorted(changed)==['src/cfr.c','src/cfr.h']
 assert (candidate/'run.sh').read_bytes()==(SHIP/'run.sh').read_bytes()
 assert b'pcfr_average is unavailable in a last-iterate-only build' in (candidate/'mist').read_bytes()
 for path in (candidate/'src').glob('*'):
  if path.name not in ('cfr.c','cfr.h'):assert path.read_bytes()==(SHIP/'src'/path.name).read_bytes()
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w') as tar:
  for path in [*sorted((candidate/'src').glob('*')),candidate/'build.sh',candidate/'run.sh']:
   data=path.read_bytes();item=tarfile.TarInfo(str(path.relative_to(candidate)));item.mtime=0;item.size=len(data);tar.addfile(item,io.BytesIO(data))
 (OUT/'source-bundle.tar.gz').write_bytes(gzip.compress(buffer.getvalue(),mtime=0))
 dependencies={str(p):sha(p) for p in [*sorted((candidate/'src').glob('*')),candidate/'build.sh',candidate/'run.sh',candidate/'mist',checks/'gpp-c',checks/'gpp-cpp',SHIP/'mist',SHIP/'run.sh',SHIP/'bin/stockfish',SHIP/'data/history.bin',build/'referee.py',Path(__file__),evidence/'publication-summary.json',evidence/'terminal-verification.json',OUT/'source-bundle.tar.gz']}
 record=dict(at=datetime.now(timezone.utc).isoformat(),commands=records,dependencies=dependencies,changed_source_files=sorted(changed),build_flag='-DASTRA_CFR_LAST_ONLY=1',launcher_unchanged=True,baseline_sha256=sha(SHIP/'mist'),candidate_sha256=sha(candidate/'mist'),stockfish_sha256=sha(SHIP/'bin/stockfish'),history_sha256=sha(SHIP/'data/history.bin'),pure_engine=True,no_diagnostic_hooks=True,source_scope='Only copied CFR source/header and compile flag change. No paired calls, timers, fixed-round hooks, learned heads, guard/model/history changes or published ZIP/version.')
 (OUT/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ('commands','dependencies')},indent=2))

if __name__=='__main__':main()
