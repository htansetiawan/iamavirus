"""Sample actual native search queries, then reuse the frozen evaluator harness."""
from datetime import datetime,timezone
import difflib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

import chess
import run
import review
from build import HERE,ROOT,OUT as PARENT,RELEASE,sha,write
OUT=PARENT/'frontier'
OLD=ROOT/'astra-submissions/analysis/move-cost-profile-20261102'
NATIVE=HERE.parent/'sparse-cfr-20261102/build/base'
RESOURCE=HERE.parent/'queen-terminal-backport-20261102/build-r2/base'
def now():return datetime.now(timezone.utc).isoformat()

def build():
    OUT.mkdir(exist_ok=False)
    assert json.loads((PARENT/'review.json').read_text())['passed']
    target=HERE/'build/capture';shutil.copytree(NATIVE/'src',target/'src')
    p=target/'src/sfeval.c';before=p.read_text()
    needle='    w->pending = 1;\n    return 1;'
    assert before.count(needle)==1
    after=before.replace(needle,'    fprintf(stderr, "astra-sf-parent %s\\n", fen);\n'+needle)
    p.write_text(after)
    (OUT/'capture.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/src/sfeval.c','b/src/sfeval.c')))
    cmd=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',*map(str,sorted((target/'src').glob('*.c'))),'-lm','-o',str(target/'mist')]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert result.returncode==0,result.stderr
    originals={str(p):sha(p) for p in sorted((NATIVE/'src').glob('*')) if p.is_file()}
    for name in (target/'src').iterdir():
        if name.name!='sfeval.c':assert sha(name)==sha(NATIVE/'src'/name.name)
    plan=json.loads((OLD/'plan.json').read_text())
    pins={str(p):sha(p) for p in [HERE/'frontier.py',HERE/'FRONTIER.md',HERE/'run.py',HERE/'review.py',target/'mist',RELEASE,RESOURCE/'data/history.bin']}
    for c in plan['cases']:
        for p in (OLD/(c['name']+'.input.txt'),ROOT/'data/raw/games'/c['game']/'replay.json'):pins[str(p)]=sha(p)
    write(OUT/'capture-plan.json',dict(at=now(),cases=plan['cases'],pins=pins,originals=originals,command=cmd,
          build_stdout=result.stdout,build_stderr=result.stderr,binary=str(target/'mist'),cores=[0,1],seconds=2.5,
          timeout=120,total_limit=900,seed=2561102,selection='32 unique supported FENs per decision by salted hash'))
    print(json.dumps(dict(built=True,captures=len(plan['cases']))),flush=True)

