from pathlib import Path
import difflib,gzip,hashlib,json,shutil,subprocess,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=ROOT/'astra-submissions/analysis/solver-workspace-20261102'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def change(s,a,b,n=1):
 assert s.count(a)==n,(a[:80],s.count(a),n)
 return s.replace(a,b)
def main():
 OUT.mkdir(parents=True,exist_ok=True);build=HERE/'build';base=build/'base';fast=build/'fast'
 archive=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
 assert sha(archive)=='41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
 with zipfile.ZipFile(archive) as z:
  for name in z.namelist():
   if name.endswith('/') or not(name.startswith('src/') or name in ('build.sh','data/history.bin')):continue
   for folder in (base,fast):
    p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
 h=(base/'src/cfr.h').read_text()
 h=change(h,'    int root;','    int root;\n    int allocated_slots, strategy_valid;\n    double *instant; /* reusable instantaneous regrets, n_slots initialized per traversal */')
 (fast/'src/cfr.h').write_text(h)
 s=(base/'src/cfr.c').read_text()
 s=change(s,'    free(g->pending);','    free(g->pending); free(g->instant);')
 s=change(s,'void game_finalize(Game *g) {','''static int slot_capacity(int required) {
    int cap = 64;
    while (cap < required) cap *= 2;
    return cap;
}

void game_finalize(Game *g) {
    g->allocated_slots = slot_capacity(g->n_slots);
    g->strategy_valid = 0;
    g->instant = malloc((size_t)g->allocated_slots * sizeof(double));''')
 s=change(s,'calloc(g->n_slots, sizeof(double))','calloc(g->allocated_slots, sizeof(double))',4)
 s=change(s,'static void apply_pending(Game *g) {','static void apply_pending(Game *g) {\n    if (g->n_pending) g->strategy_valid = 0;')
 start=s.index('void game_grow(Game *g) {');end=s.index('\nvoid game_expand_leaf',start)
 s=s[:start]+'''void game_grow(Game *g) {
    if (g->n_slots <= g->finalized_slots) { apply_pending(g); return; }
    double **arrays[4] = {&g->regret, &g->last, &g->strategy, &g->strategy_sum};
    if (g->n_slots > g->allocated_slots) {
        g->allocated_slots = slot_capacity(g->n_slots);
        for (int i = 0; i < 4; ++i)
            *arrays[i] = realloc(*arrays[i], (size_t)g->allocated_slots * sizeof(double));
        g->instant = realloc(g->instant, (size_t)g->allocated_slots * sizeof(double));
    }
    for (int i = 0; i < 4; ++i)
        memset(*arrays[i] + g->finalized_slots, 0, (size_t)(g->n_slots - g->finalized_slots) * sizeof(double));
    g->finalized_slots = g->n_slots;
    g->strategy_valid = 0;
    apply_pending(g);
}
''' +s[end:]
 s=change(s,'void pcfr_current(const Game *g, double *out) {','''void pcfr_current(const Game *g, double *out) {
    if (g->strategy_valid) {
        if (out != g->strategy) memcpy(out, g->strategy, (size_t)g->n_slots * sizeof(double));
        return;
    }''')
 start=s.index('void pcfr_iteration(Game *g, int t) {');end=s.index('\nstatic double value_of',start)
 old=s[start:end]
 new=change(old,'    double *x = malloc(g->n_slots * sizeof(double)), *inst = malloc(g->n_slots * sizeof(double));','''    double *x = g->strategy, *inst = g->instant;
    if (!g->strategy_valid) {
        pcfr_current(g, x);
        g->strategy_valid = 1;
    }''')
 new=change(new,'        pcfr_current(g, x);\n        memset(inst,','        memset(inst,')
 new=change(new,'                g->strategy_sum[o + a] += (double)t * x[o + a];\n            }','''                g->strategy_sum[o + a] += (double)t * x[o + a];
            }
            /* No other player's regrets changed; its cached strategy remains
             * exactly the profile used by the original alternating update. */
            strategy_of(g, I, x + o);''')
 new=change(new,'    free(x); free(inst);\n','')
 s=s[:start]+new+s[end:]
 (fast/'src/cfr.c').write_text(s)
 patch=''.join(''.join(difflib.unified_diff((base/'src'/n).read_text().splitlines(True),(fast/'src'/n).read_text().splitlines(True),fromfile='v37/src/'+n,tofile='fast/src/'+n)) for n in ('cfr.h','cfr.c'))
 (OUT/'candidate.patch.gz').write_bytes(gzip.compress(patch.encode(),mtime=0))
 functions=['game_init','game_free','game_infoset','game_node','game_children','game_finalize','game_grow','game_expand_leaf','game_start_on','pcfr_iteration','pcfr_current','pcfr_infoset_strategy','pcfr_average','game_value','best_response_value','exploitability']
 records=[]
 def run(cmd,cwd=None):
  r=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,text=True);records.append(dict(command=list(map(str,cmd)),cwd=str(cwd) if cwd else None,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
 for directory in (base,fast):run(['bash','build.sh'],directory)
 for variant,opts in [('opt',['-O2']),('san',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  objects=[]
  for name,directory in [('base',base),('fast',fast)]:
   flags=['-D'+fn+'=base_'+fn for fn in functions] if name=='base' else []
   flags+=['-DAPI_NAME='+name+'_api','-DFAST='+str(int(name=='fast'))]
   for source in (directory/'src/cfr.c',HERE/'wrapper.c'):
    dest=build/(name+'-'+source.stem+'-'+variant+'.o');objects.append(dest)
    run(['gcc','-std=c11',*opts,*flags,'-I',directory/'src','-I',HERE,'-c',source,'-o',dest])
  run(['gcc','-std=c11','-D_POSIX_C_SOURCE=200809L',*opts,'-I',HERE,HERE/'check.c',*objects,'-lm','-o',build/('check-'+variant)])
 diagnostic=build/'diagnostic';shutil.copytree(base/'src',diagnostic,dirs_exist_ok=True)
 shutil.copyfile(HERE/'dump.h',diagnostic/'dump.h')
 s=(diagnostic/'gtcfr.c').read_text();s=change(s,'#include "cfr.h"','#include "cfr.h"\n#include "dump.h"')
 s=change(s,'    free(x); free(idx); free(share); free(chance_kids); free(chance_p);','    solver_dump(&t.g);\n    free(x); free(idx); free(share); free(chance_kids); free(chance_p);')
 (diagnostic/'gtcfr.c').write_text(s)
 run(['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',*sorted(diagnostic.glob('*.c')),'-lm','-o',build/'dump-engine'])
 pins={str(p.relative_to(ROOT)):sha(p) for d in (base,fast) for p in [*sorted((d/'src').glob('*')),d/'mist'] if p.is_file()}
 (OUT/'build.json').write_text(json.dumps(dict(records=records,pins=pins,patch_raw_sha256=hashlib.sha256(patch.encode()).hexdigest()),indent=2)+'\n')
 print(json.dumps(dict(built=True,base=sha(base/'mist'),fast=sha(fast/'mist'))))
if __name__=='__main__':main()
