"""Correctness-only last-iterate CFR specialization, reusing audited253/254."""
from datetime import datetime,timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD=HERE.parent/'sparse-cfr-20261102'
OUT=ROOT/'astra-submissions/analysis/last-only-cfr-20261110'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def change(text,a,b,n=1):
    assert text.count(a)==n,(a,text.count(a));return text.replace(a,b)


def main():
    build=HERE/'build';build.mkdir(exist_ok=False)
    before=json.loads((ROOT/'astra-submissions/analysis/sparse-cfr-20261102/build.json').read_text())
    for name in ('base','fast'):
        for path in sorted((OLD/'build'/name/'src').glob('*')):
            if path.is_file():assert sha(path)==before['pins'][str(path.relative_to(ROOT))]
        dest=build/name;dest.mkdir();shutil.copyfile(OLD/'build'/name/'src/cfr.c',dest/'cfr.c');shutil.copyfile(OLD/'build'/name/'src/cfr.h',dest/'cfr.h')
    base=build/'base';fast=build/'fast';text=(fast/'cfr.c').read_text()
    text=change(text,'#include "cfr.h"','#include "cfr.h"\n#include <stdio.h>\n#ifndef ASTRA_CFR_LAST_ONLY\n#define ASTRA_CFR_LAST_ONLY 0\n#endif')
    text=change(text,'    g->strategy_sum = calloc(g->allocated_slots, sizeof(double));','''#if !ASTRA_CFR_LAST_ONLY
    g->strategy_sum = calloc(g->allocated_slots, sizeof(double));
#endif''')
    text=change(text,'    double **arrays[4] = {&g->regret, &g->last, &g->strategy, &g->strategy_sum};','''    double **arrays[4] = {&g->regret, &g->last, &g->strategy, &g->strategy_sum};
    const int array_count = ASTRA_CFR_LAST_ONLY ? 3 : 4;''')
    text=change(text,'for (int i = 0; i < 4; ++i)','for (int i = 0; i < array_count; ++i)',2)
    text=change(text,'void pcfr_average(const Game *g, double *out) {','''void pcfr_average(const Game *g, double *out) {
#if ASTRA_CFR_LAST_ONLY
    /* Never return a bogus uniform average, including in NDEBUG builds. */
    (void)g; (void)out;
    fputs("pcfr_average is unavailable in a last-iterate-only build\\n", stderr);
    abort();
#else''')
    text=change(text,'\n}\n\n/* Counterfactual traversal','\n#endif\n}\n\n/* Counterfactual traversal')
    anchor='''        for (int I = 0; I < g->n_infosets; ++I) {
            if (g->is_player[I] != player) continue;
            const int o = g->is_offset[I], n = g->is_actions[I];
            for (int a = 0; a < n; ++a)
                g->strategy_sum[o + a] += (double)t * x[o + a];
        }'''
    text=change(text,anchor,'#if !ASTRA_CFR_LAST_ONLY\n'+anchor+'\n#else\n        (void)t;\n#endif')
    (fast/'cfr.c').write_text(text)
    header=(fast/'cfr.h').read_text();header=change(header,'/* Average strategy (weighted by iteration) into `out`. */','''/* Average strategy (weighted by iteration) into `out` in the default build.
 * ASTRA_CFR_LAST_ONLY=1 omits its allocation/update and rejects this API.
 * Only audited last-iterate consumers may enable that compile-time mode. */''');(fast/'cfr.h').write_text(header)
    patch=''.join(difflib.unified_diff((OLD/'build/fast/src/cfr.c').read_text().splitlines(True),text.splitlines(True),fromfile='254/cfr.c',tofile='last-only/cfr.c'))
    (OUT/'last-only.patch').write_text(patch)
    api=(OLD/'api.h').read_text();api=change(api,' void (*evaluate)(void *,double *);',' void (*evaluate)(void *,double *);\n void (*average)(void *,double *);');(HERE/'api.h').write_text(api)
    wrapper=(OLD/'wrapper.c').read_text()
    a='static size_t state(void *p,double *out){Game *g=p;size_t n=g->n_slots;if(out){memcpy(out,g->regret,n*8);memcpy(out+n,g->last,n*8);memcpy(out+2*n,g->strategy_sum,n*8);pcfr_current(g,out+3*n);}return 4*n;}'
    b='''static size_t state(void *p,double *out){
 Game *g=p;size_t n=g->n_slots;
#if FAST && LAST_ONLY
 assert(!g->strategy_sum);
#endif
 if(out && n){
  memcpy(out,g->regret,n*8);memcpy(out+n,g->last,n*8);
#if LAST_ONLY
  memset(out+2*n,0,n*8); /* average intentionally excluded in BOTH arms */
#else
  memcpy(out+2*n,g->strategy_sum,n*8);
#endif
  pcfr_current(g,out+3*n);
 }
 return 4*n;
}'''
    wrapper=change(wrapper,a,b)
    wrapper=change(wrapper,'return (size_t)g->allocated_slots*5*sizeof(double);','return (size_t)g->allocated_slots*(LAST_ONLY?4:5)*sizeof(double);')
    wrapper=change(wrapper,'game_finalize(g);read_exact(g->regret,sizeof(double),g->n_slots,f);read_exact(g->last,sizeof(double),g->n_slots,f);read_exact(g->strategy_sum,sizeof(double),g->n_slots,f);','''game_finalize(g);read_exact(g->regret,sizeof(double),g->n_slots,f);read_exact(g->last,sizeof(double),g->n_slots,f);
#if FAST && LAST_ONLY
 double *discard=malloc((g->n_slots?g->n_slots:1)*sizeof(double));read_exact(discard,sizeof(double),g->n_slots,f);free(discard);
#else
 read_exact(g->strategy_sum,sizeof(double),g->n_slots,f);
#endif\n''')
    wrapper=change(wrapper,'const SolverAPI API_NAME=', 'static void average(void *p,double *out){pcfr_average(p,out);}\nconst SolverAPI API_NAME=')
    wrapper=change(wrapper,'load,wrap,clears,evaluate};','load,wrap,clears,evaluate,average};');(HERE/'wrapper.c').write_text(wrapper)
    check=(OLD/'check.c').read_text()
    check=change(check,' base_api.state(p->b,a);fast_api.state(p->f,b);',''' base_api.state(p->b,a);fast_api.state(p->f,b);
#if !LAST_ONLY
 /* Exercise the generic average API as well as its stored sums. */
 base_api.average(p->b,a);fast_api.average(p->f,b);
#endif''')
    # Average overwrites only the first n_slots: compare other arrays remains,
    # but also compare original state BEFORE calling it to retain regret proof.
    check=change(check,' /* Exercise the generic average API as well as its stored sums. */',''' assert(!memcmp(a,b,n*sizeof(double)));
 /* Exercise the generic average API as well as its stored sums. */''')
    check=change(check,' printf("{\\"passed\\":true,',' printf("{\\"last_only\\":%s,\\"passed\\":true,')
    check=change(check,'compared,checked_slots);','LAST_ONLY?"true":"false",compared,checked_slots);')
    (HERE/'check.c').write_text(check)
    misuse='''#include "cfr.h"
int main(void){Game g;game_init(&g);game_node(&g,NODE_TERMINAL,0,-1,0);game_finalize(&g);double out=0;pcfr_average(&g,&out);game_free(&g);return 0;}
'''
    (HERE/'misuse.c').write_text(misuse)
    functions=['game_init','game_free','game_infoset','game_node','game_children','game_finalize','game_grow','game_expand_leaf','game_start_on','pcfr_iteration','pcfr_current','pcfr_infoset_strategy','pcfr_average','game_value','best_response_value','exploitability']
    commands=[]
    def run(cmd):
        result=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=60)
        commands.append(dict(command=list(map(str,cmd)),code=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0,result.stderr
    for mode in (0,1):
        for kind,flags in [('opt',['-O2']),('san',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
            objects=[]
            for arm,source in [('base',base),('fast',fast)]:
                names=['-D'+name+'=base_'+name for name in functions] if arm=='base' else []
                names += ['-DAPI_NAME='+arm+'_api','-DFAST='+str(int(arm=='fast')),'-DLAST_ONLY='+str(mode),'-DASTRA_CFR_LAST_ONLY='+str(mode)]
                for file in (source/'cfr.c',HERE/'wrapper.c'):
                    dest=build/f'{arm}-{file.stem}-{mode}-{kind}.o';objects.append(dest)
                    run(['gcc','-std=c11',*flags,*names,'-I',source,'-I',HERE,'-c',file,'-o',dest])
            run(['gcc','-std=c11','-D_POSIX_C_SOURCE=200809L','-DLAST_ONLY='+str(mode),*flags,'-I',HERE,HERE/'check.c',*objects,'-lm','-o',build/f'check-{mode}-{kind}'])
    for mode in (0,1):
        run(['gcc','-std=c11','-O2','-DNDEBUG','-DASTRA_CFR_LAST_ONLY='+str(mode),'-I',fast,fast/'cfr.c',HERE/'misuse.c','-lm','-o',build/f'average-api-{mode}'])
    files=[*sorted(base.glob('*')),*sorted(fast.glob('*')),HERE/'build.py',HERE/'api.h',HERE/'wrapper.c',HERE/'check.c',HERE/'misuse.c']
    (OUT/'build.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),commands=commands,dependencies={str(p):sha(p) for p in files},nearest_prior='253workspace and254selective update reused;254whole-search advancement failed.315profiles current v38. New mode omits only unconsumed average buffer/scan; does not establish speed or playing strength.'),indent=2)+'\n')
    print(json.dumps(dict(built=True,commands=len(commands),timing=False)))

if __name__=='__main__':main()
