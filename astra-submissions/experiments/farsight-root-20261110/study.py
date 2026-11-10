"""One selected v38 root: source-exact replay plus read-only post-search export."""
from datetime import datetime, timezone
import argparse
import copy
import difflib
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/farsight-root-20261110'
BUILD = HERE / 'build'
ZIP = ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'
DEPLOYED = ROOT / 'astra-submissions/experiments/guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
TEACHER = ROOT / 'astra-submissions/analysis/deeprl-table-audit-20261025'
REPLAY = ROOT / 'data/astra-spool/v38-latest-ten-20261110/0xe4vmwz.json'
SPOOL = ROOT / 'data/astra-spool/farsight-root-20261110'
FILES = ['board', 'belief', 'movemodel', 'cfr', 'eval', 'search', 'gtcfr', 'front', 'sfeval', 'main']


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p, v):
    with Path(p).open('x') as f: json.dump(v, f, indent=2, allow_nan=False); f.write('\n')


def projection(replay, root_ply, side):
    key = ('white', 'black')[side]
    tc = replay.get('timeControl', {})
    feed = ['fow', f"{('w','b')[side]} {tc.get('baseSeconds',180)} {tc.get('incrementSeconds',2)}"]
    forced, clocks = [], []
    for ply in range(root_ply + 1):
        feed.append(replay['frames'][ply][key])
        if ply % 2 == side:
            feed.append(str(replay['frames'][ply]['clocks'][side]))
            if ply < root_ply:
                forced.append(replay['frames'][ply+1]['move'])
                clocks.append(replay['frames'][ply+1]['clocks'][side])
    return '\n'.join(feed)+'\n', forced, clocks


def environment(folder, forced, clocks, zero=False):
    env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_', 'FOW_', 'ASTRA_'))}
    env.update(MIST_FORCE_MOVES=','.join(forced), ASTRA_POST_CLOCKS=','.join(map(str, clocks)),
        MIST_STOCKFISH=str(DEPLOYED/'bin/stockfish'), MIST_HISTORY_TABLE=str(DEPLOYED/'data/history.bin'),
        ASTRA_SF_ALLCHILDREN='1', FOW_SEED='3091110', MIST_TIMING='1',
        MIST_TEACHER_OUT=str(folder/'targets.jsonl'), ASTRA_ROOT_OUT=str(folder/'population.json'),
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    if zero: env['MIST_MAX_SECONDS'] = '0'
    return env


def run_native(binary, folder, feed, env, timeout=150):
    folder.mkdir(exist_ok=False)
    (folder/'input.txt').write_text(feed)
    write(folder/'settings.json',{k:v for k,v in env.items() if k.startswith(('MIST_','FOW_','ASTRA_'))})
    proc = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)
    stat = Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')', 1)[1].split()
    write(folder/'process.json', dict(at=now(), pid=proc.pid, pgid=proc.pid, start_ticks=int(stat[19])))
    try:
        stdout, stderr = proc.communicate(feed, timeout=timeout)
    except BaseException:
        if proc.poll() is None: os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        (folder/'stdout.txt').write_text(stdout); (folder/'stderr.txt').write_text(stderr)
        write(folder/'failure.json', dict(at=now(), exit_code=proc.returncode))
        raise
    (folder/'stdout.txt').write_text(stdout); (folder/'stderr.txt').write_text(stderr)
    members = []
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try:
            s = (p/'stat').read_text().rsplit(')', 1)[1].split()
            if int(s[2]) == proc.pid and s[0] not in ('Z','X'): members.append(int(p.name))
        except (FileNotFoundError, PermissionError): pass
    if members:
        os.killpg(proc.pid, signal.SIGKILL)
    write(folder/'terminal.json', dict(at=now(), exit_code=proc.returncode, live_owned_members=members))
    assert proc.returncode == 0 and not members, (proc.returncode, stderr[-1000:], members)
    return stdout, stderr


