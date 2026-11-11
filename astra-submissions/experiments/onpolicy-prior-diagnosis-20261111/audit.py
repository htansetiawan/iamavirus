"""Post-run independent reduction of 360 and terminal replay audit of 357.

This audits existing immutable attempts. It launches no bot or prediction job,
changes no acceptance condition, and treats the six-game diagnosis as descriptive.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
DIAG = ROOT / 'astra-submissions/analysis/onpolicy-prior-diagnosis-20261111'
PLAY = ROOT / 'astra-submissions/analysis/compact-mass-playing-20261111'
STORE = ROOT / 'data/astra-spool/onpolicy-prior-diagnosis-20261111'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def check_dependencies(plan):
    for path, expected in plan['dependencies'].items():
        assert sha(path) == expected, path
    return len(plan['dependencies'])


def diagnosis():
    plan, result = read(STORE / 'plan.json'), read(DIAG / 'result.json')
    execution, calls = read(DIAG / 'execution.json'), read(STORE / 'calls.json')
    assert execution['status'] == 'complete' and execution['completed'] == 12
    assert sha(STORE / 'plan.json') == result['plan_sha256'] == execution['plan_sha256']
    assert sha(DIAG / 'result.json') == execution['result_sha256']
    assert sha(STORE / 'calls.json') == result['calls_sha256']
    assert [(c['game'], c['arm']) for c in calls] == [(j['game'], j['arm']) for j in plan['jobs']]
    cells = {}
    for call in calls:
        prefix = STORE / (call['game'] + '-' + call['arm'])
        stdout, stderr = Path(str(prefix) + '.stdout'), Path(str(prefix) + '.stderr')
        assert call['code'] == 0
        assert sha(stdout) == call['stdout_sha256'] and sha(stderr) == call['stderr_sha256']
        cells[call['game'], call['arm']] = [json.loads(line) for line in stdout.read_text().splitlines()]
    total_gain = 0.0
    primary_count = matched_counts = rows_checked = 0
    support = Counter()
    final_losses = []
    for game, recorded in zip(plan['games'], result['records'], strict=True):
        assert game['game'] == recorded['game'] and game['score'] == recorded['score']
        old, new = (cells[game['game'], arm] for arm in ('native', 'learned'))
        assert len(old) == len(new) == game['rows']
        gains, supported = [], Counter()
        for a, b in zip(old, new, strict=True):
            rows_checked += 1
            assert all(a[k] == b[k] for k in ('ply', 'decision', 'guard_applicable', 'king_label', 'queen_label'))
            for row in (a, b):
                assert 0 <= row['truth_share'] <= 1.000000001
                assert (row['matches'] > 0) == (row['truth_share'] > 0)
            if b['decision']:
                live = game['live_counts'][str(b['ply'])]
                assert live['worlds'] == b['worlds'] and live['capped'] == b['ever_capped']
                matched_counts += 1
            if a['decision'] and a['ply'] >= 16:
                gains.append(math.log(max(b['truth_share'], 1e-12) / max(a['truth_share'], 1e-12)))
                supported['native'] += a['matches'] > 0
                supported['learned'] += b['matches'] > 0
        assert len(gains) == recorded['decisions']
        assert math.isclose(math.fsum(gains) / len(gains), recorded['mean_log_truth_gain'], abs_tol=1e-12)
        assert dict(supported) == recorded['support'] and not recorded['learned_live_count_mismatches']
        for arm, rows in [('native', old), ('learned', new)]:
            last = next(row for row in reversed(rows) if row['decision'])
            assert last == recorded['final_decision'][arm]
        if not game['score']:
            a, b = (recorded['final_decision'][arm] for arm in ('native', 'learned'))
            assert a['king_label'] == b['king_label'] == 1
            final_losses.append(dict(game=game['game'], worlds=b['worlds'], truth_present=b['matches'] > 0,
                                     old_king_risk=a['kingt'], learned_king_risk=b['kingt'],
                                     learned_truth_share=b['truth_share']))
        total_gain += math.fsum(gains)
        primary_count += len(gains)
        support.update(supported)
    return dict(at=datetime.now(timezone.utc).isoformat(), dependency_hashes_verified=check_dependencies(plan),
                result_sha256=sha(DIAG / 'result.json'), calls=len(calls), rows=rows_checked,
                games=len(plan['games']), primary_decisions=primary_count, support=dict(support),
                pooled_log_truth_gain=total_gain / primary_count,
                equal_game_mean_log_truth_gain=math.fsum(r['mean_log_truth_gain'] for r in result['records']) / len(result['records']),
                positive_gain_games=sum(r['mean_log_truth_gain'] > 0 for r in result['records']),
                positive_gain_losing_games=sum(r['score'] == 0 and r['mean_log_truth_gain'] > 0 for r in result['records']),
                live_population_counts_matched=matched_counts, terminal_losses=final_losses,
                scope='Independent reduction, hashes and live count agreement on all six frozen paths. '
                      'Counts do not certify live weight fingerprints. No strength estimate or policy counterfactual.')


def playing():
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
    from learning import ingest, _native
    tactics = module('astra_postrun_tactics', ROOT / 'astra-submissions/tools/audit_top6_tactics.py')
    referee = tactics.load_referee(ROOT.parent / 'fow-starter/referee.py')
    clocks = module('astra_postrun_clocks', ROOT / 'astra-submissions/experiments/deferred-prior-playing-20261111/clock_audit.py')
    plan, result, execution = read(PLAY / 'plan.json'), read(PLAY / 'result.json'), read(PLAY / 'execution.json')
    assert result['status'] == execution['status'] == 'closed_futility' and not result['gate_pass']
    assert not execution['active'] and not execution['cleanup_unverified']
    assert sha(PLAY / 'plan.json') == result['plan_sha256']
    assert sha(PLAY / 'execution.json') == result['execution_sha256']
    assert _native._library is None
    validator = ROOT / 'astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so'
    _native.ensure_built = lambda verbose=True: validator
    rows, frames, counters = [], 0, Counter()
    for job in plan['jobs']:
        directory = Path(plan['store']) / 'jobs' / job['id']
        if not (directory / 'result.json').exists():
            assert job['id'] in result['unstarted'] and not (directory / 'started.json').exists()
            continue
        receipt, path = read(directory / 'result.json'), directory / 'replay.json'
        assert receipt['job'] == job and not receipt['faults'] and receipt['exit_code'] == 0
        assert sha(path) == receipt['replay_sha256']
        replay = read(path)
        states, errors = ingest.validate_replay(replay)
        assert not errors and len(states) == receipt['validated_frames'] == receipt['plies'] + 1
        assert tuple(states[-1].outcome()) == (receipt['result'], receipt['reason'])
        frames += len(states)
        team = replay[job['side']]
        row = tactics.audit(replay, team, referee)
        assert row['score'] == receipt['score']
        row['job'] = job['id']
        for seat, text in replay['privateDiagnostics'].items():
            who = 'candidate' if seat == job['side'] else 'reference'
            counters[who + '_rebuilds'] += text.count('belief empty, rebuilt')
            counters[who + '_clock_thins'] += text.count('P thinned from')
        rows.append(row)
    scores = [r['score'] for r in rows]
    assert (len(rows), scores.count(1), scores.count(.5), scores.count(0), frames) == (9, 1, 0, 8, 901)
    assert result['native_frames_verified'] == frames
    assert sum(scores) + result['planned'] - len(rows) < plan['gate']['points']
    return dict(at=datetime.now(timezone.utc).isoformat(), dependency_hashes_verified=check_dependencies(plan),
                result_sha256=sha(PLAY / 'result.json'), validator_sha256=sha(validator),
                frames=frames, games=len(rows), counters=dict(counters),
                terminal_kinds=dict(Counter(r['terminal']['kind'] for r in rows if r['terminal'])),
                losses_with_true_safe_alternative=sum(bool(r['terminal']['safe_moves']) for r in rows if r['terminal']),
                rows=rows, clock_audit=clocks.summarize(PLAY),
                scope='All nine immutable actual games. Independent C++ rules, course tactical walk, hashes, clocks and final futility. '
                      'Selected small development match, no arena Elo inference. Tactical true safe moves are oracle diagnostics.')


if __name__ == '__main__':
    diag = diagnosis()
    save(DIAG / 'independent-audit.json', diag)
    print(json.dumps({k: v for k, v in diag.items() if k != 'terminal_losses'}), flush=True)
    play = playing()
    save(PLAY / 'independent-audit.json', play)
    print(json.dumps({k: v for k, v in play.items() if k not in ('rows', 'clock_audit')}), flush=True)
