"""Check the promotion boundary and adjudication against existing game receipts."""
import copy
import itertools
import json
import math
from pathlib import Path
from run import OUT, ROOT, PILOT, OLD, calculate, imported, inspect, sha


def main():
    plan = json.loads((OUT / 'design.json').read_text())
    jobs = plan['jobs']; rows = [dict(job=j, score=1., faults=[], exit=0, opponent_fault=False) for j in jobs]
    for r in rows:
        if r['job']['panel'] == 'misty' and r['job']['arm'] == 'base': r['score'] = 0.
    assert calculate(plan, rows)['decision'] == 'release_review'
    assert calculate(plan, rows[:-1])['decision'] == 'incomplete'
    fair = copy.deepcopy(rows)
    for r in fair:
        if r['job']['panel'] != 'misty': r['score'] = int(r['job']['side'] == 'white')
    assert calculate(plan, fair)['decision'] == 'close_frozen_candidate'
    assert calculate(plan, fair)['stratified_pair_interval_95'] == [.5, .5]
    one_bad = copy.deepcopy(rows)
    failure = next(r for r in one_bad if r['job']['panel'] == 'misty' and r['job']['pair'] == 32 and r['job']['arm'] == 'base')
    failure.update(opponent_fault=True, score=1.)
    result = calculate(plan, one_bad)
    assert result['decision'] == 'release_review' and result['invalid_misty_blocks'] == [32]
    assert result['panels']['misty/base']['games'] == result['panels']['misty/candidate']['games'] == 6
    assert result['panels']['misty/base']['points'] == 0 and result['panels']['misty/candidate']['points'] == 6
    two_bad = copy.deepcopy(one_bad)
    next(r for r in two_bad if r['job']['panel'] == 'misty' and r['job']['pair'] == 33)['opponent_fault'] = True
    assert calculate(plan, two_bad)['decision'] == 'inconclusive_opponent_panel'
    candidate_fault = copy.deepcopy(rows); candidate_fault[0]['faults'] = ['candidate timeout']
    assert calculate(plan, candidate_fault)['decision'] == 'technical_failure_no_promotion'
    misty_regression = copy.deepcopy(rows)
    for r in misty_regression:
        if r['job']['panel'] == 'misty': r['score'] = float(r['job']['arm'] == 'base')
    assert calculate(plan, misty_regression)['decision'] == 'close_frozen_candidate'

    interval = imported('verify_old_interval', OLD / 'run.py').pair_interval
    for panels in ([[0, 2], [.5, 1.5]], [[0, 1, 2], [.5, 1.5]], [[1.5], [.5]]):
        totals = [0.]
        for p in panels:
            draws = [sum(x) for x in itertools.product(p, repeat=len(p))]
            totals = [a + b for a in totals for b in draws]
        scores = sorted(t / (2 * sum(map(len, panels))) for t in totals)
        expected = [scores[math.ceil(q * len(scores)) - 1] for q in (.025, .975)]
        assert interval(panels) == expected

    priorfault = ROOT / 'astra-submissions/analysis/persistent-confirmation-20261102/jobs/confirm-misty-p1-white-base'
    old_result = json.loads((priorfault / 'result.json').read_text())
    actual = inspect(old_result['job'], priorfault)
    assert actual['opponent_fault'] and not actual['faults']
    assert actual['replay_sha256'] == old_result['replay_sha256']
    candidate = PILOT / 'jobs/qexp-p0-white'
    candidate_result = json.loads((candidate / 'result.json').read_text())
    actual_candidate = inspect(candidate_result['job'], candidate)
    assert not actual_candidate['faults'] and not actual_candidate['opponent_fault']
    assert actual_candidate['score'] == candidate_result['score']
    # Each complete direct pair keeps both colours on one lane. Each Misty
    # block contains both arms and both colours with matching seeds.
    for panel in ('v35', 'base', 'misty'):
        groups = {j['pair'] for j in jobs if j['panel'] == panel}
        for p in groups:
            group = [j for j in jobs if j['panel'] == panel and j['pair'] == p]
            assert len({j['lane'] for j in group}) == 1
            assert {j['side'] for j in group} == {'white', 'black'}
            assert len({(j['engine_seed'], j['opponent_seed']) for j in group}) == 1
            assert len(group) == (4 if panel == 'misty' else 2)
    result = dict(passed=True, source_sha256=sha(Path(__file__)), runner_sha256=sha(Path(__file__).with_name('run.py')),
                  gate_fixtures=7, independent_bootstrap_cases=3, actual_replay_fixtures=2,
                  real_misty_fault_replay_sha256=actual['replay_sha256'], actual_candidate_replay_sha256=actual_candidate['replay_sha256'],
                  complete_colour_and_control_blocks=True, scope='Harness and gate correctness, not new playing-strength evidence.')
    with (OUT / 'verification.json').open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
