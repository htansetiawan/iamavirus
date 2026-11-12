"""Fixed statistical examples for the presentation; no engine or game runs.

Independent, draw-free Bernoulli illustrations only. Real paired games,
opponent changes, draws, optional stopping and repeated selection need a
corresponding analysis rather than a claim of these exact confidence levels.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/measurement-resolution-20261111"


def elo(score):
    if score == 0:
        return -math.inf
    if score == 1:
        return math.inf
    if not 0 < score < 1:
        raise ValueError("score must be between zero and one")
    return 400 * math.log10(score / (1 - score))


def score_at_elo(difference):
    return 1 / (1 + 10 ** (-difference / 400))


def wilson(wins, games, confidence=.95):
    if not 0 <= wins <= games or games <= 0 or not 0 < confidence < 1:
        raise ValueError("invalid binomial interval inputs")
    p = wins / games
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    denominator = 1 + z * z / games
    center = (p + z * z / (2 * games)) / denominator
    radius = z * math.sqrt(p * (1 - p) / games + z * z / (4 * games * games)) / denominator
    return center - radius, center + radius


def gate_pass_probability(wins_needed, games, p):
    return sum(math.comb(games, k) * p ** k * (1 - p) ** (games - k)
               for k in range(wins_needed, games + 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT / "result.json")
    parser.add_argument("--baseline-revision", default="f744934e4e12ef9e4018893bd037184b23efae42")
    args = parser.parse_args()
    # Independent numerical cross-check against the existing scientific library.
    from scipy.stats import binom, binomtest
    scenarios = {}
    for wins, games in ((20, 40), (9, 16)):
        lo, hi = wilson(wins, games)
        reference = binomtest(wins, games).proportion_ci(confidence_level=.95, method="wilson")
        assert max(abs(lo - reference.low), abs(hi - reference.high)) < 1e-14
        scenarios[f"{wins}_of_{games}"] = dict(wins=wins, games=games, score=wins / games,
            score_interval=[lo, hi], elo_point=elo(wins / games), elo_interval=[elo(lo), elo(hi)])
    gates = []
    for difference in (0, 15, 100, 200):
        p = score_at_elo(difference)
        passing = gate_pass_probability(10, 16, p)
        assert abs(passing - binom.sf(9, 16, p)) < 1e-14
        gates.append(dict(assumed_elo_difference=difference, true_win_probability=p,
                          ten_of_sixteen_pass_probability=passing,
                          ten_of_sixteen_fail_probability=1 - passing))
    exact_null = Fraction(sum(math.comb(16, k) for k in range(10, 17)), 2 ** 16)
    assert float(exact_null) == gates[0]["ten_of_sixteen_pass_probability"]
    assert gate_pass_probability(10, 16, 0) == 0
    assert gate_pass_probability(10, 16, 1) == 1
    old_bytes = subprocess.check_output(["git", "show", args.baseline_revision + ":docs/evaluation.md"], cwd=ROOT)
    claim = "Forty games resolve a 15-point gap at best"
    assert claim in old_bytes.decode()
    result = dict(assumptions="Independent draw-free fixed-sample Bernoulli games; standard logistic Elo mapping.",
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        corrected_claim=dict(path="docs/evaluation.md", baseline_revision=args.baseline_revision,
                             old_sha256=hashlib.sha256(old_bytes).hexdigest(), text=claim),
        wilson95=scenarios, fixed_ten_of_sixteen_gate=gates,
        null_gate_exact_fraction=str(exact_null), score_80_percent_elo=elo(.8),
        validation=dict(scipy_wilson_cases=2, scipy_binomial_tail_cases=4,
                        exact_rational_null=True, zero_one_controls=True),
        limits=["A pointwise illustrative interval, not a selection-adjusted retrospective claim for an engine.",
                "Actual paired games, draws, schedule changes and early stopping differ from these assumptions.",
                "The original16-game screens retain their predeclared outcomes; no failed candidate is reopened.",
                "No new match, fit, GPU job, ZIP/version, service or website deployment."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
