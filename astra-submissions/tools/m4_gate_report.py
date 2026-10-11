#!/usr/bin/env python3
"""Compact audit of a frozen M4 gate, including missing-truth vs policy failures.

The minimum-root-risk selector is a post-hoc diagnostic on recorded action
profiles. It is not a shipped policy, a retrained model, or a strength estimate.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    summary_path=args.run/'summary.json'
    summary=json.loads(summary_path.read_text())
    manifest=args.run/'manifest.json'
    seats=json.loads((args.run/'seats.json').read_text())['cases']
    cases={c['case']:c for c in seats}
    result={k:v for k,v in summary.items() if k!='rows'}
    result.update({'run':str(args.run.resolve()),'manifest_sha256':sha(manifest),
                   'source_summary_sha256':sha(summary_path),'rows':[]})
    failure_buckets=defaultdict(Counter)
    selector_counts=defaultdict(Counter)
    dominance_counts=defaultdict(Counter)
    matched_beliefs=defaultdict(dict)
    for row in summary['rows']:
        r=dict(row)
        key=f"{r['case']}-seed{r['seed']}-{r['variant']}"
        multi_scale=len(summary.get('scales',[]))>1
        label=r['variant']
        if multi_scale:
            key+=f"-scale{r['leaf_scale']:g}"
            label+=f"/scale{r['leaf_scale']:g}"
        r['report_group']=label
        case=cases[r['case']]
        if r['status']=='ok':
            report_path=args.run/'jobs'/key/'results.json'
            report=json.loads(report_path.read_text());raw=report['rows'][0]
            if sha(report_path)!=r['file_hashes']['results.json']:
                raise ValueError(f'Changed report: {key}')
            diagnostic=next((p for p in (args.run/'jobs'/key).glob('*.stderr') if p.name!='probe.stderr'),None)
            if diagnostic is not None:
                if sha(diagnostic)!=r['file_hashes'][diagnostic.name]:
                    raise ValueError(f'Changed engine diagnostic: {key}')
                lines=[line for line in diagnostic.read_text().splitlines() if line.startswith('mist: n=')]
                if lines:
                    r['engine_work']={k:int(v) for k,v in re.findall(r'\b(n|samples|moves|infosets|nodes|iters)=(\d+)',lines[-1])}
            profiles=raw.get('action_profiles',[])
            actual=next((p for p in profiles if p['move']==r['chosen']),None)
            ranked=sorted(profiles,key=lambda p:(p['fatal'],-p['raw'],p['move']))
            if actual and ranked:
                alternative=ranked[0]
                best_value=max(profiles,key=lambda p:p['raw'])
                zero_risk=[p for p in profiles if p['fatal']<=1e-12]
                best_zero=max(zero_risk,key=lambda p:p['raw']) if zero_risk else None
                r['final_profile_diagnostic']={
                    'best_raw_move':best_value['move'],
                    'best_raw_advantage_over_chosen':best_value['raw']-actual['raw'],
                    'best_raw_would_lose':best_value['move'] not in case['safe_moves'],
                    'zero_risk_actions':len(zero_risk),
                    'best_zero_risk_move':best_zero['move'] if best_zero else None,
                    'best_zero_risk_value_gap':best_zero['raw']-actual['raw'] if best_zero else None,
                    'best_zero_risk_would_lose':best_zero['move'] not in case['safe_moves'] if best_zero else None}
                r['posthoc_minimum_risk']={'move':alternative['move'],'root_fatal_share':alternative['fatal'],
                    'raw_value':alternative['raw'],'would_lose':alternative['move'] not in case['safe_moves'],
                    'chosen_root_fatal_share':actual['fatal'],'chosen_raw_value':actual['raw']}
                selection=selector_counts[label+'/'+r['cohort']]
                selection['available']+=1
                selection['chosen_loses']+=r['immediate_loss']
                selection['posthoc_loses']+=alternative['move'] not in case['safe_moves']
                selection['posthoc_changes']+=alternative['move']!=r['chosen']
                selection['saves']+=r['immediate_loss'] and alternative['move'] in case['safe_moves']
                selection['regressions']+=not r['immediate_loss'] and alternative['move'] not in case['safe_moves']
                # Development diagnosis only: truth labels are used after the
                # choice, never to identify a dominating action.
                dominators=[p for p in profiles if p['fatal']<actual['fatal']-1e-9 and p['raw']>=actual['raw']]
                replacement=min(dominators,key=lambda p:(p['fatal'],-p['raw'],p['move'])) if dominators else actual
                loss=replacement['move'] not in case['safe_moves']
                r['posthoc_dominance']={'move':replacement['move'],'dominating_actions':len(dominators),
                    'root_fatal_share':replacement['fatal'],'raw_value':replacement['raw'],'would_lose':loss}
                dc=dominance_counts[label+'/'+r['cohort']];dc['available']+=1
                dc['changes']+=replacement['move']!=actual['move'];dc['chosen_loses']+=r['immediate_loss']
                dc['posthoc_loses']+=loss;dc['saves']+=r['immediate_loss'] and not loss
                dc['regressions']+=not r['immediate_loss'] and loss
            if r['immediate_loss']:
                bucket=('unavoidable' if case['unavoidable_immediate_loss'] else
                        'tactical_truth_absent_from_belief' if not r.get('belief_tactical_states',0) else
                        'root_diagnostic_unavailable' if not r.get('dumped_current_roots',0) else
                        'truth_board_absent_from_roots' if not r.get('true_board_roots',0) else
                        'truth_present_but_policy_loses')
                r['failure_bucket']=bucket
                failure_buckets[label+'/'+r['cohort']][bucket]+=1
            matched_beliefs[(r['case'],r['seed'])][label]=[
                r.get(k) for k in ['belief_count','belief_true_states','belief_tactical_states','belief_truth_share','belief_tactical_share']]
        result['rows'].append(r)
    result['failure_buckets']={k:dict(v) for k,v in failure_buckets.items()}
    result['posthoc_minimum_risk_selector']={'classification':'descriptive post-hoc choice from frozen profiles; no new search; not a promotion result',
        'rule':'minimize recorded root fatal share; break ties by greatest raw root action value, then UCI',
        'counts':{k:dict(v) for k,v in selector_counts.items()}}
    result['posthoc_dominance_selector']={'classification':'post-hoc development diagnostic, rounded profiles, fixed searched opponent response; no playing-strength claim',
        'rule':'Only replace a selected move if another has strictly lower root fatal share and no lower raw value; select least fatal share among those dominators, then highest value and UCI.',
        'limitation':'Counterfactual root reach is not the posterior. Opponent response and carried blueprint would need revalidation after changing the executed strategy.',
        'counts':{k:dict(v) for k,v in dominance_counts.items()}}
    result['matched_belief_mismatches']=[{'case':k[0],'seed':k[1],'fingerprints':v} for k,v in matched_beliefs.items()
                                        if len(v)>1 and any(x!=next(iter(v.values())) for x in v.values())]
    result['work_by_variant']={}
    for variant in sorted({r['report_group'] for r in result['rows']}):
        valid=[r for r in result['rows'] if r['report_group']==variant and r['status']=='ok']
        stat={}
        for key in ['iters','nodes','samples']:
            values=sorted(r['engine_work'][key] for r in valid if key in r.get('engine_work',{}))
            if values:stat[key]={'count':len(values),'min':min(values),'max':max(values),'mean':sum(values)/len(values),
                                 'median':values[len(values)//2] if len(values)%2 else (values[len(values)//2-1]+values[len(values)//2])/2}
        values=sorted(r['final_metrics']['total'] for r in valid if 'total' in r.get('final_metrics',{}))
        if values:stat['search_seconds']={'count':len(values),'min':min(values),'max':max(values),'mean':sum(values)/len(values)}
        result['work_by_variant'][variant]=stat
    if len(summary.get('scales',[]))==2:
        base,candidate=summary['scales']
        pairs=defaultdict(dict)
        for r in result['rows']:pairs[(r['case'],r['seed'],r['variant'])][r['leaf_scale']]=r
        result['scale_pairs']=[]
        for (case,seed,variant),pair in sorted(pairs.items()):
            if any(s not in pair or pair[s]['status']!='ok' for s in [base,candidate]):continue
            a,b=pair[base],pair[candidate]
            result['scale_pairs'].append({'case':case,'seed':seed,'variant':variant,'cohort':a['cohort'],
                'base_move':a['chosen'],'candidate_move':b['chosen'],'base_loss':a['immediate_loss'],
                'candidate_loss':b['immediate_loss'],'unavoidable':a['unavoidable_immediate_loss']})
        result['unique_seat_summary']={}
        for variant in ['internal','stockfish']:
            for cohort in ['death','survival']:
                pairs=[r for r in result['scale_pairs'] if r['variant']==variant and r['cohort']==cohort]
                saves={r['case'] for r in pairs if r['base_loss'] and not r['candidate_loss']}
                regressions={r['case'] for r in pairs if not r['base_loss'] and r['candidate_loss']}
                result['unique_seat_summary'][variant+'/'+cohort]={
                    'paired_seats':len({r['case'] for r in pairs}), 'paired_seed_decisions':len(pairs),
                    'seats_with_any_save':sorted(saves),'seats_with_any_regression':sorted(regressions),
                    'seats_with_both_directions':sorted(saves&regressions)}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['completed','expected_decisions','complete','paired_outcomes','failure_buckets','posthoc_minimum_risk_selector','matched_belief_mismatches','work_by_variant']},indent=2))


if __name__=='__main__':main()
