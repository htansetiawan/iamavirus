"""Three Game layouts stay private; one unchanged front end and shared belief."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import shutil,subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/v38-last-only-cost-20261110'
OLD=HERE.parent/'last-only-cfr-20261110'
SHIP=HERE.parent/'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def once(text,a,b):
 assert text.count(a)==1,(a,text.count(a));return text.replace(a,b)

def main():
 assert json.loads((ROOT/'astra-submissions/analysis/last-only-cfr-20261110/independent-review.json').read_text())['passed']
 plan=json.loads((ROOT/'astra-submissions/analysis/last-only-cfr-20261110/plan.json').read_text())
 for path,value in plan['dependencies'].items():assert sha(path)==value,path
 build=HERE/'build';build.mkdir(exist_ok=False)
 records=[];objects=[];symbols=['game_init','game_free','game_infoset','game_node','game_children','game_finalize','game_grow','game_expand_leaf','game_start_on','pcfr_iteration','pcfr_current','pcfr_infoset_strategy','pcfr_average','game_value','best_response_value','exploitability','gtcfr_decide']
 def compile(cmd):
  result=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=60)
  records.append(dict(command=list(map(str,cmd)),code=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0,result.stderr
 flags=['-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=200809L']
 for arm in ('base','cached','last'):
  dest=build/arm;shutil.copytree(SHIP/'src',dest)
  if arm!='base':
   for name in ('cfr.c','cfr.h'):shutil.copyfile(OLD/f'candidate-{name}',dest/name)
  p=dest/'gtcfr.c';text=p.read_text()
  original='    while (!async && seconds_since(&t0) < params->seconds * 0.85) {'
  changed='''    const char *astra_fixed = getenv("ASTRA_FIXED_ROUNDS");
    int astra_round = 0;
    while (!async && (astra_fixed ? astra_round++ < atoi(astra_fixed) : seconds_since(&t0) < params->seconds * 0.85)) {'''
  p.write_text(once(text,original,changed))
  names=['cfr','gtcfr']
  if arm=='base':names+=['board','belief','movemodel','eval','search','front','sfeval','main']
  if arm=='base':
   p=dest/'main.c';text=p.read_text();text=once(text,'#include "gtcfr.h"','#include "gtcfr.h"\n#include "front.h"\nint astra_three_way(const Belief *,const GtcfrParams *,const Front *,const char *,const MoveList *,SearchResult *);');p.write_text(once(text,'gtcfr_decide(&b, &gp, &r)','astra_three_way(&b, &gp, &front, view, &allowed, &r)'))
   with (dest/'main.c').open('a') as stream:stream.write('\n/* Diagnostic: apply the unmodified front-end acceptance rule to each arm. */\nMove astra_front_effective(const Belief *b,const Front *f,const char *view,const MoveList *allowed,Move move){\n if(allowed->count>0){\n  int found=0;for(int i=0;i<allowed->count;++i)found|=allowed->moves[i]==move;\n  if(!found&&!b->overflowed)found=legal_everywhere(b,move);\n  if(!found)return front_best_allowed(f,view,allowed);\n }\n return move;\n}\n')
   with (dest/'sfeval.c').open('a') as stream:stream.write('\n/* Diagnostic getter; does not change worker behavior. */\nint astra_sf_restarts(void){return restarts;}\n')
  for name in names:
   rename=[] if arm=='base' else ['-D'+s+'='+arm+'_'+s for s in symbols]
   define=['-DASTRA_CFR_LAST_ONLY=1'] if arm=='last' else []
   obj=build/f'{arm}-{name}.o';objects.append(obj)
   compile(['gcc',*flags,*rename,*define,'-I',dest,'-c',dest/(name+'.c'),'-o',obj])
 compile(['gcc',*flags,'-I',build/'base',HERE/'compare.c',*objects,'-lm','-o',build/'compare'])
 # Publish a small complete source bundle; binaries and replay data stay local.
 import gzip,io,tarfile
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w') as tar:
  for p in sorted(build.glob('*/*')):
   if p.is_file():
    data=p.read_bytes();info=tarfile.TarInfo(str(p.relative_to(build)));info.size=len(data);info.mtime=0;tar.addfile(info,io.BytesIO(data))
 (OUT/'source-bundle.tar.gz').write_bytes(gzip.compress(buffer.getvalue(),mtime=0))
 dependencies={str(p):sha(p) for p in [HERE/'build.py',HERE/'compare.c',*sorted(build.glob('*/*')),build/'compare',OUT/'source-bundle.tar.gz'] if p.is_file()}
 (OUT/'build.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),commands=records,dependencies=dependencies,binary_sha256=sha(build/'compare'),source='Original v38 common front end; separate original/cached/last-only CFR+GT-CFR modules. Only diagnostic hook, fixed-work condition and SF restart getter added. Unmodified conditional time branch for measured searches.'),indent=2)+'\n')
 print(json.dumps(dict(built=True,commands=len(records),binary_sha256=sha(build/'compare'))))

if __name__=='__main__':main()
