#!/usr/bin/env python3
"""Omniscient orthodox evaluator check, not a Fog of War policy target."""
import chess
import hashlib
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from learning.move_taxonomy import fen

replay=json.loads((ROOT/'data/raw/games/92px495s/replay.json').read_text())
base=chess.Board(fen(replay['frames'][26]['board']))
binary=HERE/'build/bin/stockfish'
engine=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
pending=b''
def send(text): engine.stdin.write((text+'\n').encode());engine.stdin.flush()
def until(prefix):
    global pending
    deadline=time.monotonic()+5; lines=[]
    while time.monotonic()<deadline:
        if b'\n' in pending:
            line,pending=pending.split(b'\n',1);line=line.decode();lines.append(line)
            if line.startswith(prefix):return lines
            continue
        ready,_,_=select.select([engine.stdout],[],[],max(0,deadline-time.monotonic()))
        assert ready,'UCI timeout'
        data=os.read(engine.stdout.fileno(),65536);assert data,'Engine closed pipe';pending+=data
    raise TimeoutError(prefix)
rows=[]
try:
    send('uci');until('uciok');send('isready');until('readyok')
    for seq in [[],['d1d5'],['d1d5','e6d5'],['d1d5','e6d5','f3d5'],
                ['f3d5'],['f3d5','e6d5'],['f3d5','e6d5','d1d5']]:
        b=base.copy()
        for m in seq:b.push_uci(m)
        row={'moves':seq,'fen':b.fen(),'scores':[]}
        for d in [1,8]:
            send('ucinewgame');send('isready');until('readyok')
            send('position fen '+b.fen());send(f'go depth {d} movetime 500')
            lines=until('bestmove')
            info=[l for l in lines if ' score ' in l and ' pv ' in l][-1]
            match=re.search(r'score (cp|mate) (-?\d+)',info);kind,value=match.groups();value=int(value)
            cp=value if kind=='cp' else (30000 if value>0 else -30000)
            row['scores'].append({'depth':d,'cp_white':cp if b.turn else -cp,'pv':info.split(' pv ')[1].split(), 'uci_info':info})
        rows.append(row)
        print(seq,row['scores'],flush=True)
finally:
    engine.kill();engine.wait(timeout=5)
out={'scope':'Post-hoc orthodox-chess evaluator probe on true board; not a FoW policy or strength label.',
     'setup_error':'Initial ad-hoc invocation appended side/counters to an already complete FEN; failed before engine launch. Corrected here.',
     'unbounded_attempt':'First depth-only probe stalled with Python futex wait and Stockfish pipe read. Owned PIDs 151150/151152 terminated; no evidence was emitted. This run bounds each search to 0.5 seconds and API timeout to 5 seconds.',
     'adapter_attempt':'A second python-chess UCI adapter attempt also blocked despite its API timeout; owned PIDs151662/151664 stopped. This run uses a direct pipe/select protocol with hard response deadlines.',
     'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'rows':rows}
(ROOT/'astra-submissions/analysis/conditional-exchange-20261101/omniscient-stockfish-probe.json').write_text(json.dumps(out,indent=2)+'\n')
