"""Fixed-population cost diagnostic for 422; no deciding engine is invoked."""
from datetime import datetime, timezone
import hashlib
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/recapture-guard-cost-20261111'
PRIVATE=ROOT/'data/astra-spool/recapture-guard-cost-20261111'
BUILD=HERE/'build'
ENGINE=ROOT.parent/'fowsearch-c'
SOURCE=ROOT/'astra-submissions/experiments/safe-recapture-integration-20261111/build/coherent/src/main.c'
NAMES=['board','belief','movemodel','cfr','eval','search','gtcfr','front','sfeval']


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')


def function(source,name):
    match=re.search(r'^static (?:void|int) '+re.escape(name)+r'\(',source,re.M)
    assert match,name
    start=match.start();brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def prepare():
    spec=read(OUT/'spec.json')
    for p,v in spec['pins'].items():assert sha(ROOT/p)==v,p
    assert spec['runner_sha256']==sha(Path(__file__))
    BUILD.mkdir(exist_ok=False);PRIVATE.mkdir(exist_ok=False)
    tree=BUILD/'tree';tree.mkdir();shutil.copytree(ENGINE/'src',tree/'src')
    original=(ENGINE/'src/main.c').read_text();coherent=SOURCE.read_text()
    helper=function(coherent,'astra_safe_recapture')
    ticks=[('    const bb_t destination', '    ++bench_calls;'),
           ('        const int from = __builtin_ctzll(pieces);','        ++bench_scanned;'),
           ('        Position after = *p;','        ++bench_attempts;')]
    profiled=helper
    for anchor,statement in ticks:
        assert profiled.count(anchor)==1
        profiled=profiled.replace(anchor,'#ifdef ASTRA_COUNT_GUARD\n'+statement+'\n#endif\n'+anchor,1)
    profile=coherent.replace(helper,profiled,1)
    stripped=re.sub(r'#ifdef ASTRA_COUNT_GUARD\n[^\n]*\n#endif\n','',profile)
    assert stripped==coherent
    (tree/'src/profile-main.c').write_text(profile)
    baseline=[]
    for name in ('queen_risks','best_capture_net','piece_risks'):
        old=function(original,name);new=re.sub(r'\b(queen_risks|best_capture_net|piece_risks)\b',lambda m:'baseline_'+m[0],old)
        assert re.sub(r'\bbaseline_(queen_risks|best_capture_net|piece_risks)\b',lambda m:m[1],new)==old
        baseline.append(new)
    prefix='static unsigned long long bench_calls, bench_scanned, bench_attempts;\n#define main astra_unused_protocol_main\n#include "profile-main.c"\n#undef main\n'
    bench=prefix+'\n'.join(baseline)+'\n'+(HERE/'bench.c').read_text()
    (tree/'src/component-bench.c').write_text(bench)
    compile_receipts=[]
    for name,flags in [('bench',[]),('trace',['-DASTRA_COUNT_GUARD'])]:
        argv=['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',*flags,*['src/'+n+'.c' for n in NAMES],'src/component-bench.c','-lm','-o',name]
        p=subprocess.run(argv,cwd=tree,capture_output=True,text=True,timeout=15)
        compile_receipts.append(dict(binary=name,argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        assert p.returncode==0,p.stderr
    save(OUT/'compilation.json',compile_receipts)
    path=ROOT/'astra-submissions/experiments/promotion-ledger-20261110/check.py'
    s=importlib.util.spec_from_file_location('existing_guard_cost_reference',path);oracle=importlib.util.module_from_spec(s);s.loader.exec_module(oracle)
    ref,chess=oracle.ref,oracle.ref.chess
    cases=[]
    for config in spec['cases']:
        if config['kind']=='saved':
            pop=read(ROOT/config['source']);worlds=pop['worlds'];us=pop['us'];temperature=pop['temperature']
        elif config['kind']=='cycle-saved':
            pop=read(ROOT/config['source']);worlds=[pop['worlds'][i%len(pop['worlds'])] for i in range(config['count'])];us=pop['us'];temperature=pop['temperature']
        else:
            assert config['kind']=='constructed-repeat'
            case=read(ROOT/config['source'])[0];world=dict(board=case['board'],side=0,castle='0',ep=-1,halfmove=0,logw=0)
            worlds=[world]*config['count'];us=0;temperature=2
        w=worlds[0];b=ref.FowBoard(None);b.turn=us==0;b.castling_rights=int(w['castle'],16);b.ep_square=None if w['ep']<0 else w['ep'];b.halfmove_clock=w['halfmove']
        for square,piece in enumerate(w['board']):
            if piece!='-':b.set_piece_at(square,chess.Piece.from_symbol(piece))
        view=ref.observation(b,b.turn)
        lines=[f'{len(worlds)} 20000 {us} {temperature} {view}']
        lines += [f"{w['board']} {w['side']} {w['castle']} {w['ep']} {w['halfmove']} {w['logw']}" for w in worlds]
        p=PRIVATE/(config['name']+'.txt')
        with p.open('x') as f:f.write('\n'.join(lines)+'\n')
        cases.append(dict(**config,input_path=str(p.relative_to(ROOT)),input_sha256=sha(p),worlds=len(worlds),us=us,temperature=temperature))
    plan=dict(spec_sha256=sha(OUT/'spec.json'),cases=cases,binaries={n:dict(path=str((tree/n).relative_to(ROOT)),sha256=sha(tree/n)) for n in ('bench','trace')},
              generated_source_sha256={p.name:sha(p) for p in (tree/'src/component-bench.c',tree/'src/profile-main.c')},
              runner_sha256=sha(Path(__file__)),instrumentation='Timed binary has no counter increments; preprocessor blocks strip exactly back to tested coherent source. Separate binary traces one untimed pass.',
              blocks=4,order='AB BA AB BA',minimum_cpu_ns=1000000,case_seconds=60,batch_seconds=120,
              no_retries=True,no_policy=True,limits=spec['limits'])
    save(OUT/'plan.json',plan)
    print(json.dumps({'prepared':True,'cases':len(cases),'no_native_probe_or_timing_started':True}))


def run():
    plan=read(OUT/'plan.json');spec=read(OUT/'spec.json')
    assert sha(OUT/'spec.json')==plan['spec_sha256'] and sha(Path(__file__))==plan['runner_sha256']
    for p,v in spec['pins'].items():assert sha(ROOT/p)==v,p
    for b in plan['binaries'].values():assert sha(ROOT/b['path'])==b['sha256']
    for c in plan['cases']:assert sha(ROOT/c['input_path'])==c['input_sha256']
    allocation=read(ROOT/'chatroom/cores.json')['allocation']
    assert any(x.get('lease')=='423-recapture-cost' and x.get('cores')==[2,3] for x in allocation)
    assert not any(set(x.get('cores',[]))&{2,3} for x in allocation if x.get('lease')!='423-recapture-cost')
    os.sched_setaffinity(0,{2})
    save(OUT/'run-started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    deadline=time.monotonic()+plan['batch_seconds'];results=[]
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    for mode,binary in [('time','bench'),('trace','trace')]:
        for c in plan['cases']:
            seconds=min(plan['case_seconds'],deadline-time.monotonic());assert seconds>0
            argv=[str(ROOT/plan['binaries'][binary]['path']),mode,str(ROOT/c['input_path'])]
            p=subprocess.Popen(argv,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            timed_out=False
            try:stdout,stderr=p.communicate(timeout=seconds)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
            row=dict(case=c['name'],mode=mode,argv=argv,exit_code=p.returncode,timed_out=timed_out,stdout=stdout,stderr=stderr)
            results.append(row)
            with (OUT/'runs.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            assert p.returncode==0 and not timed_out,row
    save(OUT/'completion.json',dict(completed=True,at=now(),native_component_processes=len(results),policy_or_backend_processes=0))
    print(json.dumps({'completed':True,'native_component_processes':len(results),'policy_or_backend_processes':0}))


if __name__=='__main__':
    assert sys.argv[1:] in (['prepare'],['run'])
    (prepare if sys.argv[1]=='prepare' else run)()
