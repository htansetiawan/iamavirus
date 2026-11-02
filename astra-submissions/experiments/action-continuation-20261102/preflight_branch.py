"""Exercise intervention clocks, immediate terminals and native root diagnostics."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from branch import HERE, ROOT, PRIOR, base, run, inspect
from build_proposer import OUT, HELPER
from preflight import synthetic


def clean_env():
    e = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_','OMP_','OPENBLAS_','MKL_'))}
    e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    return e


def main():
    fixtures = [
        ('ep', ['e2e4','a7a6','e4e5','d7d5','e5d6','c7d6'], 4, 1.25, None),
        ('castle', ['e2e4','e7e5','g1f3','b8c6','f1c4','g8f6','e1g1','a7a6'], 6, 3.25, None),
        ('repetition', ['g1f3','g8f6','f3g1','f6g8']*2, 7, 2.5, '1/2-1/2'),
        ('terminal-loss', ['f2f3','e7e5','g2g4','d8h4','a2a3'], 4, 2.5, '0-1'),
        ('pair-e4', ['e2e4','a7a6'], 0, 2.5, None),
        ('pair-d4', ['d2d4','a7a6'], 0, 2.5, None),
    ]
    reports=[]
    for name, moves, branch, charge, expected in fixtures:
        p=base.prefix(synthetic(moves),branch);directory=OUT/('preflight-'+name);directory.mkdir(exist_ok=False)
        cmds=[]
        for side in (0,1):
            actor=base.actor_prefix(p,side)
            cmds.append([sys.executable,str(PRIOR/'fixture_bot.py'),json.dumps(dict(
                moves=moves[side::2],views=actor['views'],clocks=actor['clocks']+[actor['branch_clock']]))])
        game=run(p,cmds,moves[branch],charge,directory,len(moves)-branch)
        r=inspect(game,p,moves[branch],charge)
        assert r['result']==expected and game['censored']==(expected is None)
        (directory/'replay.json').write_text(json.dumps(game,indent=2)+'\n')
        reports.append(dict(fixture=name,**r,replay_sha256=base.sha(directory/'replay.json')))
    assert reports[-1]['root_post_clocks']==reports[-2]['root_post_clocks']==[179.5,180.0]
    invalids=0
    for action,charge in [('a1h8',1),('e2e4',180),('e2e4',float('nan')),('e2e4',-1)]:
        try:run(base.prefix(synthetic(['e2e4']),0),[],action,charge,OUT/'never-created',1)
        except AssertionError:invalids+=1
    assert invalids==4 and not (OUT/'never-created').exists()

    # Native helper vs independent public game_value on a small tree with
    # shared infosets, chance and the engine's doubled (-2) terminal utility.
    source='#include <assert.h>\n#include <math.h>\n#include "cfr.h"\n'+HELPER+r'''
int main(void) {
 Game g; game_init(&g); int I=game_infoset(&g,0,2), J=game_infoset(&g,1,2);
 int root=game_node(&g,NODE_CHANCE,0,-1,0), worlds[2]; double weights[2]={.25,.75};
 for(int w=0;w<2;++w) {
  worlds[w]=game_node(&g,NODE_PLAYER,0,I,0); int actions[2];
  for(int a=0;a<2;++a) {
   actions[a]=game_node(&g,NODE_PLAYER,1,J,0); int ends[2];
   for(int o=0;o<2;++o) ends[o]=game_node(&g,NODE_TERMINAL,0,-1,(double)(w+a-o-1));
   game_children(&g,actions[a],ends,0,2);
  }
  game_children(&g,worlds[w],actions,0,2);
 }
 game_children(&g,root,worlds,weights,2); game_finalize(&g);
 double x[4]={.3,.7,.4,.6}; double q[2]={0};
 for(int a=0;a<2;++a) for(int w=0;w<2;++w)
  q[a]+=weights[w]*astra_subtree_value(&g,g.child[g.nodes[worlds[w]].first+a],x);
 assert(fabs(.3*q[0]+.7*q[1]-game_value(&g,x))<1e-12);
 for(int a=0;a<2;++a) { x[0]=a==0; x[1]=a==1; assert(fabs(q[a]-game_value(&g,x))<1e-12); }
 game_free(&g); return 0;
}
'''
    src=HERE/'build/test-values.c';src.write_text(source)
    proc=subprocess.run(['gcc','-std=c11','-O2','-I'+str(HERE/'build/src'),str(src),
                         str(HERE/'build/src/cfr.c'),'-lm','-o',str(HERE/'build/test-values')],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    assert subprocess.run([str(HERE/'build/test-values')]).returncode==0
    env=clean_env();env.update(ASTRA_PROPOSAL='1',MIST_MAX_SECONDS='.1',FOW_SEED='243')
    view=synthetic(['e2e4'])['frames'][0]['white']
    proc=subprocess.run([str(HERE/'build/proposer')],input='fow\nw 180 2\n'+view+'\n180\n',
                        env=env,text=True,capture_output=True,timeout=30)
    (OUT/'native-smoke.stderr').write_text(proc.stderr);(OUT/'native-smoke.stdout').write_text(proc.stdout)
    assert proc.returncode==0
    rows=[(m,float(p),float(q)) for m,p,q in re.findall(r'astra-proposal: (\w+) (\S+) (\S+)',proc.stderr)]
    value=float(re.search(r'astra-proposal-value: (\S+)',proc.stderr)[1])
    assert len(rows)>1 and abs(sum(p for _,p,_ in rows)-1)<1e-10
    assert abs(sum(p*q for _,p,q in rows)-value)<1e-10
    legal=re.search(r'astra-view-legal:(.*)',proc.stderr)[1].split()
    assert all(m in legal for m,_,_ in rows)
    result=dict(passed=True,fixtures=reports,invalid_interventions_rejected=invalids,
                shared_clock_pair=True,root_value_fixture=True,native_root_rows=len(rows),
                native_weighted_value_error=abs(sum(p*q for _,p,q in rows)-value),
                proposer_sha256=base.sha(HERE/'build/proposer'),continuation_sha256=base.sha(PRIOR/'build/mist'))
    with (OUT/'preflight.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('passed','invalid_interventions_rejected','shared_clock_pair','root_value_fixture','native_root_rows','native_weighted_value_error')}))


if __name__=='__main__':main()
