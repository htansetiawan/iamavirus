"""Retrospective uncertainty for the existing first300 schedule comparison.

No new data, fit, candidate selection, retention rule or claim of causality.
"""
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/v38-measurement-bounds-20261110'
SAVED=ROOT/'astra-submissions/analysis/v38-arena-20261109/20261109T204526Z'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def summarize(candidate,baseline,alpha=.05):
    assert candidate and 0<alpha<1
    c=defaultdict(list);b=defaultdict(list)
    for g in candidate:c[g['stratum']].append(g['score'])
    for g in baseline:b[g['stratum']].append(g['score'])
    assert all(0<=s<=1 for group in list(c.values())+list(b.values()) for s in group)
    rows=[];actual_matched=expected_matched=base_squared=0.;matched=0
    for key,scores in sorted(c.items()):
        if key not in b:continue
        nc,nb=len(scores),len(b[key]);expected=nc*math.fsum(b[key])/nb
        matched+=nc;actual_matched+=math.fsum(scores);expected_matched+=expected
        base_squared+=nc*nc/nb
        rows.append(dict(stratum=list(key),candidate_n=nc,baseline_n=nb,
                         candidate_points=math.fsum(scores),baseline_points=math.fsum(b[key]),expected_points=expected))
    total=len(candidate);unknown=total-matched;points=math.fsum(g['score'] for g in candidate)
    # Every unmatched historical baseline cell mean can be anywhere in[0,1].
    # These are algebraic bounds holding matched historical estimates fixed.
    proxy_range=[(points-expected_matched-unknown)/total,(points-expected_matched)/total]
    # Candidate and historical baseline game scores BOTH contribute noise.
    # For fixed schedules/weights and independent bounded outcomes, apply
    # Hoeffding to signed weighted scores. These assumptions are not certified
    # for this adaptively scheduled historical arena comparison.
    full_sq=1/total+base_squared/(total*total)
    full_radius=math.sqrt(.5*full_sq*math.log(2/alpha))
    if matched:
        difference=(actual_matched-expected_matched)/matched
        match_sq=1/matched+base_squared/(matched*matched)
        match_radius=math.sqrt(.5*match_sq*math.log(2/alpha))
        effective_base=matched*matched/base_squared
        working_match=[max(-1,difference-match_radius),min(1,difference+match_radius)]
    else:difference=match_radius=effective_base=working_match=None
    return dict(total=total,matched=matched,unmatched=unknown,coverage=matched/total,
        matched_point_difference=difference,matched_expected_points=expected_matched,
        effective_baseline_games=effective_base,rows=rows,
        full_schedule_proxy_range_unmatched=proxy_range,
        fixed_schedule_independent_working_model=dict(alpha=alpha,
            matched_radius=match_radius,matched_interval=working_match,
            full_radius=full_radius,full_envelope=[max(-1,proxy_range[0]-full_radius),min(1,proxy_range[1]+full_radius)],
            full_signed_weight_sum_squares=full_sq,
            limitation='Illustrative bound only: fixed schedules/weights and independent bounded game outcomes are assumed, not established. Adaptive scheduling, time drift and version-selection confounding prevent a certified causal confidence interval.'))


def main():
    OUT.mkdir(exist_ok=False)
    checkpoint=ROOT/'astra-submissions/tools/v38_checkpoint.py'
    old=module(checkpoint,'old_checkpoint')
    stamp=module(ROOT/'astra-submissions/experiments/cohort-integrity-20261110/audit.py','timestamp_only')
    candidate=old.load(SAVED,'games-*.json',38);baseline=old.load(SAVED,'baseline-v37-*.json',37)
    assert [g['id'] for g in candidate]==[g['id'] for g in sorted(candidate,key=lambda g:(stamp.stamp_ns(g['createdAt']),g['id']))]
    first=candidate[:300];assert len(first)==300
    result=summarize(first,baseline)
    archived=json.loads((SAVED/'checkpoint.json').read_text())['first_300_matched']
    assert result['matched']==archived['matched_games'] and result['unmatched']==archived['unmatched_games']
    assert abs(result['matched_point_difference']-archived['difference'])<1e-12
    assert abs(result['matched_expected_points']/result['matched']-archived['baseline_expected_score'])<1e-12
    result.update(at=datetime.now(timezone.utc).isoformat(),scope='Retrospective measurement extension of the unchanged Nov9 first300 checkpoint; no new promotion gate, data, model, fit, arena action or current-v38 causal estimate.',
        candidate_ids=[g['id'] for g in first],
        source_sha256={str(p):sha(p) for p in [checkpoint,HERE/'analysis.py',ROOT/'astra-submissions/experiments/cohort-integrity-20261110/audit.py',*sorted(SAVED.glob('games-*.json')),*sorted(SAVED.glob('baseline-v37-*.json')),SAVED/'checkpoint.json']},
        retention_decision_unchanged=True,future295_sources_opened=False)
    (OUT/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','source_sha256','candidate_ids')},indent=2),flush=True)


if __name__=='__main__':main()