def prepare():
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    assert sha(ZIP) == 'ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    with zipfile.ZipFile(ZIP) as z:
        launchers = [n for n in z.namelist() if n == 'run.sh' or n.endswith('/run.sh')]
        assert len(launchers) == 1, launchers
        prefix = launchers[0][:-len('run.sh')]
        names = [n[len(prefix):] for n in z.namelist() if n.startswith(prefix+'src/') and not n.endswith('/')]
        for arm in ('control', 'observer'):
            dest = BUILD/arm; dest.mkdir()
            for name in names:
                data = z.read(prefix+name); assert data == (DEPLOYED/name).read_bytes()
                p = dest/name; p.parent.mkdir(exist_ok=True); p.write_bytes(data)
        for name in ('bin/stockfish','data/history.bin','run.sh'):
            assert z.read(prefix+name) == (DEPLOYED/name).read_bytes(), name
    source = BUILD/'observer/src'
    p = source/'main.c'; old = p.read_text(); new = old
    needle = '    const char *forced = getenv("MIST_FORCE_MOVES");'
    assert new.count(needle) == 1
    new = new.replace(needle, needle+'\n    const char *post_clocks = getenv("ASTRA_POST_CLOCKS");')
    needle = '            clock_left = reported - (now_seconds() - view_at) + increment;'
    assert new.count(needle) == 1
    new = new.replace(needle, needle+'''
            if (post_clocks) {
                char *end_clock = NULL;
                const double restored = strtod(post_clocks, &end_clock);
                if (end_clock == post_clocks || !isfinite(restored) || restored < 0 ||
                    (*end_clock && *end_clock != ',')) exit(87);
                post_clocks = *end_clock == ',' ? end_clock + 1 : end_clock;
                clock_left = restored;
                fprintf(stderr, "astra-prefix: clock=%.17g\\n", clock_left);
            }
''')
    p.write_text(new)
    (OUT/'clock.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v38/main.c',tofile='observer/main.c')))
    p = source/'gtcfr.c'; old = p.read_text(); new = old.replace('#include "cfr.h"', '#include "cfr.h"\n#include "teacher_dump.h"\n#include "observe.h"')
    needle = '    free(x); free(idx); free(share); free(chance_kids); free(chance_p);'
    assert new.count(needle) == 1
    new = new.replace(needle, '    astra_teacher_dump(&t.g,x,root_I,&ours,out,b,idx,share,K,params);\n'
        '    astra_root_observe(&t.g,x,&ours,b,idx,share,K,chance_kids,t.leaf_of,t.cap_leaf_of);\n'+needle)
    p.write_text(new)
    (OUT/'observer.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v38/gtcfr.c',tofile='observer/gtcfr.c')))
    for name in ('teacher_targets.c','teacher_targets.h','teacher_dump.c','teacher_dump.h'):
        shutil.copyfile(TEACHER/name, source/name)
    for name in ('observe.c','observe.h'): shutil.copyfile(HERE/name, source/name)
    commands = []
    for arm in ('control','observer'):
        extra = ['teacher_targets','teacher_dump','observe'] if arm == 'observer' else []
        cmd = ['gcc','-std=c11','-O2','-pthread','-D_POSIX_C_SOURCE=199309L',
               *['src/'+n+'.c' for n in FILES+extra],'-lm','-o','mist']
        result = subprocess.run(cmd,cwd=BUILD/arm,capture_output=True,text=True,timeout=120)
        (OUT/(arm+'-build.stderr')).write_text(result.stderr)
        assert result.returncode == 0, result.stderr
        commands.append(dict(arm=arm,argv=cmd,binary_sha256=sha(BUILD/arm/'mist')))
    # Bounded deterministic fixed-work checks: zero timed growth, same20final iterations.
    sys.path.insert(0,str(ROOT)); from learning.histories import replay_from_moves
    fixture = replay_from_moves('pref0000',['g1f3','g8f6','f3g1','f6g8'],'*','fixture')
    for i, f in enumerate(fixture['frames']): f['clocks']=[180.-.25*i,180.-.5*i]
    checks = []
    for side, ply in [(0,4),(1,3)]:
        feed, forced, clocks = projection(fixture,ply,side)
        rows = []
        for arm in ('control','observer'):
            folder = OUT/f'preflight-{side}-{arm}';env=environment(folder,forced,clocks,True)
            stdout, stderr = run_native(BUILD/arm/'mist',folder,feed,env,30)
            moves = [s[5:] for s in stdout.splitlines() if s.startswith('move ')]
            assert moves[:-1] == forced
            if arm == 'observer':
                restored = [float(v) for v in re.findall(r'astra-prefix: clock=([\d.]+)',stderr)]
                assert restored == clocks
                t = [json.loads(v) for v in (folder/'targets.jsonl').read_text().splitlines()]
                pop = read(folder/'population.json'); assert len(t) == 1
                assert abs(pop['root_value']-t[0]['root_value']) < 1e-10
                assert [(s['index'],s['weight']) for s in pop['samples']] == [(s['belief_index'],s['weight']) for s in t[0]['samples']]
                assert len(pop['worlds']) == pop['count']
            rows.append(moves)
        assert rows[0] == rows[1]
        checks.append(dict(side=side,fixed_work_moves_match=True,restored_clocks=clocks))
    replay = read(REPLAY);feed, forced, clocks = projection(replay,65,1)
    assert replay['blackVersion'] == 38 and replay['frames'][66]['move'] == 'a2a1r'
    redacted = copy.deepcopy(replay)
    for i, f in enumerate(redacted['frames']):
        f['board']='x'*64; f['white']='x'*64; f['clocks'][0]=-999
        if i and (i-1)%2 != 1: f['move']='a1a1'
    assert projection(redacted,65,1) == (feed,forced,clocks)
    write(OUT/'preflight.json',dict(at=now(),passed=True,checks=checks,private_projection_unchanged=True,
          commands=commands,control_matches_deployed_binary=sha(BUILD/'control/mist')==sha(DEPLOYED/'mist')))
    deps=[Path(__file__),HERE/'observe.c',HERE/'observe.h',HERE/'audit.py',REPLAY,ZIP,DEPLOYED/'mist',DEPLOYED/'bin/stockfish',DEPLOYED/'data/history.bin',ROOT.parent/'fow-starter/referee.py']
    deps += [p for arm in ('control','observer') for p in (BUILD/arm/'src').iterdir() if p.is_file()]
    deps += [BUILD/arm/'mist' for arm in ('control','observer')]
    write(OUT/'plan.json',dict(at=now(),game='0xe4vmwz',root_ply=65,decision_ply=66,side=1,
        seed=3091110,cores=[2,3],process_seconds=150,wall_seconds=180,archive_bytes=134217728,
        spool=str(SPOOL),replay_path=str(REPLAY),dependencies={str(p):sha(p) for p in deps},
        native_settings='Exact v38 defaults/launcher, root32draws, original reported clocks. Prefix post-clock restoration only; both exports run after the original solver chooses. No truth input. One first attempt; no search/scorer/guard/prior changes.',
        nearest_prior='283/285 already implement population/sample/guard diagnostics and close a sampling/guard-only rescue.241 already implements prefix clock restoration. This is reuse on the new pre-cutoff v38 Farsight predecessor, not a new algorithm or a reopened candidate.',
        scope='Selected diagnostic reconstruction, not the historical process RNG/timing or an Elo test. Whole-population placement/rule support, weighted danger families, actual sampled worlds, guard support, fixed-tree root values and reply expansion. No automatic policy, tuning, fit, match, ZIP or promotion.',
        audit='Join truth after native exit. Check every exported sample and reply with the course rules, source/privacy/clock integrity, normalized chance/strategy and recomputed root Q. All-population observations if<=20000, otherwise1024fixed-hash worlds with an explicit sampled-audit scope. No future307sources or models.'))
    print(json.dumps(dict(prepared=True,pins=len(deps),preflight=checks)),flush=True)


