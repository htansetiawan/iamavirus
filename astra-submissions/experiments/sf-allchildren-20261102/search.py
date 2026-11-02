"""Reuse audited paired-search collection/referee tools with new frozen arms."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from build import HERE,ROOT,OUT as PARENT,RELEASE,sha,write
from run import now

OUT=PARENT/'search';DEST=HERE/'build/diagnostic'
OLD=HERE.parent/'sparse-cfr-20261102'
RESOURCE=HERE.parent/'queen-terminal-backport-20261102/build-r2/base'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools'),str(OLD)]
from fresh_taxonomy_gate import protocol

def module(name):
    spec=importlib.util.spec_from_file_location('sf_'+name,OLD/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.HERE=HERE;m.OUT=OUT;return m

def build():
    assert json.loads((PARENT/'review.json').read_text())['passed']
    assert json.loads((PARENT/'frontier/review.json').read_text())['passed']
    OUT.mkdir(exist_ok=False);src=DEST/'src';src.mkdir(parents=True,exist_ok=False)
    archive=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
    assert sha(archive)=='41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.startswith('src/') and not name.endswith('/'):(DEST/name).write_bytes(z.read(name))
    teacher=ROOT/'astra-submissions/analysis/deeprl-table-audit-20261025'
    for name in ('teacher_targets.c','teacher_targets.h','teacher_dump.c','teacher_dump.h'):shutil.copyfile(teacher/name,src/name)
    p=src/'gtcfr.c';s=p.read_text();s=s.replace('#include "cfr.h"','#include "cfr.h"\n#include "teacher_dump.h"')
    anchor='    free(x); free(idx); free(share); free(chance_kids); free(chance_p);';assert s.count(anchor)==1
    s=s.replace(anchor,'    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'+anchor);p.write_text(s)
    p=src/'main.c';s=p.read_text();s=s.replace('#include "gtcfr.h"','#include "gtcfr.h"\nint astra_solver_pair(const Belief *, const GtcfrParams *, SearchResult *);')
    assert s.count('gtcfr_decide(&b, &gp, &r)')==1;p.write_text(s.replace('gtcfr_decide(&b, &gp, &r)','astra_solver_pair(&b, &gp, &r)'))
    cmd=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=200809L','-I',str(src),*map(str,sorted(src.glob('*.c'))),str(HERE/'search_pair.c'),'-lm','-o',str(DEST/'mist')]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert r.returncode==0,r.stderr
    (DEST/'bin').symlink_to(RESOURCE/'bin',target_is_directory=True);(DEST/'data').symlink_to(RESOURCE/'data',target_is_directory=True)
    (DEST/'run.sh').write_text('#!/bin/sh\nset -eu\nexport MIST_STOCKFISH="'+str(RELEASE)+'"\nexport MIST_HISTORY_TABLE="'+str(RESOURCE/'data/history.bin')+'"\nexport ASTRA_SF_CANDIDATE="'+str(HERE/'build/candidate/src/stockfish')+'"\nexec "'+str(DEST/'mist')+'"\n')
    pins={str(p):sha(p) for p in [*src.iterdir(),DEST/'mist',DEST/'run.sh',HERE/'search_pair.c',archive,RELEASE,HERE/'build/candidate/src/stockfish',RESOURCE/'data/history.bin'] if p.is_file()}
    write(OUT/'build.json',dict(command=cmd,stdout=r.stdout,stderr=r.stderr,pins=pins))
    print(json.dumps(dict(built=True,binary_sha256=sha(DEST/'mist'))),flush=True)

def preflight():
    os.sched_setaffinity(0,{0,1});cases=json.loads((ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json').read_text())['cases']
    replay=json.loads(Path(cases[0]['replay_path']).read_text());records=[]
    for mode in ('fallback','control','candidate'):
        for side in (0,1):
            target=OUT/f'preflight-{mode}-{side}.targets.jsonl';assert not target.exists()
            feed,forced=protocol(replay,side,side);assert not forced
            e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_'))}
            e.update(ASTRA_SOLVER_PAIR=str(side),ASTRA_PAIR_SECONDS='0.1' if mode=='candidate' else '0',
                     MIST_TEACHER_OUT=str(target),FOW_SEED='2561102')
            if mode!='fallback':e.update(MIST_STOCKFISH=str(RELEASE),MIST_HISTORY_TABLE=str(RESOURCE/'data/history.bin'),ASTRA_SF_CANDIDATE=str(HERE/'build/candidate/src/stockfish'))
            if mode=='control':e['ASTRA_PAIR_CONTROL']='1'
            r=subprocess.run([str(DEST/'mist')],input=feed,capture_output=True,text=True,env=e,timeout=30)
            write(OUT/f'preflight-{mode}-{side}.json',dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
            assert r.returncode==0,r.stderr
            rows=[json.loads(s) for s in target.read_text().splitlines()];assert len(rows)==2
            for k in ('samples','avoid_moves','search_budget_seconds','belief_count'):assert rows[0][k]==rows[1][k],k
            assert [a['uci'] for a in rows[0]['actions']]==[a['uci'] for a in rows[1]['actions']]
            if mode!='candidate':assert rows[0]==rows[1],(mode,side)
            else:
                assert all(r['search_budget_seconds']==.1 for r in rows)
            records.append(dict(mode=mode,side=side,passed=True,targets_sha256=sha(target)))
    write(OUT/'preflight.json',dict(passed=True,records=records));print(json.dumps(dict(passed=True,cases=len(records))),flush=True)

def prepare():
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    cases_path=ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101/cases.json';cases=json.loads(cases_path.read_text())['cases'];assert len(cases)==51
    oracle_path=HERE.parent/'persistent-response-20261101/review.py';spec=importlib.util.spec_from_file_location('sf_oracle',oracle_path);oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    pins=json.loads((OUT/'build.json').read_text())['pins']
    for p in [*HERE.glob('*.py'),HERE/'SEARCH.md',HERE/'search_pair.c',*OLD.glob('search*.py'),PARENT/'review.json',PARENT/'frontier/review.json',OUT/'preflight.json',cases_path,ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',oracle_path,oracle.REFPATH,ROOT/'learning/rules.py',ROOT/'learning/ingest.py']:pins[str(p)]=sha(p)
    write(OUT/'plan.json',dict(at=now(),seed=2561102,cores=[0,1],per_search_seconds=2.5,prefix_max_seconds=10,
          case_wall_cap=120,wall_cap=2700,arms=['off','on'],cases=cases,dependencies=pins,
          order='alternate first arm; fresh scorer processes per arm, same belief/mask/worlds',truth_to_actor=False,gpu=False,
          gate=dict(min_exercised_pairs=20,min_median_node_ratio=1.15,max_additional_fatal=1,max_additional_material_ge2=2,technical_failures=0,illegal_choices=0),
          scope='reused development; changed evaluator, separate fresh worker histories; startup excluded from search budget',
          full_game_followup=dict(conditional_on_replay_and_review_pass=True,pairs=8,opponent='exact v37',time_control='180+2',seed_base=2561200,minimum_points_for_opponent_gate=10,wall_cap=14400)))
    print(json.dumps(dict(prepared=True,cases=len(cases),plan_sha256=sha(OUT/'plan.json'))),flush=True)

if __name__=='__main__':
    task=sys.argv[1]
    if task in ('run','review'):module('search_'+task).main()
    else:{'build':build,'preflight':preflight,'prepare':prepare}[task]()
