#!/usr/bin/env python3
"""Distinguish depth-1 evaluator history effects from request-log parsing errors.

Run a small frozen set with the same engine options as m4sf.c. Repeated fresh
ucinewgame calls are a diagnostic, not a proposed default or throughput test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
from m4_sf_reuse_audit import requests,sha


class Engine:
    def __init__(self,path):
        self.process=subprocess.Popen([str(path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.lines=queue.Queue();self.thread=threading.Thread(target=self.read,daemon=True);self.thread.start()
        self.send('uci');self.until('uciok')
        self.send('setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name MultiPV value 256\nisready');self.until('readyok')
    def read(self):
        for line in self.process.stdout:self.lines.put(line.rstrip())
        self.lines.put(None)
    def send(self,command):self.process.stdin.write(command+'\n');self.process.stdin.flush()
    def until(self,prefix):
        rows=[];deadline=time.monotonic()+5
        while True:
            line=self.lines.get(timeout=max(.001,deadline-time.monotonic()))
            if line is None:raise RuntimeError('Engine exited before '+prefix)
            rows.append(line)
            if line.startswith(prefix):return rows
    def fresh(self):
        begin=time.monotonic();self.send('ucinewgame\nisready');self.until('readyok');return time.monotonic()-begin
    def evaluate(self,fen):
        command=f'position fen {fen}\ngo depth 1';start=time.monotonic();self.send(command);lines=self.until('bestmove ')
        records=list(requests(['>> '+s for s in command.splitlines()]+['<< '+s for s in lines]));assert len(records)==1
        row=records[0];row['elapsed']=time.monotonic()-start;return row
    def close(self):
        if self.process.poll() is None:
            try:self.send('quit');self.process.wait(timeout=3)
            except (BrokenPipeError,subprocess.TimeoutExpired):self.process.kill();self.process.wait(timeout=3)
        self.process.stdin.close();self.process.stdout.close();self.thread.join(timeout=1)


def compare(a,b):
    common=set(a['scores'])&set(b['scores']);delta={m:abs(a['scores'][m]-b['scores'][m]) for m in common}
    return {'identical_score_map':a['scores']==b['scores'],'same_move_coverage':set(a['scores'])==set(b['scores']),
            'max_abs_cp_difference':max(delta.values(),default=0),'bestmove_equal':a['bestmove']==b['bestmove']}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    audit=json.loads(args.audit.read_text());r=args.run;assert audit['log_sha256']==sha(r/'stockfish.log')
    manifest=json.loads((r/'manifest.json').read_text());assert sha(r/'stockfish')==manifest['files']['stockfish']['sha256']
    with (r/'stockfish.log').open() as f:recorded=list(requests(f))
    chosen=[];seen=set()
    for example in audit['all_requests']['largest_changes']:
        if example['fen'] not in seen:chosen.append(example);seen.add(example['fen'])
        if len(chosen)==3:break
    # A low-sensitivity repeated opening position provides a comparison.
    first={}
    for record in recorded:
        fen=record['fen']
        if fen in first and fen not in seen and compare(first[fen],record)['max_abs_cp_difference']<5:
            chosen.append({'fen':fen,'repeat_line':record['line'],'max_abs_cp_change':compare(first[fen],record)['max_abs_cp_difference']});break
        first[fen]=record
    engine=Engine(r/'stockfish');results=[]
    try:
        for sample in chosen:
            fen=sample['fen'];index=next(i for i,row in enumerate(recorded) if row['line']==sample['repeat_line'])
            prime=[row['fen'] for row in recorded[max(0,index-20):index]]
            reset_a=engine.fresh();fresh_a=engine.evaluate(fen);self_warm=engine.evaluate(fen)
            for context in prime:engine.evaluate(context)
            primed=engine.evaluate(fen);reset_b=engine.fresh();fresh_b=engine.evaluate(fen)
            results.append({'fen':fen,'original_max_cp_change':sample['max_abs_cp_change'],
                'priming_fens':prime,'reset_seconds':[reset_a,reset_b],
                'fresh_a':fresh_a,'immediate_repeat':self_warm,'after_20_contexts':primed,'fresh_b':fresh_b,
                'reset_reproducibility':compare(fresh_a,fresh_b),'self_warm_difference':compare(fresh_a,self_warm),
                'context_difference':compare(fresh_a,primed)})
    finally:engine.close()
    result={'classification':'controlled evaluator-context diagnostic, not playing strength or proposed runtime setting',
        'engine_sha256':sha(r/'stockfish'),'audit_sha256':sha(args.audit),'tool_sha256':sha(Path(__file__)),
        'configuration':{'Threads':1,'Hash':16,'MultiPV':256,'go':'depth 1'},'cases':results,
        'limits':['The 20-position priming sequence is a controlled intervention, not a replay of the entire earlier engine state.',
            'Scores are parsed with the production adapter rules; fresh runs independently query the engine.',
            'No engine-state reset or cache is enabled in the bot by this diagnostic.']}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k in ['fen','original_max_cp_change','reset_seconds','reset_reproducibility','self_warm_difference','context_difference']} for row in results],indent=2))

if __name__=='__main__':main()
