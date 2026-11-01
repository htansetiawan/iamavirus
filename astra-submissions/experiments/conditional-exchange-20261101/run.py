#!/usr/bin/env python3
"""Six frozen, private-input diagnostics; no change to the playing decision."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/conditional-exchange-20261101'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest, rules
from learning import compare_archives as ca
from fresh_taxonomy_gate import protocol

def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path,data): path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def freeze():
    OUT.mkdir(exist_ok=False)
    original=json.loads((ROOT/'astra-submissions/analysis/frozen-tree-20261101/early/plan.json').read_text())
    cases=[]
    for game,ply,moves,reply,attacker in [('tjds234d',54,['b1b7','b1b3'],'d6b7','n'),('92px495s',26,['d1d5','f3d5'],'e6d5','b')]:
        source=next(c for c in original['cases'] if c['game']==game and c['ply']==ply)
        data=(ROOT/'data/raw/games'/game/'replay.json').read_bytes(); assert sha(data)==source['replay_sha256']
        replay=json.loads(data); states,errors=ingest.validate_replay(replay); assert not errors
        feed,forced=protocol(replay,ply,source['side'])
        # Prove that the generated input does not depend on truth or their views/moves.
        redacted=json.loads(data)
        for i,f in enumerate(redacted['frames']):
            f['board']='X'*64; f[('black','white')[source['side']]]='X'*64
            if i==0 or (i-1)%2!=source['side'] or i>ply: f['move']='REDACTED'
        assert protocol(redacted,ply,source['side'])==(feed,forced)
        for seed in [11012026,11012027,11012028]:
            name=f'{game}-{ply}-{seed}'; (OUT/(name+'.input.txt')).write_text(feed)
            cases.append({**source,'name':name,'input_sha256':sha(feed.encode()),'forced':forced,'seed':seed,
                          'moves':moves,'reply':reply,'attacker':attacker})
    pins=json.loads((HERE/'provenance.json').read_text())
    with zipfile.ZipFile(ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip') as z:
        base=HERE.parent/'stable-mix-20261101/build/base'
        for p in (base/'src').iterdir():
            assert p.read_bytes()==z.read('src/'+p.name),p
        for p in (HERE/'build/src').iterdir():
            if p.name not in ['gtcfr.c','exchange_audit.h','numeric_audit.h']:
                assert p.read_bytes()==z.read('src/'+p.name),p
    dump(OUT/'plan.json',{'cases':cases,'pins':pins,'runner_sha256':sha(Path(__file__).read_bytes()),
         'seconds':2.5,'cores':'0,1','status':'mechanism diagnosis only; selected known failures, no strength claim',
         'gate':'No parameter change from these cases. Attribute conditional values and test any later candidate on separate evidence.'})
    print('Frozen six cases; all base source matches archive; private-input redaction passes')

def run():
    plan=json.loads((OUT/'plan.json').read_text()); assert sha(Path(__file__).read_bytes())==plan['runner_sha256']
    for name,h in plan['pins']['files'].items(): assert sha((ROOT/name).read_bytes())==h,name
    with (OUT/'receipts.jsonl').open('x') as receipt:
        for case in plan['cases']:
            name=case['name']; feed=(OUT/(name+'.input.txt')).read_text(); assert sha(feed.encode())==case['input_sha256']
            env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
            env.update(MIST_FORCE_MOVES=','.join(case['forced']),MIST_MAX_SECONDS=str(plan['seconds']),
                       FOW_SEED=str(case['seed']),MIST_STOCKFISH=str(HERE/'build/bin/stockfish'),
                       MIST_HISTORY_TABLE=str(HERE/'build/data/history.bin'),ASTRA_EXCHANGE_OUT=str(OUT/(name+'.audit.json')),
                       ASTRA_EXCHANGE_MOVES=','.join(case['moves']))
            start=time.monotonic()
            proc=subprocess.Popen(['taskset','-c',plan['cores'],str(HERE/'build/mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
            error=None
            try: stdout,stderr=proc.communicate(feed,timeout=180)
            except subprocess.TimeoutExpired:
                ca.kill_tree(proc.pid);stdout,stderr=proc.communicate();error='timeout'
            (OUT/(name+'.stdout')).write_text(stdout);(OUT/(name+'.stderr')).write_text(stderr)
            emitted=[l[5:].strip() for l in stdout.splitlines() if l.startswith('move ')]
            valid=proc.returncode==0 and len(emitted)==len(case['forced'])+1 and emitted[:-1]==case['forced']
            path=OUT/(name+'.audit.json')
            row={'name':name,'exit':proc.returncode,'error':error,'protocol_valid':valid,'move':emitted[-1] if valid else None,
                 'seconds':time.monotonic()-start,'audit_sha256':sha(path.read_bytes()) if path.exists() else None,
                 'stdout_sha256':sha(stdout.encode()),'stderr_sha256':sha(stderr.encode())}
            receipt.write(json.dumps(row)+'\n');receipt.flush();print(json.dumps(row),flush=True)
            assert valid and path.exists(),row

def board(node): return rules.Board.from_board_string(node['board'],node['side'],node['castle'],node['ep'])

def verify():
    plan=json.loads((OUT/'plan.json').read_text());receipts=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()))
    assert len(receipts)==6 and len({r['name'] for r in receipts})==6
    checked=0;rows=[]
    for case,r in zip(plan['cases'],receipts):
        assert r['name']==case['name'] and r['protocol_valid'] and r['exit']==0
        payload=(OUT/(case['name']+'.audit.json')).read_bytes();assert sha(payload)==r['audit_sha256']
        audit=json.loads(payload);assert audit['selected']==r['move']
        assert abs(sum(w['weight'] for w in audit['worlds'])-1)<1e-8
        actions={a['move']:a for a in audit['actions']}
        assert abs(sum(a['p']*a['q'] for a in actions.values())-audit['value'])<1e-8
        infosets={}
        def visit(n,b):
            nonlocal checked
            assert (b.board_string(),b.side,b.castling,b.en_passant)==(n['board'],n['side'],n['castle'],n['ep'])
            if not n['children']:return
            assert set(b.legal_moves())=={c['move'] for c in n['children']}
            assert abs(sum(c['p'] for c in n['children'])-1)<1e-8
            assert abs(sum(c['p']*c['node']['q'] for c in n['children'])-n['q'])<1e-8
            signature=[(c['move'],c['p']) for c in n['children']]
            if n['infoset'] in infosets: assert infosets[n['infoset']]==signature
            else:infosets[n['infoset']]=signature
            for c in n['children']:
                q=b.copy();q.push(c['move']);checked+=1;visit(c['node'],q)
        sq=rules.square_index(case['reply'][:2]);pieceidx=audit['marginal_order'].index(case['attacker'])
        report={'case':case['name'],'selected':audit['selected'],'nodes':audit['nodes'],'belief_count':audit['belief_count'],
                'full_belief_attacker_mass':audit['marginals'][pieceidx][sq],
                'sample_attacker_mass':sum(w['weight'] for w in audit['worlds'] if w['board'][sq]==case['attacker']),
                'actions':[]}
        for move in case['moves']:
            if move not in actions: report['actions'].append({'move':move,'avoided':True});continue
            ag=defaultdict(float);attacker_worlds=[]
            for w in audit['worlds']:
                branch=next(c['node'] for c in w['branches'] if c['move']==move)
                b=board(w);b.push(move);checked+=1;visit(branch,b)
                mass=w['weight'];present=w['board'][sq]==case['attacker']
                ag['q']+=mass*branch['q'];ag['attacker_q_numerator']+=mass*branch['q']*present
                ag['expanded_mass']+=mass*(branch['type']==1)
                reply=next((c for c in branch['children'] if c['move']==case['reply']),None)
                if reply:
                    ag['reply_probability']+=mass*reply['p']
                    if present:
                        alternatives=sorted(branch['children'],key=lambda c:-c['p'])[:3]
                        child=reply['node'];responses=sorted(child['children'],key=lambda c:-c['p'])[:3]
                        attacker_worlds.append({'weight':mass,'reply_p':reply['p'],'reply_q':child['q'],'branch_q':branch['q'],
                          'reply_expanded':child['type']==1,'reply_stored_value':child['stored_value'],
                          'opponent_infoset':branch['infoset'],
                          'top_replies':[{'move':c['move'],'p':c['p'],'q':c['node']['q']} for c in alternatives],
                          'top_responses':[{'move':c['move'],'p':c['p'],'q':c['node']['q'],'expanded':c['node']['type']==1} for c in responses]})
            assert abs(ag['q']-actions[move]['q'])<1e-8
            am=report['sample_attacker_mass']
            report['actions'].append({**actions[move],**ag,'q_given_attacker':ag['attacker_q_numerator']/am if am else None,
                'q_without_attacker':(ag['q']-ag['attacker_q_numerator'])/(1-am) if am<1 else None,
                'attacker_worlds':attacker_worlds})
        rows.append(report)
    dump(OUT/'summary.json',{'runs':len(rows),'independent_edge_checks':checked,'rows':rows})
    print(json.dumps({'runs':len(rows),'independent_edge_checks':checked}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['freeze','run','verify']);globals()[ap.parse_args().command]()
