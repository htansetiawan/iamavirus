#!/usr/bin/env python3
"""Post-hoc print-only traces of the four safety changes; not extra gate runs."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'astra-submissions/tools'))
from fresh_taxonomy_gate import protocol
from learning import compare_archives as ca

out = ROOT/'astra-submissions/analysis/root-loss-cv-20261101'
summary = json.loads((out/'development/summary.json').read_text())
paired = summary['paired']['off->on']['fatal']
selected = set(paired['fixed']+paired['broken'])
rows = [json.loads(l) for l in (out/'development/results.jsonl').read_text().splitlines()]
records = []
for row in rows:
    case = row['case']; key = f"{case['game']}:{case['ply']}"
    if key not in selected: continue
    payload = Path(case['replay_path']).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == case['replay_sha256']
    replay = json.loads(payload)
    feed,forced = protocol(replay,case['ply'],('white','black').index(case['side']))
    env = {k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_'))}
    env.update(MIST_FORCE_MOVES=','.join(forced),MIST_MAX_SECONDS='2.5',FOW_SEED='11012026',
               MIST_ROOT_CV='1',MIST_ROOT_CV_TRACE='1',MIST_TIMING='1')
    proc = subprocess.Popen(['taskset','-c','0,1','bash',str(HERE/'build/run.sh')],env=env,
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        stdout,stderr = proc.communicate(feed,timeout=180)
    except subprocess.TimeoutExpired:
        ca.kill_tree(proc.pid);proc.wait();raise
    moves = [line[5:].strip() for line in stdout.splitlines() if line.startswith('move ')]
    assert proc.returncode == 0 and moves[:-1] == forced and len(moves)==len(forced)+1
    trace = {}
    for move,pop,sample,correction in re.findall(r'astra_cv (\w+) population=([\d.]+) sample=([\d.]+) correction=([+\-\d.]+)',stderr):
        trace[move] = {'population':float(pop),'sample':float(sample),'correction':float(correction)}
    log = out/f"trace-{case['game']}-{case['ply']}.stderr";log.write_text(stderr)
    records.append({'case':key,'gate_off':row['arms']['off']['move'],'gate_on':row['arms']['on']['move'],
                    'trace_move':moves[-1],'trace':trace,'log':str(log.relative_to(ROOT)),
                    'binary_sha256':hashlib.sha256((HERE/'build/mist').read_bytes()).hexdigest()})
    print(key,moves[-1],flush=True)
(out/'correction-traces.json').write_text(json.dumps({'scope':'Post-hoc diagnostics; logging can affect time-bounded search; not added to gate.',
                                                    'records':records},indent=2)+'\n')
