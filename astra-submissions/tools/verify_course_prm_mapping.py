"""Compare shipped local updates to Algorithm 5 in exact loss notation.

One three-action invented signal sequence; no FoW search, player, model or
strength measurement. The native learner itself is not edited.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
NAME = 'course-optimism-source-20261111'
OUT = ROOT / 'astra-submissions/analysis' / NAME
STORE = ROOT / 'data/astra-spool' / NAME
BUILD = ROOT / 'astra-submissions/experiments' / NAME
SOURCE = ROOT / 'astra-submissions/experiments/presentation-real-decision-20261111/control/src'


def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def save(p, value):
    with p.open('x') as stream: stream.write(json.dumps(value, indent=2) + '\n')
def close_vectors(actual, exact):
    assert len(actual) == len(exact)
    for a, b in zip(actual, exact): assert math.isclose(a, float(b), rel_tol=1e-12, abs_tol=1e-14), (a, b)
def simplex(v):
    total = sum(v)
    return [x / total for x in v] if total else [F(1, len(v)) for _ in v]


def main():
    sources = read(OUT / 'sources.json'); paper = read(OUT / 'paper.json')
    previous = read(ROOT / 'astra-submissions/analysis/presentation-real-decision-20261111/plan.json')
    for name in ('cfr.c', 'cfr.h'): assert sha(SOURCE / name) == previous['source_members']['src/' + name]
    for row in sources['sources']: assert sha(row['local_path']) == row['sha256']
    assert sha(paper['path']) == paper['sha256']
    (STORE / 'previous-course-map.md').write_bytes((ROOT / 'docs/course-map.md').read_bytes())
    command = ['gcc', '-std=c11', '-O2', '-I' + str(SOURCE), str(BUILD / 'probe.c'), str(SOURCE / 'cfr.c'), '-lm', '-o', str(BUILD / 'probe')]
    build = subprocess.run(command, capture_output=True, text=True, timeout=30)
    save(OUT / 'build.json', dict(command=command, code=build.returncode, stdout=build.stdout, stderr=build.stderr))
    assert build.returncode == 0
    paths = [Path(__file__), BUILD / 'probe.c', BUILD / 'probe', SOURCE / 'cfr.c', SOURCE / 'cfr.h',
             OUT / 'sources.json', OUT / 'paper.json', STORE / 'previous-course-map.md']
    paths += [Path(r['local_path']) for r in sources['sources']] + [Path(paper['path'])]
    plan = dict(at=datetime.now(timezone.utc).isoformat(), calls=1, call_timeout=5,
                utilities=[[1,0,-1],[-1,1,0],[-1,0,1]],
                antecedents='371 fixed generic CFR arithmetic, 375/384 real root updates. This checks published Algorithm5 equivalence, not a new learner or candidate.',
                dependencies={str(p): sha(p) for p in paths},
                scope='One three-action local-learner fixture with invented changing feedback. Exact rational loss-notation comparison, not convergence or playing strength. No engine edit, FoW search, Stockfish, fit, GPU, game, service, package, commit, push or deployment.')
    save(OUT / 'plan.json', plan)
    for p, h in plan['dependencies'].items(): assert sha(p) == h, p
    done = subprocess.run([str(BUILD / 'probe')], capture_output=True, text=True, timeout=plan['call_timeout'])
    for suffix, value in [('stdout', done.stdout), ('stderr', done.stderr)]:
        with (STORE / suffix).open('x') as stream: stream.write(value)
    save(OUT / 'execution.json', dict(at=datetime.now(timezone.utc).isoformat(), code=done.returncode,
         plan_sha256=sha(OUT / 'plan.json'), stdout_sha256=sha(STORE / 'stdout'), stderr_sha256=sha(STORE / 'stderr')))
    assert done.returncode == 0 and len(done.stdout) < 10000
    rows = [json.loads(s) for s in done.stdout.splitlines()]
    assert len(rows) == 4
    z, x_previous, predicted_loss = [F(0)] * 3, [F(1, 3)] * 3, [F(0)] * 3
    averaging, references = [F(0)] * 3, []
    # Direct paper notation: theta=[z+<m,x_previous>1-m]+, loss ell=-u.
    # Do not use the native stored-last vector to construct this reference.
    for t, utility in enumerate(plan['utilities'], 1):
        prediction_baseline = sum(m * x for m, x in zip(predicted_loss, x_previous))
        theta = [max(F(0), a + prediction_baseline - m) for a, m in zip(z, predicted_loss)]
        x = simplex(theta)
        loss = [F(-u) for u in utility]
        loss_baseline = sum(l * p for l, p in zip(loss, x))
        regret = [loss_baseline - l for l in loss]
        z = [max(F(0), a + r) for a, r in zip(z, regret)]
        prediction_next = simplex([max(F(0), a + loss_baseline - l) for a, l in zip(z, loss)])
        native = rows[t - 1]
        assert native['round'] == t and native['utility'] == utility
        for key, expected in [('strategy', x), ('regret', z), ('last', regret), ('next', prediction_next)]:
            close_vectors(native[key], expected)
        averaging = [a + t * p for a, p in zip(averaging, x)]
        references.append(dict(round=t, strategy=list(map(str, x)), regret=list(map(str, z)),
                               instantaneous=list(map(str, regret)), next_strategy=list(map(str, prediction_next))))
        x_previous, predicted_loss = x, loss
    expected_next = [F(0), F(12, 31), F(19, 31)]
    assert prediction_next == expected_next
    assert rows[-1]['kind'] == 'average'; close_vectors(rows[-1]['strategy'], simplex(averaging))
    assert sha(SOURCE / 'cfr.c') == previous['source_members']['src/cfr.c']
    result = dict(at=datetime.now(timezone.utc).isoformat(), status='passed', plan_sha256=sha(OUT / 'plan.json'),
        course_commit=sources['commit'], paper_algorithm=5, prediction_choice='previous counterfactual loss vector',
        native_rounds=rows[:3], exact_loss_notation=references,
        final_strategy_exact=list(map(str, expected_next)), linearly_weighted_root_average_exact=list(map(str, simplex(averaging))),
        scalar_values_compared=3*4*3+3, source_unchanged=True,
        equivalence='For m(t)=-u(t-1), the paper prediction <m(t),x(t-1)>1-m(t) equals the stored previous instantaneous regret. Updates match after sign conversion.',
        limitations=['Three invented local feedback rounds, not a convergence-rate experiment, full-tree average validation or strength result.',
                     'The published PCFR+ experiment uses quadratic sequence-form averaging; the deployed path selects the last iterate then root argmax.',
                     'Growing-tree initialization/frontier changes and information-set approximations require separate analysis.'],
        scope=plan['scope'])
    save(OUT / 'result.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'course_commit', 'scalar_values_compared', 'final_strategy_exact', 'linearly_weighted_root_average_exact')}))


if __name__ == '__main__': main()