def run():
    plan=read(OUT/'plan.json');assert read(OUT/'preflight.json')['passed']
    for p,h in plan['dependencies'].items():assert sha(p)==h,p
    leases=read(ROOT/'chatroom/cores.json')['allocation']
    assert any(x.get('lease')=='309-farsight-root' and x.get('cores')==plan['cores'] for x in leases)
    assert not any(set(x.get('cores',[]))&set(plan['cores']) for x in leases if x.get('lease')!='309-farsight-root')
    assert not SPOOL.exists();SPOOL.mkdir()
    os.sched_setaffinity(0,set(plan['cores']))
    replay=read(REPLAY);feed,forced,clocks=projection(replay,65,1)
    write(OUT/'started.json',dict(at=now(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    start=time.monotonic();folder=SPOOL/'actor'
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('180-second study wall cap')))
    signal.alarm(plan['wall_seconds'])
    try:
        stdout,stderr=run_native(BUILD/'observer/mist',folder,feed,environment(folder,forced,clocks),150)
        assert sum(p.stat().st_size for p in folder.iterdir()) <= plan['archive_bytes']
        moves=[s[5:] for s in stdout.splitlines() if s.startswith('move ')]
        assert len(moves)==len(forced)+1 and moves[:-1]==forced
        assert [float(v) for v in re.findall(r'astra-prefix: clock=([\d.]+)',stderr)] == clocks
        assert (folder/'population.json').is_file() and (folder/'targets.jsonl').is_file()
        for name in ('input.txt','settings.json','stdout.txt','stderr.txt','process.json','terminal.json'):
            shutil.copyfile(folder/name,OUT/name)
        write(OUT/'completion.json',dict(at=now(),status='complete',seconds=time.monotonic()-start,
            move=moves[-1],files={p.name:sha(p) for p in folder.iterdir() if p.is_file()}))
        print(json.dumps(dict(status='complete',move=moves[-1],seconds=time.monotonic()-start)),flush=True)
    except BaseException as e:
        write(OUT/'failure.json',dict(at=now(),status='failed',error=repr(e),seconds=time.monotonic()-start));raise
    finally:
        signal.alarm(0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run'])
    action=parser.parse_args().action
    try: globals()[action]()
    except BaseException as error:
        if action=='prepare' and OUT.is_dir() and not (OUT/'preparation-failure.json').exists():
            write(OUT/'preparation-failure.json',dict(at=now(),error=repr(error)))
        raise
