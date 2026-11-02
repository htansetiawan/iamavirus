"""Conditional production-binary pilot; uses the audited turn-isolated runner."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
from build import HERE,ROOT,OUT as PARENT,RELEASE,sha,write
from run import now

OUT=PARENT/'full-games';EVIDENCE=PARENT/'search'
OLD=HERE.parent/'sparse-cfr-20261102/full_games.py'
spec=importlib.util.spec_from_file_location('allchild_full_games',OLD)
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
legacy.HERE=HERE;legacy.ROOT=ROOT;legacy.OUT=OUT;legacy.EVIDENCE=EVIDENCE;legacy.__file__=__file__

def prepare():
    prior=json.loads((EVIDENCE/'plan.json').read_text());summary=json.loads((EVIDENCE/'paired-summary.json').read_text())
    review=json.loads((EVIDENCE/'independent-review.json').read_text());inputs=json.loads((EVIDENCE/'input-source-review.json').read_text())
    assert summary['gate_pass'] and review['labels_match'] and inputs['passed']
    assert review['summary_sha256']==inputs['summary_sha256']==sha(EVIDENCE/'paired-summary.json')
    assert json.loads((EVIDENCE/'terminal.json').read_text())['status']=='complete'
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'plan.json').exists() and not (OUT/'batch-start.json').exists()
    resource=HERE.parent/'queen-terminal-backport-20261102/build-r2/base'
    native=HERE.parent/'sparse-cfr-20261102/build/base/mist'
    assert sha(native)=='14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd'
    for arm in ('base','candidate'):
        directory=HERE/'build'/arm;shutil.copy2(native,directory/'mist')
        scorer=RELEASE if arm=='base' else HERE/'build/candidate/src/stockfish'
        (directory/'run.sh').write_text('#!/bin/sh\nset -eu\nexport MIST_STOCKFISH="'+str(scorer)+'"\nexport MIST_HISTORY_TABLE="'+str(resource/'data/history.bin')+'"\nexport ASTRA_SF_ALLCHILDREN='+('0' if arm=='base' else '1')+'\nexec "'+str(directory/'mist')+'"\n')
    shutil.copyfile(ROOT.parent/'fow-starter/referee.py',HERE/'build/referee.py')
    dependencies={str(ROOT/p):h for p,h in prior['dependencies'].items()}
    for p in [OLD,Path(__file__),legacy.RUNNER,HERE/'build/referee.py',EVIDENCE/'paired-summary.json',
              EVIDENCE/'independent-review.json',EVIDENCE/'input-source-review.json',EVIDENCE/'plan.json',
              ROOT/'astra-submissions/tools/local_turn_control.py',HERE/'build/base/run.sh',HERE/'build/candidate/run.sh',
              HERE/'build/base/mist',HERE/'build/candidate/mist',RELEASE,HERE/'build/candidate/src/stockfish',resource/'data/history.bin']:
        dependencies[str(p)]=sha(p)
    for p,h in dependencies.items():assert sha(p)==h,p
    jobs=[dict(id=f'sf256-p{pair}-{side}',phase='h2h',lane=pair%2,pair=pair,arm='candidate',side=side,
               engine_seed=2561200+2*pair,opponent_seed=2561201+2*pair,opponent='base')
          for pair in range(8) for side in ('white','black')]
    plan=dict(created_at=now(),dependencies=dependencies,jobs=jobs,lanes={'0':'0,1','1':'2,3'},
          time_control={'base':180,'increment':2,'max_plies':1000},game_wall_cap=2450,batch_wall_cap=14400,
          gate='16 first-attempt games, eight colour-swapped pairs vs exact v37 source/binary/history and shipped SF. At least10points and zero faults/forfeits earns a separate opponent gate, not promotion. Otherwise close this unchanged configuration.',
          resume='Skip only verified completed receipts. Never repeat a started game until its original process/handle is reconciled.',
          initial_position='standard start, both colors share pair engine seeds',
          baseline_binary_sha256=sha(native),candidate_binary_sha256=sha(native),
          baseline_scorer_sha256=sha(RELEASE),candidate_scorer_sha256=sha(HERE/'build/candidate/src/stockfish'),
          gpu=False,truth_to_actor=False,source_mode='Original v37 native binary in both arms; only external scorer/flag changes. No diagnostic exports.',
          limitations='Small local full-clock pilot against one reference; not arena Elo or instructors/duck strength. Experimental AVX2 scorer, not an arena-portable release.')
    write(OUT/'plan.json',plan);legacy.module().load()
    print(json.dumps(dict(planned_games=16,pairs=8,plan_sha256=sha(OUT/'plan.json'))),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','start','worker','lane','summarize'));p.add_argument('--job');p.add_argument('--lane',type=int,choices=(0,1));args=p.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='worker':legacy.module().worker(args.job)
    elif args.command=='lane':legacy.lane(args.lane)
    else:getattr(legacy,args.command)()
