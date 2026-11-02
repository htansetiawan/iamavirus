#!/usr/bin/env python3
"""Minimal known queen-event correction, separate from frozen trial 219."""
from datetime import datetime,timezone
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/queen-terminal-backport-20261102'
PERSIST=HERE.parent/'persistent-response-20261101'
QUEEN=ROOT/'astra-submissions/analysis/queen-screen-20261101'
FRESH=ROOT/'astra-submissions/analysis/fresh-taxonomy-20261101'
ARCHIVE=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
MODEL=ROOT/'astra-submissions/analysis/visible-response-20261101/models/response.bin'
ARMS=('base','base_fixed','persistent','persistent_fixed')
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from fresh_taxonomy_gate import protocol,exchange_probe
from learning import ingest
from learning.compare_archives import kill_tree


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def clean_env():return {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
def fix(directory):
    p=directory/'src/main.c';before=p.read_text()
    needle='                Position q = p; Undo v; make_move(&q, l.moves[j], &v);\n                if (is_attacked(&q, sq, us))'
    assert before.count(needle)==1
    after=before.replace(needle,needle.replace('\n                if', '\n                if (mover_left_king_capturable(&q)) continue; /* Fable dd89907: suicidal capture is not a queen loss. */\n                if'))
    p.write_text(after);(OUT/(directory.name+'.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/src/main.c','b/src/main.c')))


