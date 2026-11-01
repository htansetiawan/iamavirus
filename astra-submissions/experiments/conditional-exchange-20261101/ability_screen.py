#!/usr/bin/env python3
"""Does unchanged v37 find the verified clearance tactic from permitted history?

Six known positive cases. Missing the recorded move is NOT proof of a bad
choice: different attacks can be better. No win rate or Elo is inferred.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/conditional-exchange-20261101'
BASE=HERE.parent/'stable-mix-20261101/build/base'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools'),str(HERE)]
from learning import ingest,compare_archives as ca
from fresh_taxonomy_gate import protocol
from mine_clearance import prove
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')

def freeze():
    cases=[]
    for e in json.loads((OUT/'clearance-corpus.json').read_text())['hits']:
        payload=(ROOT/'data/raw/games'/e['game']/'replay.json').read_bytes();assert sha(payload)==e['replay_sha256']
        rep=json.loads(payload);side=e['ply']%2;feed,forced=protocol(rep,e['ply'],side)
        redacted=json.loads(payload)
        for i,f in enumerate(redacted['frames']):
            f['board']='X'*64;f[('black','white')[side]]='X'*64
            if i==0 or (i-1)%2!=side or i>e['ply']:f['move']='REDACTED'
        assert protocol(redacted,e['ply'],side)==(feed,forced)
        name=e['game']+'-'+str(e['ply']);(OUT/(name+'.ability.input.txt')).write_text(feed)
        cases.append({**e,'name':name,'forced':forced,'input_sha256':sha(feed.encode())})
    p={'cases':cases,'seed':204100,'seconds':2.5,'script_sha256':sha(Path(__file__).read_bytes()),
       'dependencies':{str(p):sha(p.read_bytes()) for p in [BASE/'mist',BASE/'bin/stockfish',BASE/'data/history.bin',HERE/'mine_clearance.py']},
       'scope':__doc__}
    with (OUT/'ability-plan.json').open('x') as f:json.dump(p,f,indent=2)

def run():
    plan=json.loads((OUT/'ability-plan.json').read_text());assert sha(Path(__file__).read_bytes())==plan['script_sha256']
    for p,h in plan['dependencies'].items():assert sha(Path(p).read_bytes())==h
    rows=[]
    with (OUT/'ability-receipts.jsonl').open('x') as sink:
        for c in plan['cases']:
            name=c['name'];feed=(OUT/(name+'.ability.input.txt')).read_text();assert sha(feed.encode())==c['input_sha256']
            env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
            env.update(MIST_FORCE_MOVES=','.join(c['forced']),MIST_MAX_SECONDS=str(plan['seconds']),FOW_SEED=str(plan['seed']),
                       MIST_STOCKFISH=str(BASE/'bin/stockfish'),MIST_HISTORY_TABLE=str(BASE/'data/history.bin'))
            start=time.monotonic();proc=subprocess.Popen(['taskset','-c','0,1',str(BASE/'mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
            error=None
            try:stdout,stderr=proc.communicate(feed,timeout=180)
            except subprocess.TimeoutExpired:ca.kill_tree(proc.pid);stdout,stderr=proc.communicate();error='timeout'
            (OUT/(name+'.ability.stdout')).write_text(stdout);(OUT/(name+'.ability.stderr')).write_text(stderr)
            moves=[l[5:].strip() for l in stdout.splitlines() if l.startswith('move ')]
            valid=proc.returncode==0 and len(moves)==len(c['forced'])+1 and moves[:-1]==c['forced']
            receipt={'case':name,'exit':proc.returncode,'protocol_valid':valid,'seconds':time.monotonic()-start,'error':error,
                     'stdout_sha256':sha(stdout.encode()),'stderr_sha256':sha(stderr.encode()),'move':moves[-1] if valid else None}
            sink.write(json.dumps(receipt)+'\n');sink.flush();assert valid,receipt
            payload=(ROOT/'data/raw/games'/c['game']/'replay.json').read_bytes();assert sha(payload)==c['replay_sha256']
            states,errors=ingest.validate_replay(json.loads(payload));assert not errors
            state=states[c['ply']];move=moves[-1];assert move in state.board.legal_moves()
            chosen=state.copy();chosen.push(move);proof=prove(state,move,c['slider_capture'])
            row={'case':name,'original_attacker':c['attacker'],'expected':c['first'],'selected':move,
                 'same_move':move==c['first'],'outcome_after_choice':chosen.outcome(),
                 'same_target_proven_gain':proof['minimum_gain'] if proof else None}
            rows.append(row);print(json.dumps(row),flush=True)
    dump(OUT/'ability-summary.json',{'rows':rows,'same_move':sum(r['same_move'] for r in rows),
         'scope':'Six selected positives, one seed, 2.5 seconds; no strength estimate. Other selected moves are not labelled mistakes.'})

if __name__=='__main__':globals()[sys.argv[1]]()
