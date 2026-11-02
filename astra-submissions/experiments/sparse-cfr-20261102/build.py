from pathlib import Path
import difflib,gzip,hashlib,json,shutil,subprocess
from modify import patch,change
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OLD=HERE.parent/'solver-workspace-20261102';OUT=ROOT/'astra-submissions/analysis/sparse-cfr-20261102'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);build=HERE/'build';base=build/'base';fast=build/'fast'
 previous=json.loads((ROOT/'astra-submissions/analysis/solver-workspace-20261102/build.json').read_text())
 for relative,digest in previous['pins'].items():assert sha(ROOT/relative)==digest,relative
 for name,dest in [('base',base),('fast',fast)]:
  shutil.copytree(OLD/'build'/name/'src',dest/'src',dirs_exist_ok=True);shutil.copyfile(OLD/'build'/name/'build.sh',dest/'build.sh')
 for name in ('api.h','wrapper.c','check.c'):shutil.copyfile(OLD/name,HERE/name)
 c,h=patch((fast/'src/cfr.c').read_text(),(fast/'src/cfr.h').read_text());(fast/'src/cfr.c').write_text(c);(fast/'src/cfr.h').write_text(h)
 # Test-only accessors exercise the generation wrap and prove stale clears run.
 api=(HERE/'api.h').read_text();api=change(api,' void *(*load)(const char *);',' void *(*load)(const char *);\n void (*wrap)(void *);\n unsigned long long (*clears)(void *);\n void (*evaluate)(void *,double *);');(HERE/'api.h').write_text(api)
 wrapper=(HERE/'wrapper.c').read_text();wrapper=change(wrapper,'#include <assert.h>','#include <assert.h>\n#include <limits.h>')
 marker='const SolverAPI API_NAME='
 wrapper=change(wrapper,marker,'''static void wrap(void *p){
#if FAST
 ((Game*)p)->sparse_epoch=UINT_MAX;
#else
 (void)p;
#endif
}
static unsigned long long clears(void *p){
#if FAST
 return ((Game*)p)->sparse_prediction_clears;
#else
 (void)p;return 0;
#endif
}
static void evaluate(void *p,double *out){
 Game *g=p;double *x=malloc((g->n_slots?g->n_slots:1)*sizeof(double));pcfr_current(g,x);
 out[0]=game_value(g,x);out[1]=best_response_value(g,x,0);out[2]=best_response_value(g,x,1);free(x);
}
const SolverAPI API_NAME=''')
 wrapper=change(wrapper,'step,state,value,storage,load};','step,state,value,storage,load,wrap,clears,evaluate};');(HERE/'wrapper.c').write_text(wrapper)
 check=(HERE/'check.c').read_text();check=change(check,'static uint64_t rng=253;','static unsigned long long cleared=0;\nstatic uint64_t rng=254;')
 check=change(check,'static void destroy(Pair *p){','static void destroy(Pair *p){cleared+=fast_api.clears(p->f);')
 check=change(check,'   base_api.step(p.b,t);fast_api.step(p.f,t);compare(&p);','   if(t%17==0){base_api.wrap(p.b);fast_api.wrap(p.f);}\n   base_api.step(p.b,t);fast_api.step(p.f,t);compare(&p);')
 check=change(check,'  destroy(&p);\n }','  if(seed%8==0){double a[3],b[3];base_api.evaluate(p.b,a);fast_api.evaluate(p.f,b);assert(!memcmp(a,b,sizeof(a)));}\n  destroy(&p);\n }')
 check=change(check,'base_api.step(terminal.b,1);fast_api.step(terminal.f,1);','base_api.wrap(terminal.b);fast_api.wrap(terminal.f);base_api.step(terminal.b,1);fast_api.step(terminal.f,1);')
 check=change(check,' printf("{\\"passed\\":true,',' assert(cleared>0);\n fprintf(stderr,"stale predictions cleared: %llu\\n",cleared);\n printf("{\\"passed\\":true,')
 (HERE/'check.c').write_text(check)
 diff=''.join(''.join(difflib.unified_diff((base/'src'/n).read_text().splitlines(True),(fast/'src'/n).read_text().splitlines(True),fromfile='v37/src/'+n,tofile='sparse/src/'+n)) for n in ('cfr.c','cfr.h'))
 (OUT/'candidate.patch.gz').write_bytes(gzip.compress(diff.encode(),mtime=0))
 negative=build/'negative';shutil.copytree(fast/'src',negative,dirs_exist_ok=True)
 n=(negative/'cfr.c').read_text();n=change(n,'            memset(g->last + o, 0, (size_t)n * sizeof(double));','            /* Injected test defect: stale prediction is not cleared. */');(negative/'cfr.c').write_text(n)
 functions=['game_init','game_free','game_infoset','game_node','game_children','game_finalize','game_grow','game_expand_leaf','game_start_on','pcfr_iteration','pcfr_current','pcfr_infoset_strategy','pcfr_average','game_value','best_response_value','exploitability'];records=[]
 def run(cmd,cwd=None):
  r=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,text=True);records.append(dict(command=list(map(str,cmd)),cwd=str(cwd) if cwd else None,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
 for d in (base,fast):run(['bash','build.sh'],d)
 for variant,options in [('opt',['-O2']),('san',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']),('negative',['-O2'])]:
  objects=[]
  for name,d in [('base',base/'src'),('fast',negative if variant=='negative' else fast/'src')]:
   flags=['-D'+fn+'=base_'+fn for fn in functions] if name=='base' else []
   flags+=['-DAPI_NAME='+name+'_api','-DFAST='+str(int(name=='fast'))]
   for source in (d/'cfr.c',HERE/'wrapper.c'):
    dest=build/(name+'-'+source.stem+'-'+variant+'.o');objects.append(dest);run(['gcc','-std=c11',*options,*flags,'-I',d,'-I',HERE,'-c',source,'-o',dest])
  run(['gcc','-std=c11','-D_POSIX_C_SOURCE=200809L',*options,'-I',HERE,HERE/'check.c',*objects,'-lm','-o',build/('check-'+variant)])
 pins={str(p.relative_to(ROOT)):sha(p) for d in (base,fast) for p in [*sorted((d/'src').glob('*')),d/'mist'] if p.is_file()}
 (OUT/'build.json').write_text(json.dumps(dict(records=records,pins=pins,patch_raw_sha256=hashlib.sha256(diff.encode()).hexdigest(),parent_build_sha256=sha(ROOT/'astra-submissions/analysis/solver-workspace-20261102/build.json')),indent=2)+'\n')
 print(json.dumps(dict(built=True,base=sha(base/'mist'),fast=sha(fast/'mist'))))
if __name__=='__main__':main()
