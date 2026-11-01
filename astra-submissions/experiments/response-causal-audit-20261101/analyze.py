#!/usr/bin/env python3
"""Join truth only after all private-history processes are terminal."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/response-causal-audit-20261101'
sys.path[:0]=[str(ROOT),str(ROOT/'astra-submissions/tools')]
from learning import ingest,rules
from fresh_taxonomy_gate import exchange_probe
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def state_key(w):return w['board'],w['castle'],w['ep']

def main():
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    plan=json.loads((OUT/'plan.json').read_text());receipts=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()))
    by={(r['name'],r['arm']):r for r in receipts};assert len(by)==len(receipts)==9
    report=[];checks=0;frames=0
    for case in plan['cases']:
        path=Path(case['path']);assert sha(path)==case['replay_sha256'];rp=json.loads(path.read_text());states,errors=ingest.validate_replay(rp);assert not errors
        frames+=len(states);state=states[case['ply']];truth=state.board.board_string();true_key=(truth,state.board.castling,state.board.en_passant)
        chosen=rp['frames'][case['ply']+1]['move'];reply=rp['frames'][case['ply']+2]['move']
        item=dict(case=case['name'],historical_move=chosen,historical_reply=reply,arms={});beliefs=[];samples=[]
        for arm in plan['arms']:
            record=by[(case['name'],arm)];assert record['returncode']==0 and record['protocol_valid'] and not record['error']
            prefix=case['name']+'-'+arm
            for ext in ('stdout','stderr','trace.json'):
                key='trace_sha256' if ext=='trace.json' else ext+'_sha256';assert sha(OUT/(prefix+'.'+ext))==record[key]
            trace=json.loads((OUT/(prefix+'.trace.json')).read_text());assert trace['chosen']==record['move']
            assert abs(sum(w['weight'] for w in trace['belief'])-1)<1e-8 and abs(sum(w['weight'] for w in trace['worlds'])-1)<1e-8
            beliefs.append({state_key(w):w['weight'] for w in trace['belief']})
            samples.append({state_key(trace['belief'][w['belief_index']]):w['weight'] for w in trace['worlds']})
            truthworlds=[];attacker_mass=0
            for w in trace['worlds']:
                b=trace['belief'][w['belief_index']];board=rules.Board.from_board_string(w['board'],case['side'],b['castle'],b['ep'])
                assert w['board']==b['board'] and board.observation(case['side'])==state.board.observation(case['side'])
                checks+=1;legal=board.legal_moves()
                for action in w['actions']:
                    if not action['expanded']:continue
                    assert action['move'] in legal
                    child=board.copy();child.push(action['move']);assert set(child.legal_moves())=={r['move'] for r in action['replies']}
                    assert abs(sum(r['probability'] for r in action['replies'])-1)<1e-8
                    assert abs(sum(r['probability']*r['q'] for r in action['replies'])-action['q'])<1e-8
                    for response in action['replies']:
                        assert abs(response['probability']-(response['confidence']*response['fixed']+(1-response['confidence'])*response['free']))<1e-8
                    checks+=1+len(action['replies'])
                historical=next(a for a in w['actions'] if a['move']==chosen)
                if reply in [r['move'] for r in historical['replies']]:attacker_mass+=w['weight']
                if state_key(b)==true_key:
                    truthworlds.append(dict(weight=w['weight'],historical_action=historical,
                                           selected_action=next(a for a in w['actions'] if a['move']==trace['chosen'])))
            probabilities={a['move']:a['probability'] for a in trace['root_actions']}
            item['arms'][arm]=dict(chosen=trace['chosen'],nodes=trace['nodes'],belief_count=len(trace['belief']),sample_count=len(trace['worlds']),
                truth_board_mass=sum(w['weight'] for w in trace['belief'] if w['board']==truth),truth_full_state_mass=beliefs[-1].get(true_key,0),
                sampled_truth_mass=samples[-1].get(true_key,0),historical_reply_expanded_world_mass=attacker_mass,
                root_actions=trace['root_actions'],true_worlds=truthworlds,selected_tactical_label=exchange_probe(state,trace['chosen']),
                historical_tactical_label=exchange_probe(state,chosen),root_probability_sum=sum(probabilities.values()))
        item['identical_beliefs_across_arms']=beliefs[0]==beliefs[1]==beliefs[2]
        item['identical_samples_across_arms']=samples[0]==samples[1]==samples[2]
        report.append(item)
    result=dict(scope='Selected diagnostic reconstruction. Different arm trees/strategies can differ; their value differences are not a fixed-tree causal decomposition or proof of move optimality.',
                independent_transition_probability_checks=checks,validated_frames=frames,cases=report)
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'frames':frames,'cases':[dict(case=c['case'],same_belief=c['identical_beliefs_across_arms'],same_samples=c['identical_samples_across_arms'],arms={a:{k:r[k] for k in ['chosen','truth_full_state_mass','sampled_truth_mass','historical_reply_expanded_world_mass']} for a,r in c['arms'].items()}) for c in report]},indent=2))

if __name__=='__main__':main()
