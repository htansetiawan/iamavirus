"""Post-hoc risk-ranking assessment. Never fit or tune on the diagnostic panel."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sigmoid(x):return 1/(1+math.exp(-x)) if x>=0 else math.exp(x)/(1+math.exp(x))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--predictions',type=Path,default=HERE/'existing-danger-80-result.json')
    p.add_argument('--teacher',type=Path,default=HERE/'teacher-readiness-80-result.json')
    p.add_argument('--referee-dir',type=Path,default=Path('/home/henrytan/git/fow-starter'))
    a=p.parse_args()
    sys.path.insert(0,str(a.referee_dir))
    import chess
    from referee import FowBoard, outcome, position_key
    data=json.loads(a.predictions.read_bytes())
    teacher=json.loads(a.teacher.read_bytes())
    assert data['panel_sha256']==teacher['panel_sha256']
    search={(c['replay'],c['frame']):c for c in teacher['cases']}
    rows=[];counts=defaultdict(Counter);metrics=defaultdict(lambda:defaultdict(list))
    for sample in data['cases']:
        case=sample['case'];key=(case['replay'],case['frame'])
        replay_path=ROOT/case['replay']
        assert sha(replay_path)==case['replay_sha256']
        replay=json.loads(replay_path.read_bytes())
        board=FowBoard();repetitions=Counter({position_key(board):1})
        for frame in replay['frames'][1:case['frame']+1]:
            board.push(board.parse_uci(frame['move']))
            repetitions[position_key(board)]+=1
        assert outcome(board,repetitions) is None
        candidates=[]
        for prediction in sample['native_prediction']['candidates']:
            assert math.isfinite(prediction['neural_logit']) and math.isfinite(prediction['policy'])
            q=board.copy(stack=False)
            try:
                q.push(q.parse_uci(prediction['move']))
            except chess.IllegalMoveError:
                legal=False;fatal=None
            else:
                legal=True;k=q.king(board.turn)
                fatal=k is None or q.is_attacked_by(q.turn,k)
            candidates.append({'move':prediction['move'],'danger_logit':prediction['neural_logit'],
                               'danger_probability':sigmoid(prediction['neural_logit']),
                               'policy':prediction['policy'],'true_legal':legal,'true_king_fatal':fatal})
        by_move={c['move']:c for c in candidates}
        assert len(by_move)==len(candidates)
        root=search[key]['target']['actions']
        missing_root=[c['uci'] for c in root if c['uci'] not in by_move]
        root_candidates=[by_move[c['uci']] for c in root if c['uci'] in by_move]
        risk_order=lambda c:(c['danger_logit'],-c['policy'],c['move'])
        selected={'min_risk_all_native':min(candidates,key=risk_order),
                  'max_policy_all_native':max(candidates,key=lambda c:c['policy']),
                  'min_risk_current_root':None if missing_root else min(root_candidates,key=risk_order),
                  'v35_base':by_move.get(search[key]['protocol_move'])}
        valid=[c for c in candidates if c['true_legal']]
        safe=[c for c in valid if not c['true_king_fatal']]
        fatal=[c for c in valid if c['true_king_fatal']]
        brier=statistics.mean((c['danger_probability']-int(c['true_king_fatal']))**2 for c in valid)
        logloss=statistics.mean(max(c['danger_logit'],0)-c['danger_logit']*int(c['true_king_fatal'])+
                                math.log1p(math.exp(-abs(c['danger_logit']))) for c in valid)
        auc=None
        if safe and fatal:
            auc=sum((s['danger_logit']<f['danger_logit'])+.5*(s['danger_logit']==f['danger_logit'])
                    for s in safe for f in fatal)/(len(safe)*len(fatal))
        ranked=sorted(candidates,key=risk_order)
        safe_rank=next((i+1 for i,c in enumerate(ranked) if c['true_legal'] and not c['true_king_fatal']),None)
        excluded_safe=[c for c in safe if c['move'] in search[key]['target']['avoid_moves']]
        all_escapes_excluded=bool(safe) and not any(c['move'] in {v['uci'] for v in root} for c in safe)
        row={'game':case['game'],'frame':case['frame'],'slice':case['slice'],
             'candidates':candidates,'selected':selected,'missing_v35_root_moves':missing_root,
             'first_safe_risk_rank':safe_rank,'within_decision_safe_fatal_auc':auc,
             'brier':brier,'log_loss':logloss,'all_native_safe_moves_excluded_by_v35':all_escapes_excluded,
             'excluded_safe_moves':excluded_safe}
        rows.append(row)
        for name in ('all',case['slice']):
            c=counts[name];m=metrics[name];c['decisions']+=1
            c['native_candidates']+=len(candidates);c['illegal_native_candidates']+=len(candidates)-len(valid)
            c['missing_root_candidates']+=len(missing_root)
            m['decision_weighted_brier'].append(brier);m['decision_weighted_log_loss'].append(logloss)
            if auc is not None:
                m['mean_within_decision_auc'].append(auc)
                c['decisions_with_safe_and_fatal_candidates']+=1
            for selector,chosen in selected.items():
                if chosen is None:c[selector+'_uncovered']+=1
                else:c[selector+'_unsafe']+=int(not chosen['true_legal'] or chosen['true_king_fatal'])
    summary={name:{**dict(counts[name]),**{metric:statistics.mean(values) for metric,values in metrics[name].items()}}
             for name in counts}
    paired={}
    for selector in ('min_risk_all_native','min_risk_current_root'):
        record=Counter()
        for row in rows:
            base,other=row['selected']['v35_base'],row['selected'][selector]
            if base is None or other is None:
                record['uncovered']+=1
                continue
            base_unsafe=not base['true_legal'] or base['true_king_fatal']
            other_unsafe=not other['true_legal'] or other['true_king_fatal']
            record['both_fatal' if base_unsafe and other_unsafe else 'both_safe' if not base_unsafe and not other_unsafe else 'rescued' if base_unsafe else 'regressed']+=1
        n=record['rescued']+record['regressed'];lo=min(record['rescued'],record['regressed'])
        paired[selector]={**record,'exact_two_sided_discordant_pair_p':
                          min(1.,2*sum(math.comb(n,j) for j in range(lo+1))/2**n) if n else 1.}
    masked=[r for r in rows if r['all_native_safe_moves_excluded_by_v35']]
    print(json.dumps({'classification':'frozen danger-head diagnostic; no fitting, deployment, or strength estimate',
                      'input_sha256':sha(a.predictions),'teacher_sha256':sha(a.teacher),
                      'analyzer_sha256':sha(Path(__file__)),'referee_sha256':sha(a.referee_dir/'referee.py'),
                      'summary_by_slice':summary,'paired_vs_v35_base':paired,'guard_exclusion_cases':[{
                          k:r[k] for k in ('game','frame','first_safe_risk_rank','within_decision_safe_fatal_auc',
                                          'selected','excluded_safe_moves')} for r in masked],
                      'limits':['Balanced historical diagnostic panel is not a population-calibration set or guaranteed clean holdout.',
                                'Minimum-risk selection is only a diagnostic; material and eventual winning value are unmeasured.',
                                'Old C++ particle scores and old fusion coefficients are not used.',
                                'Current-root selector requires complete neural coverage of that root; missing cases are explicit.'],
                      'cases':rows},indent=2))


if __name__=='__main__':main()
