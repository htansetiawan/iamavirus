"""Build and freeze a private-input ancestry parity/privacy/cost screen."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from patch import apply

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/private-ancestry-20261110'
BUILD=HERE/'build'
PARENT=ROOT/'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
STORE=Path('/media/henrytan/seagate/iamavirus/astra/private-ancestry-20261110')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def env():
    e={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    e.update(MIST_THREADS='2',MIST_HISTORY_TABLE=str(PARENT/'data/history.bin'))
    return e
def feed(case):
    replay=json.loads(Path(case['replay_path']).read_text())
    assert sha(case['replay_path'])==case['replay_sha256']
    us=0 if case['side']=='white' else 1
    lines=[f'{us} 200000 2911100']
    for ply in range(1,case['ply']+1):
        view=replay['frames'][ply][case['side']]
        if (ply-1)%2==us:
            # Only OUR move is passed. Opponent move strings never enter this feed.
            lines.append(f"o {replay['frames'][ply]['move']} {view}")
        else:
            lines.append(f'p {view}')
            # Fixed, shared schedule replaces wall-clock thinning in this screen.
            lines.append('s 4096')
    lines.append('d 32')
    return '\n'.join(lines)+'\n'


def main():
    OUT.mkdir(exist_ok=True);BUILD.mkdir(exist_ok=True)
    commands=[]
    for arm in ('base','track'):
        src=BUILD/arm
        if src.exists():shutil.rmtree(src)
        shutil.copytree(PARENT/'src',src)
        if arm=='track':apply(src)
        cmd=['gcc','-O2','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(src),'-I',str(HERE)]
        if arm=='track':cmd+=['-DTRACK']
        cmd+=[str(HERE/'driver.c'),*[str(src/(n+'.c')) for n in ('board','belief','movemodel')],'-lm','-o',str(BUILD/('driver-'+arm))]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=45);assert r.returncode==0,r.stderr;commands.append(cmd)
    # Original function bodies use the extended header, with unused NULL
    # ancestry, so a paired checker compares every field (not just hashes).
    src=BUILD/'track';(src/'baseline.c').write_text((PARENT/'src/belief.c').read_text())
    names=['zobrist_init','position_key','view_hash','history_mix','belief_history_stats','belief_temperature',
           'belief_init_start','belief_free','belief_after_opponent','belief_after_own','belief_shrink',
           'belief_contains','belief_share','belief_sample','belief_resample','view_moves']
    cmd=['gcc','-O2','-std=c11','-pthread','-D_POSIX_C_SOURCE=199309L','-I',str(src),'-I',str(HERE)]
    original=[*cmd,*['-D'+n+'=base_'+n for n in names],'-c',str(src/'baseline.c'),'-o',str(BUILD/'baseline.o')]
    r=subprocess.run(original,capture_output=True,text=True,timeout=45);assert r.returncode==0,r.stderr;commands.append(original)
    paired=[*cmd,'-DTRACK','-DPAIR',str(HERE/'driver.c'),str(BUILD/'baseline.o'),
            *[str(src/(n+'.c')) for n in ('board','belief','movemodel')],'-lm','-o',str(BUILD/'driver-pair')]
    r=subprocess.run(paired,capture_output=True,text=True,timeout=45);assert r.returncode==0,r.stderr;commands.append(paired)
    prior=json.loads((ROOT/'astra-submissions/analysis/private-reply-join-20261110/plan.json').read_text())
    # Keep only identifiers, immutable input provenance and root selection.
    # No oracle ancestor or hidden recorded reply is copied into this plan.
    cases=[{k:c[k] for k in ('context','game','ply','side','replay_path','replay_sha256')} for c in prior['cases']]
    smoke=[]
    for side in ('white','black'):
        c=dict(next(c for c in cases if c['side']==side));c['ply']=2 if side=='white' else 3
        text=feed(c);outputs={}
        for arm in ('base','track','pair'):
            r=subprocess.run([str(BUILD/('driver-'+arm))],input=text,capture_output=True,text=True,env=env(),timeout=10)
            assert r.returncode==0,(arm,r.stderr,r.returncode)
            outputs[arm]=[json.loads(line) for line in r.stdout.splitlines()]
        a=[r for r in outputs['base'] if r['kind']=='state'];b=[r for r in outputs['track'] if r['kind']=='state']
        assert a==b
        assert a==[r for r in outputs['pair'] if r['kind']=='state']
        assert len(a)==len([r for r in outputs['pair'] if r['kind']=='exact_parity'])
        contexts=[r for r in outputs['track'] if r['kind']=='context'];assert contexts
        smoke.append(dict(side=side,states=len(a),contexts=len(contexts),input=text))
    write(OUT/'preflight.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,commands=commands,smoke=smoke,
          sanitizer='Address/undefined/leak sanitizer unit exits0 outside sandbox ptrace monitor; initial fixture error and sandbox LSan failure retained separately.',
          tests=['EP both colors','castling both wings/colors','promotion and underpromotion','capture','cap','shrink','ownership replacement','recovery exclusion']))
    deps=[HERE/n for n in ('patch.py','prepare.py','run.py','audit.py','driver.c','unit.c','ancestry_types.h','ancestry_impl.h')]
    deps+=[BUILD/('driver-'+a) for a in ('base','track','pair')]+[BUILD/'baseline.o']
    deps+=list((PARENT/'src').glob('*'))+list((BUILD/'track').glob('*'))+list((BUILD/'base').glob('*'))
    deps+=[PARENT/'data/history.bin',ROOT.parent/'fow-starter/referee.py',ROOT/'astra-submissions/iamavirus-v38-mist-c-allchildren.zip']
    deps+=[Path(c['replay_path']) for c in cases]
    write(OUT/'plan.json',dict(at=datetime.now(timezone.utc).isoformat(),cases=cases,cores=[0,1],per_process_seconds=90,total_seconds=900,
          per_output_bytes=64*1024**2,address_space_bytes=3*1024**3,bulk_store=str(STORE),
          dependencies={str(p):sha(p) for p in deps},
          scope='32 reused oracle-development root selections, but actor now receives only own views/moves from initial state. '
                'No hidden reply, true ancestor, true current board or replay path supplied to either binary. '
                'Native model/history prior unchanged. One representative ancestry per merged world, fixed shrink4096 after opponent updates. '
                'No search, Stockfish, learned fit, GPU, release or arena action.',
          criteria=dict(all_states_exact=True,all_exported_edges_and_aliases_verified=True,no_state_or_rng_mutation=True,
                minimum_native_aliases=12,minimum_games_with_aliases=4,max_update_cpu_ratio=1.25,min_base_cpu_for_cost=0.25,
                max_incremental_rss_bytes=128*1024**2,max_ancestry_payload_bytes=64*1024**2,max_generator_cpu_per_context=0.1),
          exclusions='Two-step legality and histories are checked. Complete native-path repetition counts are not retained; '
                     'draw-history certification is still missing, as are counterfactual reaches and continuation values. '
                     'No generated alternative is inserted into our true posterior or assigned a probability.',
          next='Passing permits reference-reach/information-set integration DESIGN review only, not a playing candidate. '
               'Fresh separately selected data and certified draw histories needed before decision/playing confirmation. '
               'Any first failure stops this frozen screen without replacing a started case.'))
    print(json.dumps(dict(prepared=True,cases=len(cases),pins=len(set(map(str,deps))))),flush=True)

if __name__=='__main__':main()
