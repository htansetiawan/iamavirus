from pathlib import Path
import hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/search-cost-20261102'
PRIOR=HERE.parent/'sparse-cfr-20261102'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def wrap(s,name,kind,args,root=False):
    # Find the definition, preserving all original function-body bytes.
    import re
    pattern=r'(?m)^(?:static )?(?:int|void) '+name+r'\([^;]*?\) \{'
    matches=list(re.finditer(pattern,s));assert len(matches)==1,(name,len(matches))
    m=matches[0];start=m.start();brace=m.end()-1;depth=1;i=brace+1
    # These audited functions have no unmatched braces inside string literals.
    while depth:
        if s[i]=='{':depth+=1
        if s[i]=='}':depth-=1
        i+=1
    signature=s[start:brace].rstrip(); renamed=signature.replace(name+'(',name+'_profile_impl(',1)
    is_void=signature.startswith('void ')
    setup='prof_begin(); ' if root else ''
    call=('' if is_void else 'int result = ')+name+'_profile_impl('+args+');'
    tail=''
    if root:
        tail=' prof_report(out->nodes, out->iterations, params->seconds, getenv("MIST_ASYNC") ? atoi(getenv("MIST_ASYNC")) : 0);'
    wrapper=signature+' { '+setup+'int token = prof_enter('+kind+'); '+call+' prof_leave(token);'+tail+('' if is_void else ' return result;')+' }'
    return s[:start]+renamed+' '+s[brace:i]+'\n\n'+wrapper+s[i:]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'build.json').exists()
    old=json.loads((ROOT/'astra-submissions/analysis/sparse-cfr-20261102/plan.json').read_text())
    for p,h in old['build'].items():assert sha(ROOT/p)==h,p
    records=[];pins={}
    def run(cmd,cwd=None):
        r=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,text=True,timeout=120)
        records.append(dict(command=list(map(str,cmd)),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        assert r.returncode==0,r.stderr
        return r
    for arm in ('base','fast'):
        dest=HERE/'build'/arm;shutil.copytree(PRIOR/'build'/arm/'src',dest/'src',dirs_exist_ok=True)
        shutil.copyfile(PRIOR/'build'/arm/'build.sh',dest/'build.sh')
        for n in ('profile.c','profile.h'):shutil.copyfile(HERE/n,dest/'src'/n)
        for filename,functions in {
            'cfr.c':[('pcfr_iteration','PROF_SOLVE','g, t'),('pcfr_current','PROF_STRATEGY','g, out'),('game_grow','PROF_GROW','g')],
            'gtcfr.c':[('build_children_scored','PROF_EXPAND','t, p, hist, kids, only, sf, sf_cp, sf_found'),('pick_once','PROF_SELECT','t, explorer, x, x_slots'),('gtcfr_decide','PROF_OTHER','b, params, out')],
            'sfeval.c':[('sf_children','PROF_SF','p, l, cp, found'),('sf_submit','PROF_SF','worker, p'),('sf_collect','PROF_SF','worker, l, cp, found'),('sf_poll','PROF_SF','timeout_ms')]
        }.items():
            p=dest/'src'/filename;s=p.read_text()
            for name,kind,args in functions:s=wrap(s,name,kind,args,root=name=='gtcfr_decide')
            s=s.replace('#include <math.h>','#include "profile.h"\n#include <math.h>') if filename!='sfeval.c' else s.replace('#include "sfeval.h"','#include "sfeval.h"\n#include "profile.h"')
            assert '#include "profile.h"' in s;p.write_text(s)
        p=dest/'build.sh';p.write_text(p.read_text().replace('src/main.c"','src/main.c src/profile.c"'))
        run(['bash','build.sh'],dest)
        pins.update({str(p.relative_to(ROOT)):sha(p) for p in [*sorted((dest/'src').glob('*')),dest/'build.sh',dest/'mist']})
    run(['gcc','-std=c11','-O2','-DPROFILE_TEST_CLOCK',HERE/'profile.c',HERE/'test_profile.c','-o',HERE/'build/test-profile'])
    r=run([HERE/'build/test-profile']);v=json.loads(r.stderr.split('astra-search-cost ')[1])
    assert v['wall']==9 and v['cpu']==4.5
    assert {k:x['wall'] for k,x in v['buckets'].items() if x['calls']}=={'other':3,'solver':2,'strategy':1,'stockfish':3},v
    assert sum(x['wall'] for x in v['buckets'].values())==v['wall']
    (OUT/'build.json').write_text(json.dumps(dict(pins=pins,records=records,nested_timer_test=v),indent=2)+'\n')
    print(json.dumps(dict(built=True,pins=len(pins),nested_timer_pass=True)))
if __name__=='__main__':main()
