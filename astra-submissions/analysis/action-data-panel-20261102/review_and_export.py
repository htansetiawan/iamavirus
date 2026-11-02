"""Audit all frozen branches and export only the predeclared observable input.

Labels and provenance are deliberately separate from learner inputs. Unknown
terminal outcomes remain null with bounds; repeated trajectories are grouped.
"""
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SOURCE = ROOT / 'astra-submissions/experiments/action-data-panel-20261102'
sys.path.insert(0, str(SOURCE))
import run as experiment
from input_contract import actor_history, critic_input, digest, VERSION


def write(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def jsonlines(name, rows):
    with (OUT / name).open('x') as f:
        for row in rows:
            f.write(json.dumps(row, separators=(',', ':')) + '\n')


def main():
    plan, frozen = experiment.pilot.branches()
    summary = json.loads((OUT / 'branches-summary.json').read_text())
    assert summary['complete']
    expected = {j['id'] for j in frozen['jobs']}
    assert len(expected) == len(frozen['jobs'])
    assert {a['job']['id'] for a in summary['attempts']} == expected
    for attempt in summary['attempts']:
        assert attempt['passed'] and attempt['exit'] == 0
        assert not attempt['timeout'] and not attempt['unverified_groups']
    reviewed, targets, inputs, pairs = [], [], {}, defaultdict(dict)
    per_action = defaultdict(list)
    groups = {}
    checks = frames = decisions = 0
    wall = 0.0
    for job in frozen['jobs']:
        d = OUT / job['id']
        case = plan['cases'][job['case']]
        prefix = json.loads((ROOT / case['prefix']).read_text())
        receipt = json.loads((d / 'result.json').read_text())
        process = json.loads((d / 'process-result.json').read_text())
        assert process['passed'] and process['exit'] == 0
        assert experiment.base.sha(d / 'replay.json') == receipt['replay_sha256']
        assert receipt['job'] == job
        game = json.loads((d / 'replay.json').read_text())
        actual = experiment.inspect(game, prefix, job['action'], job['common_charge'])
        assert all(receipt[k] == v for k, v in actual.items())
        frames += actual['frames']
        decisions += actual['new_plies'] - 1  # externally forced root is not searched
        wall += actual['wall_seconds']
        side = case['side']
        proposal = json.loads((OUT / f'proposal-{job["case"]}' / 'proposal.json').read_text())
        assert job['action'] == proposal['chosen' if job['arm'] == 0 else 'alternative']
        assert job['common_charge'] == proposal['common_charge']
        observed = critic_input(prefix, job['action'], proposal)
        input_hash = digest(observed)
        assert proposal['input_sha256'][job['action']] == input_hash
        from_replay = experiment.base.prefix(game, case['branch_ply'])
        assert critic_input(from_replay, job['action'], proposal) == observed
        # Check the prefix really was delivered to the actor in this branch.
        events = [e for e in game['protocol']['events'] if e['direction'] == 'input'
                  and e['side'] == observed['actor']['side'] and e['ply'] <= case['branch_ply']]
        assert [e['text'] for e in events if len(e['text']) == 64] == observed['actor']['observations']
        changed = copy.deepcopy(game)
        other = ('black', 'white')[side]
        for i, f in enumerate(changed['frames']):
            f['board'] = 'X' * 64
            f[other] = 'X' * 64
            f['clocks'][1-side] = -999
            if i and (i-1) % 2 != side:
                f['move'] = 'zzzz'
            if i > case['branch_ply']:
                f[observed['actor']['side']] = 'X' * 64
                f['move'] = 'zzzz'
        changed.update(result='ignored', privateDiagnostics={}, protocol={})
        changed_prefix = experiment.base.prefix(changed, case['branch_ply'])
        assert critic_input(changed_prefix, job['action'], proposal) == observed
        checks += 1
        changed_prefix.update(id='ignored', result='ignored', seed='ignored')
        assert critic_input(changed_prefix, job['action'], proposal) == observed
        checks += 1
        assert inputs.setdefault(input_hash, observed) == observed
        source = case['game']
        group = dict(trajectory=case['source_trajectory_sha256'],
                     observable_history_without_clocks=case['observable_history_without_clocks_sha256'])
        assert groups.setdefault(source, group) == group
        expected_return = None if game['censored'] else (0 if game['result'] == '1/2-1/2'
                          else (1 if (game['result'] == '1-0') == (side == 0) else -1))
        assert expected_return == receipt['actor_return']
        target = dict(id=job['id'], source_group=source, phase=case['phase'], side=side,
                      input_sha256=input_hash, action=job['action'], arm=job['arm'],
                      repeat=job['repeat'], seed=job['seed'], terminal_return=expected_return,
                      censored=game['censored'], new_plies=actual['new_plies'],
                      terminal_return_interval=[-1, 1] if expected_return is None else [expected_return]*2,
                      root_post_clocks=actual['root_post_clocks'], common_charge=job['common_charge'],
                      wall_seconds=actual['wall_seconds'], replay_sha256=receipt['replay_sha256'])
        targets.append(target)
        assert job['arm'] not in pairs[(source, job['repeat'])]
        pairs[(source, job['repeat'])][job['arm']] = target
        per_action[(source, job['arm'])].append(target)
        reviewed.append(receipt)
    paired = []
    for (source, repeat), arms in sorted(pairs.items()):
        assert set(arms) == {0, 1}
        a, b = arms[0], arms[1]
        assert a['seed'] == b['seed'] and a['root_post_clocks'] == b['root_post_clocks']
        assert a['common_charge'] == b['common_charge']
        lo_a, hi_a = a['terminal_return_interval']
        lo_b, hi_b = b['terminal_return_interval']
        complete = not a['censored'] and not b['censored']
        paired.append(dict(source_group=source, repeat=repeat, baseline=a['id'], alternative=b['id'],
                           complete=complete,
                           return_difference=b['terminal_return']-a['terminal_return'] if complete else None,
                           return_difference_interval=[lo_b-hi_a, hi_b-lo_a]))
    replicate_rows = []
    for (source, arm), rows in sorted(per_action.items()):
        assert len(rows) == 2 and {r['repeat'] for r in rows} == {0, 1}
        values = [r['terminal_return'] for r in sorted(rows, key=lambda r: r['repeat'])]
        replicate_rows.append(dict(source_group=source, arm=arm, values=values,
                                   disagree=None if None in values else values[0] != values[1]))
    strata = defaultdict(Counter)
    for r in targets:
        for key in (f'phase={r["phase"]}', f'arm={r["arm"]}', f'side={r["side"]}'):
            strata[key]['branches'] += 1
            strata[key]['censored'] += int(r['censored'])
    review = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, rows=reviewed,
                  frames=frames, privacy_checks=checks,
                  summary_sha256=experiment.base.sha(OUT/'branches-summary.json'),
                  source_sha256=experiment.base.sha(__file__))
    write('review.json', review)
    jsonlines('critic-inputs.jsonl', [dict(sha256=h, input=v) for h, v in sorted(inputs.items())])
    jsonlines('root-targets.jsonl', targets)
    jsonlines('paired-targets.jsonl', paired)
    write('seed-variability.json', replicate_rows)
    manifest = dict(at=review['at'], schema=VERSION, source_groups=groups,
                    root_rows=len(targets), distinct_inputs=len(inputs), paired_rows=len(paired),
                    terminal_root_labels=sum(not r['censored'] for r in targets),
                    complete_pairs=sum(r['complete'] for r in paired), privacy_checks=checks,
                    censoring_by_stratum=dict(strata),
                    observed_pair_differences=dict(Counter(str(r['return_difference']) for r in paired)),
                    fully_observed_replicate_pairs=sum(r['disagree'] is not None for r in replicate_rows),
                    disagreeing_replicate_pairs=sum(r['disagree'] is True for r in replicate_rows),
                    cost=dict(batch_seconds=summary['seconds'], summed_branch_seconds=wall,
                              searched_continuation_decisions=decisions,
                              seconds_per_searched_decision=wall/decisions if decisions else None,
                              median_branch_seconds=statistics.median(r['wall_seconds'] for r in targets)),
                    artifacts={n:experiment.base.sha(OUT/n) for n in ('review.json','critic-inputs.jsonl',
                               'root-targets.jsonl','paired-targets.jsonl','seed-variability.json')},
                    split='All arms/seeds of a source trajectory stay together; also group shared observable histories before fitting.',
                    target='Root action return under reconstructed v37/v37 continuation and fixed clock policy. Not a CFR leaf value or Nash value.',
                    censoring='Null outcomes have loss-to-win bounds, not confidence intervals. Complete-case fitting can be biased by action-dependent censoring.',
                    scope='Sixteen selected development sources at most; no model fit, policy selection, significance or strength claim.')
    write('dataset.json', manifest)
    print(json.dumps({k:manifest[k] for k in ('root_rows','distinct_inputs','paired_rows',
                                            'terminal_root_labels','complete_pairs','privacy_checks','cost')}))


if __name__ == '__main__':
    main()
