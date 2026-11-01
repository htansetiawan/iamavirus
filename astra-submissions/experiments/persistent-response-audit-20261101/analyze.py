#!/usr/bin/env python3
"""Post-execution finite-tree identities and true-board joins; no new decisions."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/persistent-response-audit-20261101'
sys.path.insert(0,str(ROOT))
from learning import ingest,rules
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(w):return w['board'],w['castle'],w['ep']

def main():
    assert json.loads((OUT/'execution.json').read_text())['status']=='complete'
    plan=json.loads((OUT/'plan.json').read_text());receipts=list(map(json.loads,(OUT/'receipts.jsonl').read_text().splitlines()))
    by={(r['name'],r['arm']):r for r in receipts};assert len(by)==len(receipts)==9
    report=[];checks=frames=0
    for case in plan['cases']:
        path=Path(case['path']);assert sha(path)==case['replay_sha256']
        rp=json.loads(path.read_text());states,errors=ingest.validate_replay(rp);assert not errors
        state=states[case['ply']];truth=(state.board.board_string(),state.board.castling,state.board.en_passant);frames+=len(states)
        row=dict(case=case['name'],historical_move=rp['frames'][case['ply']+1]['move'],arms={});samples=[]
        for arm in plan['arms']:
            receipt=by[(case['name'],arm)];assert receipt['protocol_valid'] and receipt['returncode']==0 and not receipt['error']
            stem=OUT/(case['name']+'-'+arm)
            for suffix,k in [('.stdout','stdout_sha256'),('.stderr','stderr_sha256'),('.br.json','br_sha256')]:assert sha(Path(str(stem)+suffix))==receipt[k]
            br=json.loads(Path(str(stem)+'.br.json').read_text());assert br['state_unchanged'] and br['chosen']==receipt['move']
            profiles=[];sample=None
            for profile in br['profiles']:
                values=profile['values'];assert all(a>=b-1e-8 for a,b in zip(values,values[1:]));checks+=1
                if arm=='unrestricted':assert max(values[1:])-min(values[1:])<1e-9
                worlds=profile['worlds'];details=dict(profile=profile['profile'],values=values,
                    current_to_restricted_gap=values[0]-values[1],future_restriction_gap=values[1]-values[2],
                    first_restriction_gap=values[2]-values[3],total_restriction_gap=values[1]-values[3])
                if worlds:
                    assert abs(sum(w['weight'] for w in worlds)-1)<1e-9
                    for j in range(4):assert abs(sum(w['weight']*w['values'][j] for w in worlds)-values[j])<1e-8
                    checks+=5;physical={};true=[];free=0;model=0;model_mass=0
                    for index,w in enumerate(worlds):
                        assert w['branch']==index and w['weight']>=0
                        assert min(w['values'])>=-2-1e-9 and max(w['values'])<=1+1e-9
                        physical[key(w)]=physical.get(key(w),0)+w['weight']
                        board=rules.Board.from_board_string(w['board'],case['side'],w['castle'],w['ep'])
                        assert board.observation(case['side'])==state.board.observation(case['side'])
                        assert profile['profile'] in board.legal_moves();board.push(profile['profile']);checks+=4
                        if w['replies']:
                            assert {r['move'] for r in w['replies']}==set(board.legal_moves());checks+=1
                        if arm=='persistent':
                            assert w['mode'] in (0,1)
                            gap=w['weight']*(w['values'][1]-w['values'][3])
                            if w['mode']==0:
                                assert max(w['values'][1:])-min(w['values'][1:])<1e-8;free+=gap;checks+=1
                            else:model+=gap;model_mass+=w['weight']
                        else:assert w['mode']==-1
                        if key(w)==truth:true.append({k:v for k,v in w.items() if k not in ('board','castle','ep','index')})
                    if sample is None:sample=physical
                    else:assert sample==physical
                    if arm=='persistent':
                        assert abs(model_mass-.25)<1e-9 and abs(free)<1e-9
                        assert abs(model-details['total_restriction_gap'])<1e-8
                        assert -1e-9<=model<=3*model_mass+1e-8;checks+=4
                        details.update(model_mass=model_mass,model_mode_gap_contribution=model,free_mode_gap_contribution=free)
                    details['true_branches']=true
                if arm=='persistent':assert details['total_restriction_gap']<=.75+1e-8;checks+=1
                profiles.append(details)
            assert sample is not None;samples.append(sample)
            row['arms'][arm]=dict(chosen=br['chosen'],nodes=br['nodes'],infosets=br['infosets'],layers=br['layers'],
                first_restricted=br['restricted_first_sets'],later_restricted=br['restricted_later_sets'],audit_seconds=br['seconds'],
                sampled_truth_mass=sample.get(truth,0),profiles=profiles)
        row['identical_sampled_physical_positions']=samples[0]==samples[1]==samples[2]
        report.append(row)
    result=dict(cases=report,checks=checks,frames_verified=frames,analyzer_sha256=sha(Path(__file__)),
                scope='Within each fixed tree and own continuation. Root mode bounds restriction dependence, not actual exploitability; sampled truth mass is not the full belief mass. The three reused development positions are not a strength gate.')
    with (OUT/'analysis.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps({'checks':checks,'frames':frames,'cases':[{**{k:v for k,v in row.items() if k!='arms'},'arms':{a:{**{k:v for k,v in v.items() if k!='profiles'},'profiles':[{k:v for k,v in p.items() if k!='true_branches'} for p in v['profiles']]} for a,v in row['arms'].items()}} for row in report]},indent=2))

if __name__=='__main__':main()
