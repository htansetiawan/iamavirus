"""Small, exact game oracles for reviewing a native imperfect-information solver.

No CFR implementation, chess engine, GPU, or third-party dependency. Export the
trees for the native solver, then validate its policy JSON by exact enumeration
of information-set-constrained best responses. These deliberately tiny games
are correctness checks, not a strength benchmark or a full PCFR+/KLUSS test.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path


def terminal(value):
    return {"type": "terminal", "utility0": value}


def decision(player, info, actions, **metadata):
    return {"type": "decision", "player": player, "infoset": info,
            "actions": actions, **metadata}


def coin_game(name, heads=0.5, revealed=False, memory=False, scout=False):
    children, policy = [], {}
    for truth, probability in [("H", heads), ("T", 1-heads)]:
        info = f"remember:{truth}" if memory else f"seen:{truth}" if revealed else "guess"
        node = decision(0, info,
            {guess: terminal(1 if guess == truth else -1) for guess in ("H", "T")},
            current_observation="fog" if memory or not revealed else truth,
            observation_history=[truth, "fog"] if memory else [truth] if revealed else ["fog"])
        if scout:
            node["actions"]["scout"] = decision(0, f"scouted:{truth}",
                {guess: terminal((1 if guess == truth else -1)-0.1) for guess in ("H", "T")})
            policy[f"scouted:{truth}"] = {"H": float(truth == "H"), "T": float(truth == "T")}
            policy[info] = {"H": 0.0, "T": 0.0, "scout": 1.0}
        else:
            choose = truth if memory or revealed else "H"
            policy[info] = {"H": float(choose == "H"), "T": float(choose == "T")}
        children.append({"probability": probability, "child": node})
    return {"name": name, "root": {"type": "chance", "outcomes": children},
            "expected_value": 0.9 if scout else 1.0 if memory or revealed else abs(2*heads-1),
            "reference_policy": policy}


def fixtures():
    games = [coin_game("hidden_coin"), coin_game("biased_chance", heads=0.8),
             coin_game("revealed_coin", revealed=True),
             coin_game("remembered_signal", memory=True),
             coin_game("valuable_scout", scout=True)]
    games.append({"name": "hidden_matching_pennies", "expected_value": 0.0,
        "root": decision(0, "p0", {first: decision(1, "p1_uninformed",
            {reply: terminal(1 if first == reply else -1) for reply in ("H", "T")})
            for first in ("H", "T")}),
        "reference_policy": {"p0": {"H": 0.5, "T": 0.5},
                             "p1_uninformed": {"H": 0.5, "T": 0.5}}})
    kernels = {
        "counterfactual_reach": {
            "own_reach": 0.0, "chance_reach": [0.25, 0.75],
            "opponent_reach": [0.2, 0.6], "strategy": [0.5, 0.5],
            "action_values": [[1.0, -1.0], [0.0, 2.0]],
            "expected_regret_increment": [-0.4, 0.4]},
        "aggregate_then_clip_rm_plus": {
            "old_regret": [0.0, 0.0],
            "history_regret_contributions": [[-2.0, 2.0], [1.0, -1.0]],
            "expected_regret": [0.0, 1.0]},
        "predictive_rm_plus": {
            "source": "Farina/Kroer/Sandholm AAAI2021 Algorithm5; utility convention (negative loss)",
            "old_z": [1.0, 2.0], "previous_strategy": [0.5, 0.5],
            "predicted_utility": [2.0, 0.0], "realized_utility": [-1.0, 3.0],
            "expected_theta": [2.0, 1.0], "expected_strategy": [2/3, 1/3],
            "expected_new_z": [0.0, 14/3]},
        "sequence_average": {
            "own_reach": [0.0, 0.25, 0.75], "iteration_weight": [1.0, 2.0, 3.0],
            "strategies": [[0.9, 0.1], [0.8, 0.2], [0.2, 0.8]],
            "expected_average": [0.85/2.75, 1.9/2.75]}}
    return {"schema_version": 1, "payoff_perspective": "player0; player1 is the negative",
            "scope": "Tiny fixed-tree and arithmetic oracles; not a production solver or full algorithm certification.",
            "games": games, "kernels": kernels}


def information_sets(node, result=None):
    result = {} if result is None else result
    if node["type"] == "decision":
        entry = (node["player"], tuple(node["actions"]))
        previous = result.setdefault(node["infoset"], entry)
        if previous != entry:
            raise ValueError("One infoset must have one actor and one ordered action set")
        for child in node["actions"].values():
            information_sets(child, result)
    elif node["type"] == "chance":
        if not math.isclose(sum(x["probability"] for x in node["outcomes"]), 1):
            raise ValueError("Chance probabilities must sum to one")
        for outcome in node["outcomes"]:
            information_sets(outcome["child"], result)
    return result


def validate_policy(root, policy):
    infos = information_sets(root)
    if set(policy) != set(infos):
        raise ValueError("Policy keys must match infosets, not individual hidden-world nodes")
    for info, (_, actions) in infos.items():
        row = policy[info]
        if set(row) != set(actions):
            raise ValueError(f"Action mismatch at {info}")
        if any(not math.isfinite(v) or v < 0 for v in row.values()):
            raise ValueError(f"Invalid probability at {info}")
        if not math.isclose(sum(row.values()), 1, abs_tol=1e-9):
            raise ValueError(f"Probabilities do not sum to one at {info}")


def value(node, policy, pure=None):
    pure = {} if pure is None else pure
    if node["type"] == "terminal":
        return node["utility0"]
    if node["type"] == "chance":
        return sum(o["probability"] * value(o["child"], policy, pure) for o in node["outcomes"])
    info = node["infoset"]
    if info in pure:
        return value(node["actions"][pure[info]], policy, pure)
    return sum(policy[info][a] * value(child, policy, pure) for a, child in node["actions"].items())


def measure(game, policy):
    root = game["root"]
    validate_policy(root, policy)
    infos = information_sets(root)
    bounds = []
    for player in (0, 1):
        own = [(key, actions) for key, (actor, actions) in infos.items() if actor == player]
        responses = (dict(zip([key for key, _ in own], choices))
                     for choices in product(*(actions for _, actions in own)))
        scores = [value(root, policy, response) for response in responses]
        bounds.append((max if player == 0 else min)(scores))
    return {"value": value(root, policy), "best_response0": bounds[0],
            "best_response1_in_player0_units": bounds[1], "nash_gap": bounds[0]-bounds[1]}


def self_check(suite):
    reports = {}
    for game in suite["games"]:
        report = measure(game, game["reference_policy"])
        assert math.isclose(report["value"], game["expected_value"], abs_tol=1e-12)
        assert abs(report["nash_gap"]) < 1e-12
        reports[game["name"]] = report
    k = suite["kernels"]["counterfactual_reach"]
    values = [sum(c*o*v[a] for c, o, v in zip(k["chance_reach"], k["opponent_reach"], k["action_values"]))
              for a in range(2)]
    baseline = sum(p*v for p, v in zip(k["strategy"], values))
    assert all(math.isclose(v-baseline, e) for v, e in zip(values, k["expected_regret_increment"]))
    k = suite["kernels"]["aggregate_then_clip_rm_plus"]
    assert [max(0, old+sum(row[a] for row in k["history_regret_contributions"]))
            for a, old in enumerate(k["old_regret"])] == k["expected_regret"]
    k = suite["kernels"]["predictive_rm_plus"]
    predicted_baseline = sum(p*u for p, u in zip(k["previous_strategy"], k["predicted_utility"]))
    theta = [max(0, z+u-predicted_baseline) for z, u in zip(k["old_z"], k["predicted_utility"])]
    strategy = [v/sum(theta) for v in theta]
    actual_baseline = sum(p*u for p, u in zip(strategy, k["realized_utility"]))
    new_z = [max(0, z+u-actual_baseline) for z, u in zip(k["old_z"], k["realized_utility"])]
    for actual, expected in [(theta, k["expected_theta"]), (strategy, k["expected_strategy"]),
                             (new_z, k["expected_new_z"])]:
        assert all(math.isclose(v, e) for v, e in zip(actual, expected))
    k = suite["kernels"]["sequence_average"]
    weights = [r*t for r, t in zip(k["own_reach"], k["iteration_weight"])]
    got = [sum(w*s[a] for w, s in zip(weights, k["strategies"]))/sum(weights) for a in range(2)]
    assert all(math.isclose(v, e) for v, e in zip(got, k["expected_average"]))
    # Regressions this oracle must reject: forgetting a remembered signal;
    # a pure matching-pennies profile with value zero but large exploitability.
    remembered = suite["games"][3]
    forgotten = {key: {"H": 0.5, "T": 0.5} for key in remembered["reference_policy"]}
    assert math.isclose(measure(remembered, forgotten)["nash_gap"], 1)
    pennies = suite["games"][-1]
    one_pure = deepcopy(pennies["reference_policy"])
    one_pure["p1_uninformed"] = {"H": 1.0, "T": 0.0}
    assert math.isclose(measure(pennies, one_pure)["value"], 0)
    assert math.isclose(measure(pennies, one_pure)["nash_gap"], 1)
    return {"games": reports, "numeric_kernel_fixtures_checked": 4,
            "negative_controls_checked": 2, "native_solver_tested": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", type=Path)
    ap.add_argument("--policies", type=Path, help="JSON mapping game name to {infoset: {action: probability}}")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--tolerance", type=float, default=0.02)
    args = ap.parse_args()
    if not math.isfinite(args.tolerance) or args.tolerance < 0:
        ap.error("tolerance must be finite and nonnegative")
    suite = fixtures()
    report = self_check(suite)
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(json.dumps(suite, indent=2) + "\n")
    passed = True
    if args.policies:
        policies = json.loads(args.policies.read_text())
        report = {"games": {}, "scope": "Submitted policies on fixed toy trees only; numeric kernels not exercised"}
        for game in suite["games"]:
            try:
                metrics = measure(game, policies[game["name"]])
                ok = (metrics["nash_gap"] <= args.tolerance and
                      abs(metrics["value"]-game["expected_value"]) <= args.tolerance)
                report["games"][game["name"]] = {**metrics, "pass": ok}
            except (KeyError, ValueError, TypeError) as exc:
                ok = False
                report["games"][game["name"]] = {"pass": False, "error": str(exc)}
            passed &= ok
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
