#!/usr/bin/env python3
"""Join true states only after all nine diagnostic processes are complete."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/response-best-reply-r2-20261101'
sys.path.insert(0,str(ROOT))
from learning import ingest,rules
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(w):return w['board'],w['castle'],w['ep']

def main():
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    plan=json.loads((OUT/'plan.json').read_text());receipts=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()))
    by={(r['name'],r['arm']):r for r in receipts};assert len(by)==len(receipts)==9
    report=[];checks=0;frames=0
    for case in plan['cases']:
        path=Path(case['path']);assert sha(path)==case['replay_sha256'];replay=json.loads(path.read_text());states,errors=ingest.validate_replay(replay);assert not errors
        state=states[case['ply']];frames+=len(states);truth=(state.board.board_string(),state.board.castling,state.board.en_passant)
        historical=replay['frames'][case['ply']+1]['move'];capture=replay['frames'][case['ply']+2]['move']
        row=dict(case=case['name'],historical_move=historical,historical_reply=capture,arms={});beliefs=[];samples=[]
        for arm in plan['arms']:
            receipt=by[(case['name'],arm)];assert receipt['protocol_valid'] and receipt['returncode']==0 and not receipt['error']
            name=case['name']+'-'+arm
            for ext,k in [('stdout','stdout_sha256'),('stderr','stderr_sha256'),('trace.json','trace_sha256'),('br.json','br_sha256')]:assert sha(OUT/(name+'.'+ext))==receipt[k]
            trace=json.loads((OUT/(name+'.trace.json')).read_text());br=json.loads((OUT/(name+'.br.json')).read_text())
            assert br['chosen']==trace['chosen']==receipt['move'] and br['state_unchanged'] and br['nodes']==trace['nodes']
            beliefs.append({key(w):w['weight'] for w in trace['belief']});samples.append({key(trace['belief'][w['belief_index']]):w['weight'] for w in trace['worlds']})
            root={a['move']:a for a in trace['root_actions']};worlds={w['belief_index']:w for w in trace['worlds']};profiles=[]
            for p in br['profiles']:
                vals=p['values'];assert all(a>=b-1e-8 for a,b in zip(vals,vals[1:]))
                gaps=[vals[i]-vals[i+1] for i in range(3)]
                for k,v in zip(['solver_slack','future_restriction_gap','first_restriction_gap'],gaps):assert abs(v-p[k])<1e-10
                assert abs(sum(gaps)-(vals[0]-vals[3]))<1e-10
                if arm=='unrestricted':assert max(vals[1:])-min(vals[1:])<1e-10
                expected=trace['value'] if p['profile']=='mixed' else root[p['profile']]['q'];assert abs(expected-vals[0])<1e-8
                checks+=6;true_worlds=[]
                if p['profile']!='mixed':
                    assert len(p['worlds'])==len(trace['worlds'])
                    assert abs(sum(w['weight'] for w in p['worlds'])-1)<1e-8
                    for j in range(4):assert abs(sum(w['weight']*w['values'][j] for w in p['worlds'])-vals[j])<1e-8
                    for w in p['worlds']:
                        b=trace['belief'][w['index']];original=worlds[w['index']]
                        assert w['board']==b['board']==original['board'] and w['weight']==original['weight']
                        action=next(a for a in original['actions'] if a['move']==p['profile'])
                        assert abs(w['values'][0]-action['q'])<1e-8
                        board=rules.Board.from_board_string(w['board'],case['side'],b['castle'],b['ep'])
                        assert board.observation(case['side'])==state.board.observation(case['side']) and p['profile'] in board.legal_moves()
                        board.push(p['profile']);checks+=3
                        if w['replies']:
                            assert set(board.legal_moves())=={r['move'] for r in w['replies']}
                            originals={r['move']:r for r in action['replies']}
                            for response in w['replies']:
                                assert abs(response['values'][0]-originals[response['move']]['q'])<1e-8
                                # Once past the first reply, both these modes are unrestricted.
                                assert abs(response['values'][2]-response['values'][3])<1e-8
                                checks+=2
                        if key(b)==truth:
                            true_worlds.append(dict(weight=w['weight'],values=w['values'],historical_reply=next((r for r in w['replies'] if r['move']==capture),None)))
                profiles.append({**{k:v for k,v in p.items() if k!='worlds'},'true_worlds':true_worlds})
            row['arms'][arm]=dict(chosen=br['chosen'],nodes=br['nodes'],infosets=br['infosets'],layers=br['layers'],
                first_restricted=br['restricted_first_sets'],later_restricted=br['restricted_later_sets'],audit_seconds=br['seconds'],
                truth_mass=beliefs[-1].get(truth,0),sampled_truth_mass=samples[-1].get(truth,0),
                missing_focus_moves=[m for m in case['focus'].split(',') if m not in root],profiles=profiles)
        row['identical_beliefs']=beliefs[0]==beliefs[1]==beliefs[2];row['identical_samples']=samples[0]==samples[1]==samples[2];report.append(row)
    out=dict(cases=report,validated_frames=frames,checks=checks,
             scope='Selected-case, same-tree nested feasible-set decomposition with fixed own continuation. Not a full-game exploitability bound, release gate or causal explanation of match outcomes.',
             original_failed_attempt='Sibling response-best-reply-20261101 retains the original audit-only crash; these are nine newly frozen R2 calls.')
    (OUT/'analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'frames':frames,'cases':[{'case':c['case'],'arms':{a:{'chosen':r['chosen'],'audit_seconds':r['audit_seconds'],'profiles':[{k:v for k,v in p.items() if k!='true_worlds'} for p in r['profiles']]} for a,r in c['arms'].items()}} for c in report]},indent=2))

if __name__=='__main__':main()
