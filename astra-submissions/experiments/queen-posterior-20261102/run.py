#!/usr/bin/env python3
"""Read-only posterior/guard audit on the already frozen queen panel."""
from datetime import datetime,timezone
import difflib
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/queen-posterior-20261102'
PARENT=ROOT/'astra-submissions/analysis/queen-screen-20261101'
ARCHIVE=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest
from learning.compare_archives import kill_tree
from fresh_taxonomy_gate import exchange_probe


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')


def prepare():
    OUT.mkdir(parents=True,exist_ok=False);build=HERE/'build';build.mkdir(exist_ok=False)
    with zipfile.ZipFile(ARCHIVE) as z:
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(build)
    path=build/'src/main.c';before=path.read_text()
    needle='                qdropped += qout[i];';assert before.count(needle)==1
    after=before.replace(needle,needle+'''
                if (getenv("ASTRA_QDUMP")) {
                    char au[6]; move_to_uci(allowed.moves[i], au);
                    fprintf(stderr, "astra_guard %s %.17g %.17g %.17g %.17g %d\\n",
                            au, krisk[i], kriskt[i], qrisk[i], qriskt[i], out[i]);
                }''')
    needle='        SearchResult r; int ok = 0;';assert after.count(needle)==1
    after=after.replace(needle,'''
        if (getenv("ASTRA_QDUMP") && !(forced && *forced)) {
            fprintf(stderr, "astra_population %zu %d %.17g\\n", b.count, b.overflowed, guard_temp);
            for (size_t ai = 0; ai < b.count; ++ai) {
                char ab[65]; pos_to_board_string(&b.items[ai], ab);
                fprintf(stderr, "astra_world %s %.17g %llu %d %d\\n", ab,
                        b.logw ? (double)b.logw[ai] : 0.0,
                        (unsigned long long)b.items[ai].castle_rooks, b.items[ai].ep, b.items[ai].halfmove);
            }
        }
'''+needle)
    path.write_text(after)
    (OUT/'diagnostic.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/src/main.c','b/src/main.c')))
    r=subprocess.run(['bash','build.sh'],cwd=build,capture_output=True,text=True,timeout=60)
    (OUT/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    parent=json.loads((PARENT/'plan.json').read_text());deps={}
    for p in [ARCHIVE,Path(__file__),build/'mist',build/'bin/stockfish',build/'data/history.bin',PARENT/'plan.json',
              ROOT/'learning/ingest.py',ROOT/'astra-submissions/tools/fresh_taxonomy_gate.py']:
        deps[str(p)]=sha(p)
    for c in parent['cases']:
        source=PARENT/(c['name']+'.input.txt');assert sha(source)==c['input_sha256'];(OUT/source.name).write_bytes(source.read_bytes());deps[str(OUT/source.name)]=sha(source)
    plan=dict(created_at=datetime.now(timezone.utc).isoformat(),dependencies=deps,cases=parent['cases'],games=parent['games'],
              cores='2,3',seconds=parent['seconds'],seed=parent['seed'],timeout_seconds=120,
              before_main_sha256=hashlib.sha256(before.encode()).hexdigest(),after_main_sha256=sha(path),
              scope='Eight existing cases, one instrumented v37 call each; diagnostic only. Patch only logs already-computed guards and final belief. No truth, opponent moves or future replies supplied to the engine. No weights, guards or decisions edited. Logging may affect time; results do not replace the original screen or change confirmation 219.',
              questions=['Does true placement remain in support, and with what fitted/sharpened mass?',
                         'Does the known queen capturer remain represented?',
                         'Which true immediate-safe / exchange-safe alternatives does the combined guard exclude?'],
              stopping='Retain all first attempts, stop on technical failure, no automatic retry. No candidate promotion or tuning from this selected diagnostic.')
    save(OUT/'plan.json',plan);print(json.dumps({'prepared':8,'plan_sha256':sha(OUT/'plan.json')}))


def run():
    plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['dependencies'].items():assert sha(Path(p))==h,p
    execution=dict(started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),status='running',completed=0)
    with (OUT/'execution.json').open('x') as f:json.dump(execution,f)
    try:
        with (OUT/'receipts.jsonl').open('x') as sink:
            for c in plan['cases']:
                env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','ASTRA_','FOW_','OMP_','OPENBLAS_','MKL_'))}
                env.update(ASTRA_QDUMP='1',MIST_FORCE_MOVES=','.join(c['forced']),MIST_MAX_SECONDS=str(plan['seconds']),
                           MIST_STOCKFISH=str(HERE/'build/bin/stockfish'),MIST_HISTORY_TABLE=str(HERE/'build/data/history.bin'),
                           FOW_SEED=str(plan['seed']),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
                start=time.monotonic();proc=subprocess.Popen(['taskset','-c',plan['cores'],str(HERE/'build/mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
                error=None
                try:stdout,stderr=proc.communicate((OUT/(c['name']+'.input.txt')).read_text(),timeout=plan['timeout_seconds'])
                except subprocess.TimeoutExpired:kill_tree(proc.pid);stdout,stderr=proc.communicate();error='timeout'
                with (OUT/(c['name']+'.stdout')).open('x') as f:f.write(stdout)
                with gzip.open(OUT/(c['name']+'.stderr.gz'),'xt') as f:f.write(stderr)
                moves=[s[5:] for s in stdout.splitlines() if s.startswith('move ')]
                population=[s for s in stderr.splitlines() if s.startswith('astra_population ')]
                row=dict(name=c['name'],returncode=proc.returncode,error=error,elapsed=time.monotonic()-start,
                         protocol_valid=stdout.splitlines()[0]=='ready' and moves[:-1]==c['forced'] and len(moves)==len(c['forced'])+1,
                         move=moves[-1] if moves else None,population_headers=population,stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
                sink.write(json.dumps(row)+'\n');sink.flush();execution['completed']+=1;save(OUT/'execution.json',execution);print(json.dumps(row),flush=True)
                assert proc.returncode==0 and not error and row['protocol_valid'] and len(population)==1,row
        execution['status']='complete'
    except BaseException:execution['status']='failed';raise
    finally:execution['ended']=datetime.now(timezone.utc).isoformat();save(OUT/'execution.json',execution)


def summarize():
    plan=json.loads((OUT/'plan.json').read_text());assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    receipts=[json.loads(s) for s in (OUT/'receipts.jsonl').read_text().splitlines()];assert len(receipts)==8
    summaries=[];labelled=[]
    for c,row in zip(plan['cases'],receipts):
        assert c['name']==row['name'];rp_path=ROOT/'data/raw/games'/c['game']/'replay.json';assert sha(rp_path)==c['replay_sha256']
        replay=json.loads(rp_path.read_text());states,errors=ingest.validate_replay(replay);assert not errors;state=states[c['ply']]
        with gzip.open(OUT/(c['name']+'.stderr.gz'),'rt') as f:stderr=f.read()
        assert hashlib.sha256(stderr.encode()).hexdigest()==row['stderr_sha256']
        worlds=[];guards=[];population=None
        for line in stderr.splitlines():
            a=line.split()
            if not a:continue
            if a[0]=='astra_world':worlds.append(dict(board=a[1],logw=float(a[2]),castle=int(a[3]),ep=int(a[4]),halfmove=int(a[5])))
            elif a[0]=='astra_guard':guards.append(dict(move=a[1],king=float(a[2]),king_sharp=float(a[3]),queen=float(a[4]),queen_sharp=float(a[5]),veto=bool(int(a[6]))))
            elif a[0]=='astra_population':population=dict(count=int(a[1]),capped=bool(int(a[2])),temperature=float(a[3]))
        assert population and len(worlds)==population['count'] and guards
        truth=replay['frames'][c['ply']]['board'];temp=population['temperature']
        weights=[[math.exp(w['logw']/power) for w in worlds] for power in (temp,1)]
        def mass(predicate):return [sum(v for w,v in zip(worlds,ww) if predicate(w))/sum(ww) for ww in weights]
        placement=[w for w in worlds if w['board']==truth]
        entry=dict(name=c['name'],cohort=c['cohort'],population=population,true_placement_present=bool(placement),
                   true_placement_worlds=len(placement),true_placement_mass=mass(lambda w:w['board']==truth),played=c['played'],diagnostic_move=row['move'])
        capture=c['recorded_probe'].get('worst_capture')
        if capture:
            square=8*(int(capture[1])-1)+ord(capture[0])-ord('a');piece=truth[square]
            entry.update(punishing_capture=capture,attacker_square=capture[:2],attacker_piece=piece,
                         attacker_square_support=sum(w['board'][square]==piece for w in worlds),
                         attacker_square_mass=mass(lambda w:w['board'][square]==piece))
        for g in guards:
            probe=exchange_probe(state,g['move']);labelled.append(dict(name=c['name'],**g,**probe))
        gg=[g for g in labelled if g['name']==c['name']]
        entry['played_guard']=next(g for g in gg if g['move']==c['played'])
        entry['retained']=[g['move'] for g in gg if not g['veto']]
        entry['rejected_true_safe_alternatives']=[g['move'] for g in gg if g['veto'] and g['legal'] and not g['fatal'] and not g.get('forced_king_loss_after_capture') and g.get('exchange_loss')==0]
        summaries.append(entry)
    save(OUT/'summary.json',dict(scope='Selected diagnostic, not performance or causal strength evidence. Mass order is fitted then sharpened; placement equality does not certify castling/EP/history equality.',cases=summaries))
    save(OUT/'truth-labelled-guards.json',labelled);print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('prepare','run','summarize');globals()[sys.argv[1]]()
