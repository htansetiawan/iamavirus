"""Outcome-blind historical controls, excluding the diagnosed v38 cohort."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/guard-controls-20261109';BUILD=HERE/'build'
PROTO=ROOT/'astra-submissions/experiments/guard-disagreement-20261109/build'
GROUPS=['duck','Greek Gift','Knight Vision','Strongly Invisible','Decent Chess Bot','Instructors','HYPOTHERMIA','Mist Opportunities']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')


def main():
    OUT.mkdir(exist_ok=False);BUILD.mkdir(parents=True,exist_ok=False)
    shutil.copytree(PROTO/'src',BUILD/'src')
    for name in ['bin','data']:(BUILD/name).symlink_to(PROTO/name,target_is_directory=True)
    teacher=ROOT/'astra-submissions/analysis/deeprl-table-audit-20261025'
    for name in ['teacher_targets.c','teacher_targets.h','teacher_dump.c','teacher_dump.h']:shutil.copyfile(teacher/name,BUILD/'src'/name)
    p=BUILD/'src/gtcfr.c';s=p.read_text().replace('#include "cfr.h"','#include "cfr.h"\n#include "teacher_dump.h"');anchor='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);';assert s.count(anchor)==1;s=s.replace(anchor,'    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor);p.write_text(s)
    p=BUILD/'src/main.c';s=p.read_text().replace('#include "gtcfr.h"','#include "gtcfr.h"\nint astra_guard_pair(const Belief *,const GtcfrParams *,SearchResult *,const Move *,int);')
    anchor='        const double lam = (qguard >= 0 && have_qrisk) ? qweight : 0.0;';assert s.count(anchor)==1
    s=s.replace(anchor,'        Move alternatives[512]; int alternative_count=gp.avoid_count;\n        if(alternative_count)memcpy(alternatives,gp.avoid,alternative_count*sizeof(Move));\n'+anchor)
    anchor='            int out[256], dropped = 0;';assert s.count(anchor)==1
    s=s.replace(anchor,'            for(int a=0;a<allowed.count;++a)\n                if(astra_guard_excluded(risk[a],riskt[a],least,leastt,guard,0,1))alternatives[alternative_count++]=allowed.moves[a];\n'+anchor)
    anchor='gtcfr_decide(&b, &gp, &r)';assert s.count(anchor)==1;s=s.replace(anchor,'astra_guard_pair(&b,&gp,&r,alternatives,alternative_count)');p.write_text(s)
    sources=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval','main','teacher_targets','teacher_dump']
    cmd=['gcc','-O2','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(BUILD/'src'),*[str(BUILD/'src'/f'{n}.c') for n in sources],str(HERE/'pair.c'),'-lm','-o',str(BUILD/'mist')]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stderr
    snapshot=ROOT/'astra-submissions/analysis/v38-arena-20261109/20261109T204526Z'
    listings=[g for p in sorted(snapshot.glob('baseline-v37-*.json')) for g in json.loads(p.read_text())['games']]
    excluded={r['game'] for r in json.loads((ROOT/'astra-submissions/analysis/priority-diagnosis-20261109/plan.json').read_text())['cases']}
    by={name:[] for name in GROUPS}
    for g in listings:
        side='white' if g['whitePlayerId']=='a2c35173659545c99752376a70418438' else 'black';other='black' if side=='white' else 'white'
        if g[other] in by and '2026-11-03'<=g['createdAt']<'2026-11-08' and g['id'] not in excluded:
            by[g[other]].append((g,side))
    games=[];cases=[]
    for group,candidates in by.items():
        selected=sorted(candidates,key=lambda t:hashlib.sha256(('270-control-'+t[0]['id']).encode()).hexdigest())[:4]
        assert len(selected)==4,(group,len(selected))
        for g,side in selected:
            path=ROOT/'data/raw/games'/g['id']/'replay.json';rp=json.loads(path.read_text());ci=0 if side=='white' else 1
            assert rp['id']==g['id'] and rp[side+'Version']==37
            own=list(range(ci,len(rp['frames'])-1,2));assert own
            early=min(own,key=lambda ply:abs(ply-(4+ci)))
            later=[ply for ply in own if ply>=20]
            kings=[ply for ply in later if rp['frames'][ply][side][(ord(rp['frames'][ply+1]['move'][0])-97)+8*(int(rp['frames'][ply+1]['move'][1])-1)]==('K' if ci==0 else 'k')]
            late=min(kings or later or own,key=lambda ply:hashlib.sha256(f"270-ply-{g['id']}-{ply}".encode()).hexdigest())
            games.append(dict(id=g['id'],side=side,opponent=group,createdAt=g['createdAt'],replay_path=str(path),replay_sha256=sha(path)))
            for kind,ply in [('opening',early),('king_later' if kings else 'later_fallback',late)]:
                if any(c['game']==g['id'] and c['ply']==ply for c in cases):continue
                cases.append(dict(game=g['id'],side=side,ply=ply,opponent=group,kind=kind,
                                  replay_path=str(path),replay_sha256=sha(path),id=f"{g['id']}-{ply}"))
    cases.sort(key=lambda c:hashlib.sha256(('270-order-'+c['id']).encode()).hexdigest())
    deps=[HERE/'prepare.py',HERE/'run.py',HERE/'review.py',HERE/'pair.c',*[p for p in (BUILD/'src').iterdir() if p.is_file()],
          BUILD/'mist',BUILD/'bin/stockfish',BUILD/'data/history.bin',
          ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',ROOT/'learning/rules.py',ROOT/'learning/_native.py',
          Path('/home/henrytan/git/fow-starter/referee.py')]
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),games=games,cases=cases,
       seed=2701109,cores=[0,1],per_search_seconds=2.5,prefix_max_seconds=10,case_seconds=150,wall_seconds=2400,
       dependencies={str(p):sha(p) for p in deps},
       selection='Four games per named opponent by game-ID hash, Nov3–7 v37. No results used. Opening3rd decision plus own king move selected by ply hash; later fallback if none.',
       scope='Outcome-blind unused historical replay controls; same belief/seed, alternate arm order, fresh same-v38 scorer workers. Not a strength estimate.',
       gate=dict(min_mask_changes=4,min_added_actions_chosen=1,max_additional_fatal=1,max_additional_material_ge3=2,technical_failures=0),
       followup=dict(conditional_on_gate_pass=True,opponent='exact arena v38',pairs=8,seconds=180,increment=2,
                     seed_base=2701200,minimum_points_for_further_opponent_test=10,own_technical_failures=0)))
    write(OUT/'build.json',dict(command=cmd,stdout=r.stdout,stderr=r.stderr,sha256=sha(BUILD/'mist')))
    print(json.dumps(dict(games=len(games),cases=len(cases),plan_sha256=sha(OUT/'plan.json'))))


if __name__=='__main__':main()