def prepare():
    OUT.mkdir(parents=True,exist_ok=False);build=HERE/'build';build.mkdir(exist_ok=False)
    for arm in ('base','base_fixed'):
        d=build/arm;d.mkdir()
        with zipfile.ZipFile(ARCHIVE) as z:
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(d)
        if arm.endswith('fixed'):fix(d)
        r=subprocess.run(['bash','build.sh'],cwd=d,capture_output=True,text=True,timeout=60)
        (OUT/(arm+'-build.log')).write_text(r.stdout+r.stderr);r.check_returncode()
    # Copy candidate sources only. Shared running source/binaries are untouched.
    d=build/'persistent_fixed';d.mkdir();shutil.copytree(PERSIST/'src',d/'src');fix(d)
    sources=sorted((d/'src').glob('*.c'))
    r=subprocess.run(['gcc','-O3','-DNDEBUG','-std=c11','-pthread','-o',str(d/'mist'),*[str(p) for p in sources],'-lm'],capture_output=True,text=True,timeout=60)
    (OUT/'persistent_fixed-build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    binaries={'base':build/'base/mist','base_fixed':build/'base_fixed/mist','persistent':PERSIST/'build/mist','persistent_fixed':d/'mist'}
    assert sha(binaries['base'])==sha(PERSIST/'build/base/mist')
    assert sha(binaries['persistent'])=='00dc640d9773296b7af7f35b9faceb7f1b2ea6e49199742091415825e5744056'
    fixtures=[]
    for arm in ('base','base_fixed'):
        d=build/arm;exe=build/('fixtures-'+arm)
        sources=[p for p in sorted((d/'src').glob('*.c')) if p.name!='main.c']
        cmd=['gcc','-O2','-std=c11','-pthread',f'-DASTRA_MAIN_SOURCE="{d}/src/main.c"',str(HERE/'fixtures.c'),*[str(p) for p in sources],'-lm','-o',str(exe)]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);(OUT/(arm+'-fixtures-build.log')).write_text(r.stdout+r.stderr);r.check_returncode()
        r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);r.check_returncode()
        rows=[json.loads(s) for s in r.stdout.splitlines()];assert len(rows)==8
        failures=[x for x in rows if x['risk']!=x['expected'] or x['sharp']!=x['expected']]
        assert len(failures)==(4 if arm=='base' else 0),(arm,rows)
        fixtures.append(dict(arm=arm,rows=rows,known_mismatches=len(failures),binary_sha256=sha(exe)))
    # Rules oracle checks all fixture root moves and safe opponent captures.
    spec=importlib.util.spec_from_file_location('terminal_fixture_ref',ROOT.parent/'fow-starter/referee.py')
    ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
    for row in fixtures[1]['rows']:
        b=ref.FowBoard(None);b.set_piece_map({i:ref.chess.Piece.from_symbol(c) for i,c in enumerate(row['board']) if c!='-'});b.turn=row['side']==0
        own=b.turn;king=b.king(not own);assert king is not None and not b.is_attacked_by(own,king)
        b.push_uci(row['move']);safe_queen_captures=0
        for m in ref.fow_moves(b):
            p=b.piece_at(m.to_square)
            if not p or p.color!=own or p.piece_type!=ref.chess.QUEEN:continue
            q=b.copy();q.push(m);king=q.king(not q.turn)
            safe_queen_captures+=int(king is not None and not q.is_attacked_by(q.turn,king))
        assert bool(safe_queen_captures)==bool(row['expected']),row
    save(OUT/'native-fixtures.json',dict(runs=fixtures,independent_referee_fixtures=8,referee_sha256=sha(Path(spec.origin))))
    cases=[];queen=json.loads((QUEEN/'plan.json').read_text())
    for c in queen['cases']:
        feed=QUEEN/(c['name']+'.input.txt');assert sha(feed)==c['input_sha256'];(OUT/feed.name).write_bytes(feed.read_bytes());cases.append(dict(c,phase='queen'))
    fresh=json.loads((FRESH/'cases.json').read_text())
    for c in fresh['cases']:
        payload=Path(c['replay_path']).read_bytes();assert hashlib.sha256(payload).hexdigest()==c['replay_sha256'];rp=json.loads(payload)
        side=('white','black').index(c['side']);feed,forced=protocol(rp,c['ply'],side);name=f"{c['game']}-{c['ply']}";p=OUT/(name+'.input.txt');p.write_text(feed)
        cases.append(dict(name=name,game=c['game'],ply=c['ply'],side=side,opponent=c['opponent'],forced=forced,input_sha256=sha(p),replay_sha256=c['replay_sha256'],phase='broad'))
    assert len(cases)==59 and len({c['name'] for c in cases})==59
    deps={str(p):sha(p) for p in [Path(__file__),HERE/'fixtures.c',ARCHIVE,MODEL,QUEEN/'plan.json',FRESH/'cases.json',OUT/'native-fixtures.json',build/'base/bin/stockfish',build/'base/data/history.bin',ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py',ROOT/'learning/ingest.py',ROOT/'learning/compare_archives.py',*binaries.values()]}
    for c in cases:p=OUT/(c['name']+'.input.txt');deps[str(p)]=sha(p)
    plan=dict(created_at=datetime.now(timezone.utc).isoformat(),dependencies=deps,binaries={k:str(v) for k,v in binaries.items()},cases=cases,
              arms=ARMS,cores='2,3',seconds=2.5,seed=2211102,timeout_seconds=120,model=str(MODEL),confidence=.25,
              lineage='Only the queen_risks suicidal-enemy-capture predicate from Fable dd89907. No piece guard, material helper, model, history, threshold or solver changes.',
              phases={'queen':32,'broad':204},truth_to_engine=False,
              gate='Finish all 32 queen calls. Each fixed arm must repair 23paw9tn:20 bounded queen loss with no extra immediate king loss, large queen loss or >=2-point material loss versus its own parent over eight cases. Otherwise stop before broad. If both pass, run all 204 broad calls; each fixed arm must have no more immediate king or >=4 queen losses, and <=one extra >=2 material event versus its parent. All calls must be technically valid. Passing earns further review, never automatic promotion or full games. No retries or tuning.',
              limitations='Selected reused development panels; wall-clock belief/search noise. Correctness fixtures do not establish playing strength. Frozen 219 continues unchanged.')
    save(OUT/'plan.json',plan);print(json.dumps({'fixtures':8,'original_known_failures':4,'fixed_failures':0,'cases':59,'queen_calls':32,'conditional_broad_calls':204,'plan_sha256':sha(OUT/'plan.json')}))


def run(phase):
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    if phase=='broad':assert json.loads((OUT/'queen-summary.json').read_text())['decision']=='advance_to_broad'
    execution=dict(started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),status='running',completed=0,phase=phase)
    state=OUT/(phase+'-execution.json')
    with state.open('x') as f:json.dump(execution,f)
    try:
        with (OUT/(phase+'-receipts.jsonl')).open('x') as sink:
            for n,c in enumerate(x for x in plan['cases'] if x['phase']==phase):
                for arm in ARMS[n%4:]+ARMS[:n%4]:
                    learned=arm.startswith('persistent');env=clean_env();env.update(MIST_FORCE_MOVES=','.join(c['forced']),MIST_MAX_SECONDS='2.5',FOW_SEED=str(plan['seed']),MIST_STOCKFISH=str(HERE/'build/base/bin/stockfish'),MIST_HISTORY_TABLE=str(HERE/'build/base/data/history.bin'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
                    if learned:env.update(ASTRA_VISIBLE_CONFIDENCE='.25',ASTRA_VISIBLE_MODEL=plan['model'],ASTRA_VISIBLE_PROJECT='1',ASTRA_PERSISTENT='1')
                    start=time.monotonic();p=subprocess.Popen(['taskset','-c',plan['cores'],plan['binaries'][arm]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True);error=None
                    try:stdout,stderr=p.communicate((OUT/(c['name']+'.input.txt')).read_text(),timeout=plan['timeout_seconds'])
                    except subprocess.TimeoutExpired:kill_tree(p.pid);stdout,stderr=p.communicate();error='timeout'
                    prefix=OUT/(c['name']+'-'+arm)
                    for ext,text in (('.stdout',stdout),('.stderr',stderr)):
                        with Path(str(prefix)+ext).open('x') as f:f.write(text)
                    lines=stdout.splitlines();moves=[s[5:] for s in lines if s.startswith('move ')]
                    valid=bool(lines) and lines[0]=='ready' and len(lines)==len(moves)+1 and len(moves)==len(c['forced'])+1 and moves[:-1]==c['forced']
                    if learned:valid=valid and 'astra_persistent: prior 0.25 ' in stderr and 'load_failed 0' in stderr and 'model_load_failed' not in stderr
                    row=dict(name=c['name'],arm=arm,phase=phase,returncode=p.returncode,error=error,protocol_valid=bool(valid),move=moves[-1] if moves else None,elapsed=time.monotonic()-start,stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
                    sink.write(json.dumps(row)+'\n');sink.flush();execution['completed']+=1;save(state,execution);print(json.dumps(row),flush=True)
                    assert valid and not error and p.returncode==0,row
        execution['status']='complete'
    except BaseException:execution['status']='failed';raise
    finally:execution['ended']=datetime.now(timezone.utc).isoformat();save(state,execution)


def summarize(phase):
    plan=json.loads((OUT/'plan.json').read_text());assert json.loads((OUT/(phase+'-execution.json')).read_text())['status']=='complete'
    rows=[json.loads(s) for s in (OUT/(phase+'-receipts.jsonl')).read_text().splitlines()];cases=[c for c in plan['cases'] if c['phase']==phase]
    assert len(rows)==4*len(cases) and len({(r['name'],r['arm']) for r in rows})==len(rows)
    cache={};labels=[]
    for c in cases:
        if c['game'] not in cache:
            path=ROOT/'data/raw/games'/c['game']/'replay.json';assert sha(path)==c['replay_sha256'];states,errors=ingest.validate_replay(json.loads(path.read_text()));assert not errors;cache[c['game']]=states
        for arm in ARMS:
            r=next(r for r in rows if r['name']==c['name'] and r['arm']==arm);assert r['protocol_valid'] and not r['error'] and r['returncode']==0
            probe=exchange_probe(cache[c['game']][c['ply']],r['move']);assert probe['legal'];labels.append(dict(name=c['name'],game=c['game'],ply=c['ply'],side=c['side'],arm=arm,move=r['move'],**probe))
    scores={}
    for arm in ARMS:
        rr=[r for r in labels if r['arm']==arm];scores[arm]=dict(king=sum(r['fatal'] for r in rr),queen=sum((r['queen_exchange_loss'] or 0)>=4 for r in rr),material=sum((r['exchange_loss'] or 0)>=2 for r in rr))
    conditions={}
    for parent in ('base','persistent'):
        fixed=parent+'_fixed';a=scores[parent];b=scores[fixed]
        conditions[fixed]=b['king']<=a['king'] and b['queen']<=a['queen'] and b['material']<=a['material']+(phase=='broad')
        if phase=='queen':
            r=next(r for r in labels if r['name']=='23paw9tn-20' and r['arm']==fixed)
            conditions[fixed]=conditions[fixed] and not r['fatal'] and (r['queen_exchange_loss'] or 0)==0 and not r.get('forced_king_loss_after_capture')
    decision=('advance_to_broad' if phase=='queen' else 'further_review_no_automatic_promotion') if all(conditions.values()) else 'stop_this_backport_screen'
    save(OUT/(phase+'-labels.json'),labels);result=dict(phase=phase,cases=len(cases),calls=len(rows),scores=scores,conditions=conditions,decision=decision);save(OUT/(phase+'-summary.json'),result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    elif command in ('run','summarize'):assert sys.argv[2] in ('queen','broad');globals()[command](sys.argv[2])
    else:raise ValueError(command)
