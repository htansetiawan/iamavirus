"""Replay only historical own views, clocks and forced own actions; no search."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

from prepare import ROOT,OUT,BUILD,sha,write


def feed(case):
    assert sha(case['replay_path'])==case['replay_sha256']
    replay=json.loads(Path(case['replay_path']).read_text());side=['white','black'].index(case['side'])
    lines=['fow',f"{'w' if side==0 else 'b'} 180 2"];moves=[]
    for ply,frame in enumerate(replay['frames'][:case['ply']+1]):
        lines.append(frame[case['side']])
        if ply%2==side:
            lines.append(str(frame['clocks'][side]));moves.append(replay['frames'][ply+1]['move'])
    return '\n'.join(lines)+'\n',moves


def environment(parent,moves,dump):
    env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
    env.update(MIST_HISTORY_TABLE=str(parent/'data/history.bin'),MIST_FORCE_MOVES=','.join(moves),
               MIST_TIMING='1',MIST_THREADS='2',MIST_MAX_SECONDS='10',FOW_SEED='2791000',ASTRA_CAP_DUMP_DIR=str(dump))
    return env


def members(pgid):
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            f=(p/'stat').read_text().rsplit(')',1)[1].split()
            if int(f[2])==pgid and f[0] not in ('Z','X'):found.append(int(p.name))
        except (FileNotFoundError,PermissionError,ProcessLookupError):pass
    return found


def main():
    plan=json.loads((OUT/'plan.json').read_text());parent=Path(plan['parent'])
    for path,digest in plan['dependencies'].items():assert sha(path)==digest,path
    assert os.path.ismount('/media/henrytan/seagate'),'Required bulk drive is not mounted'
    assert shutil.disk_usage('/media/henrytan/seagate').free>=2*1024**3,'Insufficient bulk reserve'
    bulk=Path(plan['bulk_store']);bulk.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,set(plan['cores']));os.nice(10)
    write(OUT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(OUT/'plan.json')))
    start=time.monotonic();rows=[];error=None
    try:
        for case in plan['cases']:
            assert time.monotonic()-start+plan['per_case_seconds']<plan['total_seconds']
            folder=OUT/case['id'];folder.mkdir(exist_ok=False);dump=bulk/case['id'];dump.mkdir(exist_ok=False)
            text,moves=feed(case);(folder/'input.txt').write_text(text)
            clock=time.monotonic();p=subprocess.Popen([str(BUILD/'mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,text=True,env=environment(parent,moves,dump),start_new_session=True)
            write(folder/'process.json',dict(pid=p.pid,pgid=p.pid,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
            timeout=False
            try:stdout,stderr=p.communicate(text,timeout=plan['per_case_seconds'])
            except subprocess.TimeoutExpired:
                timeout=True;os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
            (folder/'stdout.txt').write_text(stdout);(folder/'stderr.txt').write_text(stderr)
            live=members(p.pid)
            events=[json.loads(s) for s in re.findall(r'^astra-cap-mass: (.*)$',stderr,re.M)]
            raw={f.name:dict(path=str(f),sha256=sha(f),bytes=f.stat().st_size) for f in dump.iterdir() if f.is_file()}
            row=dict(case=case,exit_code=p.returncode,timed_out=timeout,live_members=live,seconds=time.monotonic()-clock,
                     events=events,snapshots=raw,forced_moves=len(moves),
                     files={f.name:sha(f) for f in folder.iterdir() if f.is_file()})
            write(folder/'result.json',row);rows.append(row)
            assert p.returncode==0 and not timeout and not live,row
            assert re.findall(r'^move (\S+)$',stdout,re.M)==moves
            assert 'nodes=' not in stderr and 'stockfish ready' not in stderr
            assert len(events)==len(raw) and len({e['stage'] for e in events})==len(events)<=2
            print(json.dumps(dict(case=case['id'],seconds=row['seconds'],events=[dict(stage=e['stage'],discarded=e['discarded_fraction']) for e in events])),flush=True)
    except BaseException as exc:error=repr(exc);raise
    finally:
        write(OUT/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),error=error,completed=len(rows),
              elapsed_seconds=time.monotonic()-start,results=[dict(id=r['case']['id'],sha256=sha(OUT/r['case']['id']/'result.json')) for r in rows],scope=plan['scope']))


if __name__=='__main__':main()
