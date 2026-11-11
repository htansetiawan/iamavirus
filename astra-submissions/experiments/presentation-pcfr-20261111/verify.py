"""Numerical teaching example; no FoW bot, match or strategy candidate."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/presentation-pcfr-20261111'
BUILD = HERE / 'build'
ARCHIVE = ROOT / 'astra-submissions/iamavirus-v38-mist-c-allchildren.zip'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


P = [F(3, 4), F(1, 4)]
M = [[[F('0.6'), F('-0.2')], [F('-0.4'), F('0.4')]],
     [[F('-1'), F('0.6')], [F('0.6'), F('-0.2')]]]


def column_value(world, column, x):
    return x * M[world][0][column] + (1 - x) * M[world][1][column]


def worst_value(x):
    return sum(P[w] * min(column_value(w, b, x) for b in range(2)) for w in range(2))


def intersection(world):
    x0, y0 = M[world][1]
    xs = M[world][0][0] - x0
    ys = M[world][0][1] - y0
    return (y0 - x0) / (xs - ys)


def independent_values(strategy):
    x = strategy[0]
    action_values = [sum(float(P[w]) * sum(strategy[2 + 2 * w + b] * float(M[w][a][b]) for b in range(2)) for w in range(2)) for a in range(2)]
    value = x * action_values[0] + (1 - x) * action_values[1]
    lower = float(worst_value(x))
    return dict(value=value, best_response_gain_sum=max(action_values) - lower,
                worst_case_value=lower, action_values=action_values)


def main():
    assert sha(ARCHIVE) == 'ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f'
    inventory = json.loads((ROOT / 'astra-submissions/analysis/presentation-audit-20261111/inventory.json').read_text())
    BUILD.mkdir(exist_ok=False)
    with zipfile.ZipFile(ARCHIVE) as archive:
        for member in ('src/cfr.c', 'src/cfr.h'):
            data = archive.read(member)
            assert hashlib.sha256(data).hexdigest() == inventory['source_sha256'][member]
            (BUILD / Path(member).name).write_bytes(data)
    command = ['cc', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-error=maybe-uninitialized', '-I', str(BUILD),
               str(HERE / 'demo.c'), str(BUILD / 'cfr.c'), '-lm', '-o', str(BUILD / 'demo')]
    compilation = subprocess.run(command, capture_output=True, text=True, timeout=15)
    (BUILD / 'compile.stdout').write_text(compilation.stdout)
    (BUILD / 'compile.stderr').write_text(compilation.stderr)
    compilation.check_returncode()
    execution = subprocess.run([str(BUILD / 'demo')], check=True, capture_output=True, text=True, timeout=5)
    traces = [json.loads(line) for line in execution.stdout.splitlines()]
    assert [row['iteration'] for row in traces] == [0, 1, 2, 3, 4, 5, 10, 100, 1000, 10000]
    assert all(row['nodes'] == 15 and row['infosets'] == 3 for row in traces)
    for row in traces:
        for offset in (0, 2, 4):
            assert math.isclose(sum(row['current'][offset:offset + 2]), 1., abs_tol=1e-12)
            assert all(0 <= x <= 1 for x in row['current'][offset:offset + 2])
        values = independent_values(row['current'])
        assert math.isclose(values['value'], row['value'], abs_tol=1e-12)
        assert math.isclose(values['best_response_gain_sum'], row['solver_exploitability'], abs_tol=1e-12)
        row['independent'] = values
    first = traces[1]
    for actual, expected in [(first['regret'], [.025, 0., 0., .3, .2, 0.]),
                             (first['last_instantaneous_regret'], [.025, -.025, -.3, .3, .2, -.2]),
                             (first['current'], [1., 0., 0., 1., 1., 0.])]:
        assert all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(actual, expected, strict=True))
    candidates = sorted({F(0), F(1), intersection(0), intersection(1)})
    maximum = max(worst_value(x) for x in candidates)
    maximizers = [x for x in candidates if worst_value(x) == maximum]
    assert maximizers == [F(1, 2)] and maximum == F(1, 40)
    equilibrium = [0.5, 0.5, 17 / 24, 7 / 24, 1., 0.]
    assert abs(independent_values(equilibrium)['best_response_gain_sum']) < 1e-12
    fusion = sum(P[w] * min(column_value(w, b, intersection(w)) for b in range(2)) for w in range(2))
    assert fusion == F(11, 120)
    final = traces[-1]
    selected = 0 if final['current'][0] >= final['current'][1] else 1
    OUT.mkdir(exist_ok=False)
    (BUILD / 'trace.jsonl').write_text(execution.stdout)
    save(OUT / 'trace.json', traces)
    result = dict(at=datetime.now(timezone.utc).isoformat(), fixture='Invented two-world hidden-action zero-sum game, not a chess position.',
                  chance_probabilities=[str(x) for x in P], utility_matrices=[[[str(x) for x in a] for a in w] for w in M],
                  exact_shared_information_set_solution=dict(probability_A='1/2', value='1/40', opponent_X_W0='17/24', opponent_X_W1='1'),
                  exact_pure_action_worst_values=dict(A=str(worst_value(F(1))), B=str(worst_value(F(0)))),
                  information_leaking_worldwise_relaxation_value=str(fusion),
                  first_iteration_checked_against_hand_arithmetic=True,
                  first_iteration_regret=first['regret'], first_iteration_last=first['last_instantaneous_regret'],
                  final_iteration=final['iteration'], final_current=final['current'], final_value=final['value'],
                  final_toy_best_response_gain_sum=final['independent']['best_response_gain_sum'],
                  purified_final_action='A' if selected == 0 else 'B', purified_toy_worst_value=float(worst_value(F(1) if selected == 0 else F(0))),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in [ARCHIVE, HERE / 'demo.c', Path(__file__), BUILD / 'cfr.c', BUILD / 'cfr.h', BUILD / 'demo']},
                  compile_command=command, trace_sha256=sha(OUT / 'trace.json'),
                  compiler_diagnostics_sha256=sha(BUILD / 'compile.stderr'),
                  preparation_note='Initial -Werror build stopped on the unchanged shipped source maybe-uninitialized warning; original preparation preserved. No numerical result preceded this correction.',
                  limitations=['Fixed toy utilities and perfect-recall information sets; no FoW state, learned model, guards, tree growth or world resampling.',
                               'Only the unchanged generic CFR solver is exercised; this does not validate the deployed FoW subgame construction.',
                               'Toy best-response gaps are not full-game FoW exploitability or Elo estimates.',
                               'The deployed argmax depends on stochastic sampled worlds; the toy purification comparison does not quantify an arena penalty.',
                               'Existing failed mixing experiments remain closed; this is presentation material, not a successor design.'],
                  scope='Source-checked numerical teaching fixture. No bot match, training, candidate, source-package change, commit, push or deployment.')
    save(OUT / 'result.json', result)
    print(json.dumps({k: result[k] for k in ['exact_shared_information_set_solution', 'final_current', 'final_value', 'final_toy_best_response_gain_sum', 'purified_final_action', 'purified_toy_worst_value']}, indent=2))


if __name__ == '__main__':
    main()
