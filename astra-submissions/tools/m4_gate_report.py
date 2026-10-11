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
    matched_beliefs=defaultdict(dict)
    for row in summary['rows']:
        r=dict(row)
        key=f"{r['case']}-seed{r['seed']}-{r['variant']}"
        case=cases[r['case']]
        if r['status']=='ok':
            report_path=args.run/'jobs'/key/'results.json'
            report=json.loads(report_path.read_text());raw=report['rows'][0]
            if sha(report_path)!=r['file_hashes']['results.json']:
                raise ValueError(f'Changed report: {key}')
            profiles=raw.get('action_profiles',[])
            actual=next((p for p in profiles if p['move']==r['chosen']),None)
            ranked=sorted(profiles,key=lambda p:(p['fatal'],-p['raw'],p['move']))
            if actual and ranked:
                alternative=ranked[0]
                r['posthoc_minimum_risk']={'move':alternative['move'],'root_fatal_share':alternative['fatal'],
                    'raw_value':alternative['raw'],'would_lose':alternative['move'] not in case['safe_moves'],
                    'chosen_root_fatal_share':actual['fatal'],'chosen_raw_value':actual['raw']}
                selection=selector_counts[r['variant']+'/'+r['cohort']]
                selection['available']+=1
                selection['chosen_loses']+=r['immediate_loss']
                selection['posthoc_loses']+=alternative['move'] not in case['safe_moves']
                selection['posthoc_changes']+=alternative['move']!=r['chosen']
                selection['saves']+=r['immediate_loss'] and alternative['move'] in case['safe_moves']
                selection['regressions']+=not r['immediate_loss'] and alternative['move'] not in case['safe_moves']
            if r['immediate_loss']:
                bucket=('unavoidable' if case['unavoidable_immediate_loss'] else
                        'tactical_truth_absent_from_belief' if not r.get('belief_tactical_states',0) else
                        'truth_board_absent_from_roots' if not r.get('true_board_roots',0) else
                        'truth_present_but_policy_loses')
                r['failure_bucket']=bucket
                failure_buckets[r['variant']+'/'+r['cohort']][bucket]+=1
            matched_beliefs[(r['case'],r['seed'])][r['variant']]=[
                r.get(k) for k in ['belief_count','belief_true_states','belief_tactical_states','belief_truth_share','belief_tactical_share']]
        result['rows'].append(r)
    result['failure_buckets']={k:dict(v) for k,v in failure_buckets.items()}
    result['posthoc_minimum_risk_selector']={'classification':'descriptive post-hoc choice from frozen profiles; no new search; not a promotion result',
        'rule':'minimize recorded root fatal share; break ties by greatest raw root action value, then UCI',
        'counts':{k:dict(v) for k,v in selector_counts.items()}}
    result['matched_belief_mismatches']=[{'case':k[0],'seed':k[1],'fingerprints':v} for k,v in matched_beliefs.items()
                                        if len(v)==2 and v['internal']!=v['stockfish']]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['completed','expected_decisions','complete','paired_outcomes','failure_buckets','posthoc_minimum_risk_selector','matched_belief_mismatches']},indent=2))


if __name__=='__main__':main()
