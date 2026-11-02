"""Freeze and execute two first-attempt, short-budget continuation probes."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from build import BASE,ZIP
from continuation import HERE,ROOT,REF,actor_prefix,prefix,run,sha,validate_prefix
from local_turn_control import cleanup_registry

OUT=ROOT/'astra-submissions/analysis/private-continuation-20261102'
REFRESH=ROOT/'astra-submissions/analysis/arena-refresh-20261102-residual'


def now():return datetime.now(timezone.utc).isoformat()


def write(p,value):
    with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def clean_env():
    e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_','OMP_','OPENBLAS_','MKL_'))}
    e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    return e


def prepare():
    assert json.loads((OUT/'preflight.json').read_text())['passed']
    manifest=json.loads((REFRESH/'manifest.json').read_text())
    top={p['name'] for p in json.loads((REFRESH/'standings.json').read_text())['players'] if p['rank']<=12}
    candidates=[]
    for gid,digest in manifest['sha256'].items():
        path=ROOT/'data/raw/games'/gid/'replay.json';assert sha(path)==digest
        replay=json.loads(path.read_text())
        if replay['white'] not in top or replay['black'] not in top or len(replay['frames'])<=34:continue
        candidates.append((hashlib.sha256(('241-prefix:'+gid).encode()).hexdigest(),gid,path,replay))
    cases=[]
    for index,(_,gid,path,replay) in enumerate(sorted(candidates)[:2]):
        branch=32+index;p=prefix(replay,branch);validate_prefix(p)
        pref=OUT/f'prefix-{index}.json';write(pref,p)
        cases.append(dict(id=f'continuation-{index}',game=gid,branch_ply=branch,prefix=str(pref.relative_to(ROOT)),
            prefix_sha256=sha(pref),source_replay=str(path.relative_to(ROOT)),source_replay_sha256=sha(path),
            seed=2411102+2*index))
    assert len(cases)==2
    dependencies=[*HERE.glob('*.py'),HERE/'README.md',HERE/'build/mist',OUT/'build.json',OUT/'preflight.json',
                  REF,BASE/'bin/stockfish',BASE/'data/history.bin',ZIP,ROOT/'astra-submissions/tools/local_turn_control.py',
                  REFRESH/'manifest.json',REFRESH/'standings.json']
    plan=dict(at=now(),cases=cases,selection='First two SHA256(241-prefix:id) games among refresh457, both teams in snapshot top12, more than34 frames; no outcome filter or score inspection.',
        deps={str(p):sha(p) for p in dependencies},per_move_cap=1.,max_continuation_plies=64,
        per_job_wall_seconds=300,batch_wall_seconds=650,cores=[0,1],retries=0,
        gate='No protocol/legality/privacy/state/clock-restoration failure. Report natural terminals, censored continuations and cost separately. Technical error stops subsequent jobs. No strength gate or training follows.',
        continuation_policy='Reconstructed v37-v37, one second maximum search budget, recorded branch clocks and increment. Not original arena internal states or arena-budget policy.',
        data_use='Feasibility only; all source games remain excluded from any later learned-model confirmation. No fitting on 240 holdout.',
        scope='Data-generator feasibility and correctness, not a candidate match or playing-strength estimate.')
    write(OUT/'plan.json',plan)
    print(json.dumps({'plan_sha256':sha(OUT/'plan.json'),'cases':cases}))


def load():
    p=json.loads((OUT/'plan.json').read_text())
    for path,h in p['deps'].items():assert sha(path)==h,path
    for c in p['cases']:assert sha(ROOT/c['prefix'])==c['prefix_sha256']
    return p


def worker(index):
    plan=load();case=plan['cases'][index];directory=OUT/case['id']
    p=json.loads((ROOT/case['prefix']).read_text());commands=[]
    for side in (0,1):
        a=actor_prefix(p,side)
        commands.append(['/usr/bin/env',f'FOW_SEED={case["seed"]+side}',
            f'MIST_FORCE_MOVES={",".join(a["moves"])}','ASTRA_PREFIX_CONTINUE=1',
            f'ASTRA_PREFIX_CLOCKS={",".join(map(str,a["post_clocks"]))}',
            f'MIST_STOCKFISH={BASE/"bin/stockfish"}',f'MIST_HISTORY_TABLE={BASE/"data/history.bin"}',
            f'MIST_MAX_SECONDS={plan["per_move_cap"]}',str(HERE/'build/mist')])
    game=run(p,commands,directory,plan['max_continuation_plies'])
    write(directory/'replay.json',game)


def inspect(case,directory):
    sys.path.insert(0,str(ROOT))
    from learning import ingest
    game=json.loads((directory/'replay.json').read_text());p=json.loads((ROOT/case['prefix']).read_text())
    states,errors=ingest.validate_replay(game)
    assert not errors,errors
    assert not game.get('failedSide') and not game.get('warnings'),game['reason']
    branch=case['branch_ply']
    assert len(game['frames'])>branch+1
    assert all(g[k]==f[k] for g,f in zip(game['frames'][:branch+1],p['frames']) for k in ('board','white','black','move','clocks'))
    assert len(game['continuation']['prefix_observations'])==2*(branch+1)
    for side in (0,1):
        a=actor_prefix(p,side);text=game['privateDiagnostics'][a['side']]
        restored=[float(x) for x in re.findall(r'astra-prefix: decision=\d+ clock=([\d.]+)',text)]
        assert restored==a['post_clocks']
        searches=[line for line in text.splitlines() if line.startswith('mist: n=')]
        assert searches,'no newly searched continuation'
        actual=sum(e['side']==side and not e['prefix'] for e in game['continuation']['steps'])
        assert len(searches)==actual
    # Every delivered observation must match the receiver's view at that exact
    # generated ply, including after divergence. No replay truth is an input.
    for e in game['protocol']['events']:
        if e['direction']=='input' and len(e['text'])==64:
            assert e['text']==game['frames'][e['ply']][e['side']]
    assert not game['protocol']['truncated']
    if game['censored']:
        assert game['result']=='*' and states[-1].outcome() is None
        assert len(game['frames'])-1==branch+64
    else:assert states[-1].outcome()==(game['result'],game['reason'])
    c=game['continuation']
    return dict(case=case['id'],source=case['game'],branch_ply=branch,validated_frames=len(states),
        new_plies=len(game['frames'])-1-branch,natural_result=None if game['censored'] else game['result'],
        reason=game['reason'],censored=game['censored'],wall_seconds=c['wall_seconds'],
        warmup_charged_seconds=c['prefix_cpu_charged_seconds'],continuation_charged_seconds=c['continuation_charged_seconds'],
        final_clocks=game['frames'][-1]['clocks'],replay_sha256=sha(directory/'replay.json'),
        frames_clocks_and_transcripts_verified=True)


def launch():
    plan=load();write(OUT/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    start=time.monotonic();results=[]
    for index,case in enumerate(plan['cases']):
        directory=OUT/case['id'];directory.mkdir(exist_ok=False)
        remaining=plan['batch_wall_seconds']-(time.monotonic()-start)
        assert remaining>=plan['per_job_wall_seconds'],'batch cap cannot cover another attempt'
        write(directory/'started.json',dict(at=now(),case=case))
        p=subprocess.Popen([sys.executable,str(Path(__file__)),'worker','--index',str(index)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,env=clean_env())
        write(directory/'handle.json',dict(pid=p.pid,at=now()))
        timed_out=False
        try:stdout,stderr=p.communicate(timeout=plan['per_job_wall_seconds'])
        except subprocess.TimeoutExpired:
            timed_out=True;p.kill();stdout,stderr=p.communicate()
        unverified=cleanup_registry(directory/'processes.json')
        (directory/'stdout.txt').write_text(stdout);(directory/'stderr.txt').write_text(stderr)
        result=dict(exit=p.returncode,timeout=timed_out,unverified_groups=unverified)
        try:
            assert p.returncode==0 and not timed_out and not unverified,result
            result.update(inspect(case,directory));result['passed']=True
        except Exception as e:result.update(passed=False,error=repr(e))
        write(directory/'result.json',result);results.append(result);print(json.dumps(result),flush=True)
        if not result['passed']:break
    summary=dict(at=now(),planned=2,attempted=len(results),passed=len(results)==2 and all(r['passed'] for r in results),
        rows=results,seconds=time.monotonic()-start,scope=plan['scope'])
    write(OUT/'summary.json',summary)
    print(json.dumps({'passed':summary['passed'],'attempted':len(results),'seconds':summary['seconds']}),flush=True)
    if not summary['passed']:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','launch','worker'));p.add_argument('--index',type=int);a=p.parse_args()
    if a.command=='worker':worker(a.index)
    else:globals()[a.command]()