def capture():
    plan=json.loads((OUT/'capture-plan.json').read_text());os.sched_setaffinity(0,set(plan['cores']))
    for p,h in plan['pins'].items():assert sha(p)==h,p
    started=time.monotonic();receipt=dict(state='running',at=now(),plan_sha256=sha(OUT/'capture-plan.json'),jobs=[])
    write(OUT/'capture-receipt.json',receipt)
    try:
        for c in plan['cases']:
            e={k:v for k,v in os.environ.items() if not k.startswith(('ASTRA_','MIST_','FOW_'))}
            e.update(MIST_STOCKFISH=str(RELEASE),MIST_HISTORY_TABLE=str(RESOURCE/'data/history.bin'),
                     MIST_MAX_SECONDS=str(plan['seconds']),MIST_FORCE_MOVES=','.join(c['forced']),FOW_SEED=str(plan['seed']),MIST_THREADS='2')
            feed=OLD/(c['name']+'.input.txt');assert sha(feed)==c['input_sha256']
            p=subprocess.Popen([plan['binary']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=e,start_new_session=True)
            err=None;start=time.monotonic()
            try:stdout,stderr=p.communicate(feed.read_text(),timeout=min(plan['timeout'],plan['total_limit']-(time.monotonic()-started)))
            except BaseException as exc:err=repr(exc);os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
            row=dict(case=c['name'],exit_code=p.returncode,error=err,seconds=time.monotonic()-start,stdout=stdout,stderr=stderr)
            write(OUT/(c['name']+'-capture.json'),row)
            receipt['jobs'].append({k:v for k,v in row.items() if k not in ('stdout','stderr')})
            assert p.returncode==0 and err is None,row
            moves=[s[5:] for s in stdout.splitlines() if s.startswith('move ')]
            assert moves[:-1]==c['forced'] and len(moves)==len(c['forced'])+1
            assert 'mist: stockfish ready' in stderr and stderr.count('astra-sf-parent ')>=32
            print(json.dumps(receipt['jobs'][-1]),flush=True)
        receipt['state']='completed'
    except BaseException as exc:receipt.update(state='failed',error=repr(exc));raise
    finally:
        receipt.update(ended_at=now(),seconds=time.monotonic()-started)
        (OUT/'capture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

def prepare():
    receipt=json.loads((OUT/'capture-receipt.json').read_text());assert receipt['state']=='completed'
    old=json.loads((OUT/'capture-plan.json').read_text());cases=[];counts=[];skipped=[];frames=0
    path=ROOT.parent/'fow-starter/referee.py';spec=importlib.util.spec_from_file_location('frontier_referee',path);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    for c in old['cases']:
        result=json.loads((OUT/(c['name']+'-capture.json')).read_text());replay=json.loads((ROOT/'data/raw/games'/c['game']/'replay.json').read_text());board=ref.FowBoard()
        own=('white','black')[c['side']];tc=replay.get('timeControl',{});expected=['fow',f"{'w' if c['side']==0 else 'b'} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"]
        for ply,f in enumerate(replay['frames'][:c['ply']+1]):
            if ply:board.push_uci(f['move'])
            actual=ref.make_frame(board,f['clocks']);assert all(actual[k]==f[k] for k in ('board','white','black'));frames+=1
            expected.append(f[own])
            if ply%2==c['side']:expected.append(str(f['clocks'][c['side']]))
        lines=(OLD/(c['name']+'.input.txt')).read_text().splitlines();assert len(lines)==len(expected)
        for a,b in zip(lines,expected):
            if a!=b:assert float(a)==float(b)
        chosen=[s[5:] for s in result['stdout'].splitlines() if s.startswith('move ')][-1]
        assert chosen in {m.uci() for m in ref.fow_moves(board)}
        all_fens=[s[len('astra-sf-parent '):] for s in result['stderr'].splitlines() if s.startswith('astra-sf-parent ')]
        unique=sorted(set(all_fens),key=lambda f:run.salt('256-frontier:'+f));picked=[]
        for fen in unique:
            b=chess.Board(fen)
            if not b.is_valid() or b.legal_moves.count()<2:
                skipped.append(dict(case=c['name'],fen=fen,status=int(b.status()),legal=b.legal_moves.count()));continue
            picked.append(dict(id=c['name']+':'+run.salt(fen)[:12],game=c['name'],source_game=c['game'],fen=fen,
                               legal=sorted(m.uci() for m in b.legal_moves)))
            if len(picked)==32:break
        assert len(picked)==32,c['name'];cases.extend(picked)
        counts.append(dict(case=c['name'],calls=len(all_fens),unique=len(unique),selected=len(picked)))
    pins={str(p):sha(p) for p in [*HERE.glob('*.py'),HERE/'FRONTIER.md',HERE/'stockfish19-allchildren.patch',OUT/'capture-plan.json',OUT/'capture-receipt.json',*run.binaries().values()]}
    for c in old['cases']:p=OUT/(c['name']+'-capture.json');pins[str(p)]=sha(p)
    shutil.copyfile(PARENT/'provenance.json',OUT/'provenance.json')
    write(OUT/'plan.json',dict(at=now(),cases=cases,counts=counts,skipped=skipped,referee_frames=frames,pins=pins,
          regimes=['cold','warm'],passes=3,arms=list(run.binaries()),seconds_limit=900,cores=[0,1],groups=8,parents_per_group=32,
          gates=dict(mae=.08,regret=.05,large_regret_rate=.01,speedup_base=1.5,speedup_shipped=1.2),
          scope='equal decision-weighted sampled native search frontier; reused cases, instrumentation alters workload; not strength'))
    print(json.dumps(dict(prepared=True,parents=len(cases),counts=counts,skipped=len(skipped),frames=frames)),flush=True)

if __name__=='__main__':
    task=sys.argv[1]
    if task=='collect':run.OUT=OUT;run.collect()
    elif task=='review':review.OUT=OUT;review.main()
    else:{'build':build,'capture':capture,'prepare':prepare}[task]()
