#!/usr/bin/env python3
"""Trace changed failure decisions separately from the timed screen."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from run_replay_gate import ROOT, HERE, exchange_probe, protocol, ingest, ca


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('analysis',type=Path)
    ap.add_argument('--cores',default='0,1')
    args=ap.parse_args()
    audit=json.loads((args.analysis/'audit.json').read_text())
    pins=json.loads((args.analysis/'development/pins.json').read_text())
    assert hashlib.sha256((HERE/'build/mist').read_bytes()).hexdigest()==pins['binaries']['mixture']
    rows=[json.loads(s) for s in (args.analysis/'development/results.jsonl').read_text().splitlines()]
    cases={(r['case']['game'],r['case']['ply']):r['case'] for r in rows}
    out=args.analysis/'traces';out.mkdir(exist_ok=False)
    report=[]
    for change in audit['changes']:
        arm=change['arm']
        if arm=='off':continue
        case=cases[change['game'],change['ply']]
        replay=json.loads(Path(case['replay_path']).read_text());states,errors=ingest.validate_replay(replay);assert not errors
        side=('white','black').index(case['side']);feed,forced=protocol(replay,case['ply'],side)
        env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
        env.update(MIST_FORCE_MOVES=','.join(forced),MIST_MAX_SECONDS=str(pins['seconds']),FOW_SEED=str(pins['seed']),
                   MIST_ROOT_CALIB=str({'mixture':1,'residual':2}[arm]),MIST_ROOT_CALIB_TRACE='1',MIST_TIMING='1')
        proc=subprocess.Popen(['taskset','-c',args.cores,'bash',str(HERE/'build/run.sh')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        try:stdout,stderr=proc.communicate(feed,timeout=180)
        except subprocess.TimeoutExpired:
            ca.kill_tree(proc.pid);proc.wait();raise
        moves=[s[5:].strip() for s in stdout.splitlines() if s.startswith('move ')]
        assert proc.returncode==0 and moves[:-1]==forced and len(moves)==len(forced)+1
        label=f"{case['game']}-{case['ply']}-{arm}"
        (out/(label+'.stderr')).write_text(stderr)
        probs={}
        for line in stderr.splitlines():
            if line.startswith('astra_calib '):
                tokens=line.split();probs[tokens[1]]={k:float(v) for k,v in (t.split('=') for t in tokens[2:])}
        entry={'case':case,'arm':arm,'gate_v35':change['v35']['move'],'gate_move':change['candidate']['move'],
               'trace_move':moves[-1],'repeat_gate_move':moves[-1]==change['candidate']['move'],
               'truth_outcome':exchange_probe(states[case['ply']],moves[-1]),'probabilities':probs,
               'log_sha256':hashlib.sha256(stderr.encode()).hexdigest()}
        report.append(entry)
        (args.analysis/'traces.json').write_text(json.dumps({'scope':'Print-only diagnostics after the screen; not extra gate observations. Wall-clock belief thinning and logging can change decisions.','records':report},indent=2)+'\n')
        print(label,moves[-1],entry['repeat_gate_move'],flush=True)


if __name__=='__main__':main()
