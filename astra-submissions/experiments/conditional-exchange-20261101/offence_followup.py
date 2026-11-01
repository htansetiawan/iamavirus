#!/usr/bin/env python3
"""Post-choice traces of two unselected forcing-clearance opportunities."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PREVIOUS=ROOT/'astra-submissions/analysis/conditional-exchange-20261101'
OUT=ROOT/'astra-submissions/analysis/offensive-choice-20261101'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest,rules,compare_archives as ca
from fresh_taxonomy_gate import protocol
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(path,data):path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def freeze():
    OUT.mkdir(exist_ok=True);assert not (OUT/'plan.json').exists()
    cases=[];old=json.loads((PREVIOUS/'ability-plan.json').read_text())
    for c in old['cases']:
        if c['game'] not in ('5ug2qtkb','rzr3p3jl'):continue
        other={'5ug2qtkb':'g4h3','rzr3p3jl':'f5e6'}[c['game']]
        payload=(ROOT/'data/raw/games'/c['game']/'replay.json').read_bytes();assert sha(payload)==c['replay_sha256']
        rep=json.loads(payload);feed,forced=protocol(rep,c['ply'],c['ply']%2)
        assert sha(feed.encode())==c['input_sha256']
        for seed in (204100,204101,204102):
            name=f'{c["game"]}-{c["ply"]}-{seed}'
            (OUT/(name+'.input.txt')).write_text(feed)
            cases.append({**c,'name':name,'other':other,'seed':seed})
    dump(OUT/'plan.json',{'cases':cases,'provenance':json.loads((HERE/'provenance.json').read_text()),
         'runner_sha256':sha(Path(__file__).read_bytes()),'seconds':2.5,'cores':'0,1',
         'load':'Unrelated user inference and download processes share CPUs. Mechanism traces only, not comparable throughput/strength.',
         'gate':'No automatic candidate from disagreement with a known tactic. Attribute differences first.'})

def run():
    p=json.loads((OUT/'plan.json').read_text());assert sha(Path(__file__).read_bytes())==p['runner_sha256']
    for f,h in p['provenance']['files'].items():assert sha((ROOT/f).read_bytes())==h
    with (OUT/'receipts.jsonl').open('x') as sink:
        for c in p['cases']:
            name=c['name'];feed=(OUT/(name+'.input.txt')).read_text();assert sha(feed.encode())==c['input_sha256']
            env={k:v for k,v in os.environ.items() if not k.startswith(('MIST_','FOW_','ASTRA_'))}
            env.update(MIST_FORCE_MOVES=','.join(c['forced']),MIST_MAX_SECONDS=str(p['seconds']),FOW_SEED=str(c['seed']),
                       MIST_STOCKFISH=str(HERE/'build/bin/stockfish'),MIST_HISTORY_TABLE=str(HERE/'build/data/history.bin'),
                       ASTRA_EXCHANGE_OUT=str(OUT/(name+'.audit.json')),ASTRA_EXCHANGE_MOVES=','.join([c['first'],c['other']]))
            started=time.monotonic();proc=subprocess.Popen(['taskset','-c',p['cores'],str(HERE/'build/mist')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
            error=None
            try:stdout,stderr=proc.communicate(feed,timeout=180)
            except subprocess.TimeoutExpired:ca.kill_tree(proc.pid);stdout,stderr=proc.communicate();error='timeout'
            (OUT/(name+'.stdout')).write_text(stdout);(OUT/(name+'.stderr')).write_text(stderr)
            moves=[l[5:].strip() for l in stdout.splitlines() if l.startswith('move ')]
            valid=proc.returncode==0 and len(moves)==len(c['forced'])+1 and moves[:-1]==c['forced']
            a=OUT/(name+'.audit.json')
            row={'name':name,'exit':proc.returncode,'protocol_valid':valid,'error':error,'elapsed':time.monotonic()-started,
                 'selected':moves[-1] if valid else None,'audit_sha256':sha(a.read_bytes()) if a.exists() else None,
                 'stdout_sha256':sha(stdout.encode()),'stderr_sha256':sha(stderr.encode())}
            sink.write(json.dumps(row)+'\n');sink.flush();print(json.dumps(row),flush=True)
            assert valid and a.exists(),row

def verify():
    plan=json.loads((OUT/'plan.json').read_text());receipts=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()))
    assert len(receipts)==len(plan['cases'])==6
    rows=[];checks=0
    def board(n):return rules.Board.from_board_string(n['board'],n['side'],n['castle'],n['ep'])
    for c,r in zip(plan['cases'],receipts):
        assert c['name']==r['name'] and r['exit']==0 and r['protocol_valid']
        path=OUT/(c['name']+'.audit.json');data=path.read_bytes();assert sha(data)==r['audit_sha256']
        a=json.loads(data);assert a['selected']==r['selected'];side=c['ply']%2
        assert abs(sum(w['weight'] for w in a['worlds'])-1)<1e-8
        actions={x['move']:x for x in a['actions']}
        assert abs(sum(x['p'] for x in actions.values())-1)<1e-8
        assert abs(sum(x['p']*x['q'] for x in actions.values())-a['value'])<1e-8
        seen={}
        def visit(n,b):
            nonlocal checks
            assert (b.board_string(),b.side,b.castling,b.en_passant)==(n['board'],n['side'],n['castle'],n['ep'])
            if not n['children']:return
            assert set(b.legal_moves())=={x['move'] for x in n['children']}
            assert abs(sum(x['p']*x['node']['q'] for x in n['children'])-n['q'])<1e-8
            assert abs(sum(x['p'] for x in n['children'])-1)<1e-8
            signature=[(x['move'],x['p']) for x in n['children']]
            if n['infoset'] in seen:assert seen[n['infoset']]==signature
            seen[n['infoset']]=signature
            for x in n['children']:
                q=b.copy();q.push(x['move']);checks+=1;visit(x['node'],q)
        payload=(ROOT/'data/raw/games'/c['game']/'replay.json').read_bytes();assert sha(payload)==c['replay_sha256']
        states,errors=ingest.validate_replay(json.loads(payload));assert not errors
        truth=states[c['ply']].board;king=truth.king_square(side^1);target=rules.square_index(c['slider_capture'][2:4]);piece=truth.board_string()[target]
        result={'case':c['name'],'selected':a['selected'],'nodes':a['nodes'],'belief_count':a['belief_count'],'unique_sampled_worlds':len(a['worlds']),
                'truth_board_mass':sum(w['weight'] for w in a['worlds'] if w['board']==truth.board_string()),
                'victim_on_true_square_probability':a['marginals'][a['marginal_order'].index(piece)][target],
                'king_on_true_square_probability':a['marginals'][a['marginal_order'].index('k' if side==0 else 'K')][king],
                'root_top5':sorted(actions.values(),key=lambda x:-x['p'])[:5],'alternatives':[]}
        for move in [c['first'],c['other']]:
            if move not in actions:result['alternatives'].append({'move':move,'excluded':True});continue
            value=0;fatal=0;truth_value=0;trace=[]
            for w in a['worlds']:
                n=next(x['node'] for x in w['branches'] if x['move']==move);b=board(w)
                fatal+=w['weight']*b.move_loses_king(move);b.push(move);checks+=1;visit(n,b)
                value+=w['weight']*n['q']
                if w['board']==truth.board_string():truth_value=n['q']
                trace.append({'weight':w['weight'],'q':n['q'],'true_board':w['board']==truth.board_string(),
                              'victim_present':w['board'][target]==piece,'king_present':w['board'][king]==truth.board_string()[king]})
            assert abs(value-actions[move]['q'])<1e-8
            result['alternatives'].append({**actions[move],'king_risk':fatal,'truth_q':truth_value if result['truth_board_mass'] else None,'world_values':trace})
        rows.append(result)
        gz=gzip.compress(data,compresslevel=6,mtime=0);assert gzip.decompress(gz)==data;path.with_suffix('.json.gz').write_bytes(gz)
    dump(OUT/'summary.json',{'runs':len(rows),'independent_edge_checks':checks,'rows':rows,'scope':plan['load']})
    print(json.dumps({'runs':len(rows),'independent_edge_checks':checks}))

if __name__=='__main__':globals()[sys.argv[1]]()
