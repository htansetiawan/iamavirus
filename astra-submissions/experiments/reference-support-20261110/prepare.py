"""Freeze read-only reference-support diagnostics, not a playing treatment."""
from datetime import datetime,timezone
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
ANCESTRY=HERE.parent/'private-ancestry-20261110'
OUT=ROOT/'astra-submissions/analysis/reference-support-20261110';BUILD=HERE/'build'
PARENT=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
STORE=Path('/media/henrytan/seagate/iamavirus/astra/reference-support-20261110')
SOURCES=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def change(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def feed(case):
    replay=json.loads(Path(case['replay_path']).read_text());assert sha(case['replay_path'])==case['replay_sha256']
    side=0 if case['side']=='white' else 1;lines=['fow',f"{'w' if side==0 else 'b'} 180 2"];moves=[]
    for ply,frame in enumerate(replay['frames'][:case['ply']+1]):
        lines.append(frame[case['side']])
        if ply%2==side:
            lines.append(str(frame['clocks'][side]));moves.append(replay['frames'][ply+1]['move'])
    return '\n'.join(lines)+'\n',moves
def environment(case,moves,seconds):
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
    side=0 if case['side']=='white' else 1
    env.update(MIST_FORCE_MOVES=','.join(moves),MIST_THREADS='2',MIST_MAX_SECONDS=str(seconds),MIST_SAMPLES='32',
               MIST_SF_WORKERS='2',MIST_STOCKFISH=str(PARENT/'bin/stockfish'),MIST_HISTORY_TABLE=str(PARENT/'data/history.bin'),
               ASTRA_SF_ALLCHILDREN='1',ASTRA_REFERENCE_DECISION=str((case['ply']-2-side)//2),FOW_SEED=str(2921100+case['context']))
    return env
def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(exist_ok=False);shutil.copytree(PARENT/'src',BUILD/'src')
    spec=importlib.util.spec_from_file_location('ancestry_patch',ANCESTRY/'patch.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.apply(BUILD/'src')
    p=BUILD/'src/gtcfr.c';s=p.read_text();s='#include "observe.h"\n'+s
    s=change(s,'    out->move = ours.moves[best];','    astra_reference_capture(b, &ours, x + o, best);\n    out->move = ours.moves[best];');p.write_text(s)
    p=BUILD/'src/main.c';s=p.read_text();s='#include "observe.h"\n'+s
    s=change(s,'Belief b; belief_init_start(&b, us, cap);','Belief b; belief_init_start(&b, us, cap);\n    if (!astra_ancestry_enable(&b)) return 80;')
    assert s.count('!(forced && *forced)')==3
    s=s.replace('!(forced && *forced)','(!(forced && *forced) || astra_reference_warm(decisions))')
    s=change(s,'        SearchResult r; int ok = 0;','        astra_reference_dump(&b, decisions);\n        SearchResult r; int ok = 0;')
    s=change(s,'            char want[8] = ""; int k = 0;',
      '            if (astra_reference_warm(decisions)) {\n                SearchResult ref; astra_reference_legal(&allowed);\n                if (!gtcfr_decide(&b, &gp, &ref)) return 86;\n            }\n            char want[8] = ""; int k = 0;')
    p.write_text(s)
    command=['gcc','-O2','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(BUILD/'src'),'-I',str(HERE),'-I',str(ANCESTRY),
             *[str(BUILD/'src'/(n+'.c')) for n in SOURCES],str(HERE/'observe.c'),'-lm','-o',str(BUILD/'probe')]
    r=subprocess.run(command,capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
    # Same posterior, different valid cf/opponent reaches: non-identifiability.
    c1=[F(1,2),F(1,2)];y1=[F(9,10),F(1,10)];c2=[F(9,10),F(1,10)];y2=[F(1,2),F(1,2)];x=F(1,5)
    normalize=lambda v:[z/sum(v) for z in v]
    posterior=lambda c,y:normalize([a*x*b for a,b in zip(c,y)])
    alpha=lambda y:[z/2+F(1,4) for z in normalize(y)]
    assert posterior(c1,y1)==posterior(c2,y2)==[F(9,10),F(1,10)] and alpha(y1)!=alpha(y2)
    cases=json.loads((ROOT/'astra-submissions/analysis/private-ancestry-20261110/plan.json').read_text())['cases']
    smoke=[]
    for side in ('white','black'):
        case=dict(next(c for c in cases if c['side']==side));case['ply']=2 if side=='white' else 3
        text,moves=feed(case)
        r=subprocess.run([str(BUILD/'probe')],input=text,text=True,capture_output=True,env=environment(case,moves,0.1),timeout=20)
        assert r.returncode==0,(r.returncode,r.stderr[-4000:])
        assert re.findall(r'^move (\S+)$',r.stdout,re.M)==moves
        rows=[json.loads(x) for x in re.findall(r'^astra-reference: (.*)$',r.stderr,re.M)]
        policies=[r for r in rows if r['kind']=='policy'];assert len(policies)==1
        assert abs(sum(r['reference'] for r in policies[0]['rows'])-1)<1e-9
        assert sum(r['pure_search_play'] for r in policies[0]['rows'])==1
        assert any(r['kind']=='coverage' for r in rows)
        smoke.append(dict(side=side,rows=rows,stdout=r.stdout))
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,command=command,smoke=smoke,
          nonidentifiability=dict(posterior=[str(v) for v in posterior(c1,y1)],alpha1=[str(v) for v in alpha(y1)],alpha2=[str(v) for v in alpha(y2)])))
    deps=[HERE/n for n in ('prepare.py','observe.c','observe.h','run.py','audit.py')]+[BUILD/'probe',PARENT/'bin/stockfish',PARENT/'data/history.bin']
    deps+=list((BUILD/'src').glob('*'))+list((PARENT/'src').glob('*'))+[ANCESTRY/n for n in ('patch.py','ancestry_types.h','ancestry_impl.h')]
    deps+=[Path(c['replay_path']) for c in cases]+[ROOT.parent/'fow-starter/referee.py']
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=cases,cores=[0,1],search_seconds=0.75,per_case_seconds=120,
          total_seconds=1800,bulk_store=str(STORE),dependencies={str(p):sha(p) for p in deps},
          scope='One guarded GT-CFR search at the preceding own decision per reused development context, then FORCE the historical own move. '
                'No previous searches, true board or hidden move inputs. Native paid thinning retained, so reconstruction and observer cost can change P. '
                'Reference is raw last-iterate x, NOT the historical forced behavior or claimed deployed mixed policy. '
                'Only a necessary own-action support screen; no reference opponent policy, ranges, gadget, root-treatment decision or games.',
          criteria=dict(min_actual_reference=1e-6,min_alternative_mass=0.01,min_supported_context_fraction=0.20,min_supported_games=4),
          stop='All32 first attempts, no replacement/parameter sweep; any fault stops. Full referee/private-input/row-mass audit. '
               'Failing necessary support closes this configuration; passing only earns reference-opponent-policy and reach construction review. '
               'No automatic playing matches or release. Primary support also requires the forced earlier action equals the searched argmax. '
               'On those contexts pure executed-policy alias mass is zero; raw reference support is a separate approximation.'))
    print(json.dumps(dict(prepared=True,cases=len(cases),pins=len(set(map(str,deps))))),flush=True)
if __name__=='__main__':main()
