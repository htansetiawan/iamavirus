"""Summarize the frozen paired panel, checking input hashes before joining."""
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result_path=HERE/'teacher-readiness-80-result.json'
    label_path=HERE/'teacher-readiness-80-labels.json'
    panel_path=ROOT/'astra-submissions/analysis/hidden-slider-zone-20261025/independent-audit-512/teacher-readiness-panel.json'
    result=json.loads(result_path.read_bytes())
    labels=json.loads(label_path.read_bytes())
    panel=json.loads(panel_path.read_bytes())
    assert labels['input_sha256']==sha(result_path)
    assert result['panel_sha256']==sha(panel_path)
    source={(c['replay'],c['frame']):c for c in result['cases']}
    expected={(c['replay'],c['frame']):c for c in panel['cases']}
    assert len(source)==len(result['cases'])
    exclusions=[]
    for row in labels['cases']:
        if row['role']!='base' or row['true_safe_actions']:
            continue
        key=(row['replay'],row['frame'])
        c=source[key]
        safe=expected[key]['safe_replies_offline_only']
        assert safe, 'this report is only for positions with known escapes'
        exclusions.append({'replay':row['replay'],'frame':row['frame'],
                           'true_escapes':safe,'avoid_moves':c['target']['avoid_moves'],
                           'all_true_escapes_explicitly_excluded':set(safe)<=set(c['target']['avoid_moves']),
                           'selected':row['chosen']['uci'],
                           'sampled_current_king_attacked_mass':row['sampled_current_king_attacked_mass'],
                           'guard_messages':[line for line in c['stderr_tail'] if 'guard left out' in line]})
    wall=[c['wall_seconds'] for c in result['cases']]
    search=[]
    for c in result['cases']:
        assert c['target']['samples']==c['paired_target']['samples']
        assert len(c['paired_runtime'])==2
        search.extend(float(re.search(r'elapsed=(\S+)',line)[1]) for line in c['paired_runtime'])
    summary={'classification':'balanced historical diagnostic panel, not arena strength or clean holdout',
             'input_hashes':{'result':sha(result_path),'labels':sha(label_path),'panel':sha(panel_path)},
             'requested_cases':result['requested_cases'],'attempted_cases':result['attempted_cases'],
             'validated_pairs':len(result['cases']),'failed_cases':result['failures'],
             'paired_counts':labels['paired_counts'],'root_exclusion_cases':exclusions,
             'runtime':{'total_case_wall_seconds':sum(wall),
                        'median_case_wall_seconds':statistics.median(wall),
                        'p95_case_wall_seconds':sorted(wall)[int(.95*len(wall))-1],
                        'total_search_plus_export_seconds':sum(search),
                        'other_startup_prefix_guard_teardown_seconds':sum(wall)-sum(search)},
             'decision':'No immediate-safety evidence for bulk B->4B distillation. Review posterior calibration and hard root exclusions before training this teacher.',
             'limits':['Teacher action is the raw CFR root selector; only base action passes through the actual front end.',
                       'No rollout strength or general playing-strength claim; nonfatal strategic improvements are unmeasured.',
                       'One seed and two small budgets per case; earlier models may have seen these games.',
                       'This does not establish that removing the guard improves overall strength.']}
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
