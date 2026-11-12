#!/usr/bin/env python3
"""Read archived source and saved history-mixture results; never run an engine."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive = ROOT / "astra-submissions/iamavirus-v38-mist-c-allchildren.zip"
    archive_hash = digest(archive.read_bytes())
    assert archive_hash == "ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f"
    with zipfile.ZipFile(archive) as z:
        members = {}
        for name in ("belief.c", "gtcfr.c"):
            matches = [p for p in z.namelist() if p.endswith("/src/" + name)]
            assert len(matches) == 1
            members[name] = z.read(matches[0])
    b = members["belief.c"].decode()
    key = b[b.index("uint64_t position_key("):b.index("uint64_t view_hash(")]
    source_checks = {
        "key_includes_side_castling_ep": all(s in key for s in ("p->side", "p->castle_rooks", "p->ep")),
        "key_omits_halfmove_and_history": "halfmove" not in key and "hist" not in key,
        "entry_key_explicitly_ignores_history": "(void)hist; return position_key(p);" in b,
        "merge_adds_weights": "total = log_add(total, cand[j].logw);" in b,
        "merge_retains_heaviest_candidate": "if (cand[j].logw > best.logw) best = cand[j];" in b,
        "history_used_for_next_likelihood": "history_counts(b->hist ? b->hist[i] : 0, &l, hc)" in b,
        "root_action_is_argmax": "if (x[o + a] > x[o + best]) best = a;" in members["gtcfr.c"].decode(),
    }
    assert all(source_checks.values())
    old = ROOT / "astra-submissions/analysis/history-mixture-20261102"
    summary_bytes = (old / "summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    old_audit = json.loads((old / "audit.json").read_text())
    assert old_audit["passed"] and old_audit["summary_sha256"] == digest(summary_bytes)
    per_game = []
    pins = {}
    decisions = merged = 0
    for saved in summary["per_game"]:
        p = old / "games" / (saved["game"] + ".json")
        blob = p.read_bytes()
        pins[str(p.relative_to(ROOT))] = digest(blob)
        case = json.loads(blob)
        assert case["returncode"] == 0 and len(case["rows"]) == saved["decisions"]
        assert digest((old / "games" / (saved["game"] + "-raw.json.gz")).read_bytes()) == case["raw_sha256"]
        per_game.append({arm: statistics.mean(-math.log(max(r["arms"][arm]["board_probability"], 1e-12))
                                             for r in case["rows"])
                         for arm in ("legacy", "representative", "mixture")})
        decisions += len(case["rows"])
        merged += sum(r["arms"]["mixture"]["stats"][1] > r["arms"]["mixture"]["stats"][0]
                      for r in case["rows"])
    means = {arm: statistics.mean(g[arm] for g in per_game) for arm in per_game[0]}
    for arm, value in means.items():
        assert math.isclose(value, summary["phases"]["all"]["metrics"][arm]["nll"], abs_tol=1e-12)
    assert decisions == summary["decisions"] == 260 and merged == summary["merged_history_decisions"] == 201
    assert len(per_game) == 24
    # Constructed arithmetic only. Incoming conditional history masses are fixed.
    masses = (Fraction(3, 5), Fraction(2, 5))
    probabilities = (Fraction(9, 10), Fraction(1, 10))
    arithmetic = {}
    for power in (1, 2):
        mixture = sum(w * p ** power for w, p in zip(masses, probabilities))
        representative = sum(masses) * probabilities[0] ** power
        arithmetic[str(power)] = {"mixture_mass": str(mixture), "representative_mass": str(representative)}
    assert arithmetic == {"1": {"mixture_mass": "29/50", "representative_mass": "9/10"},
                          "2": {"mixture_mass": "49/100", "representative_mass": "81/100"}}
    result = {
        "passed": True, "archive_sha256": archive_hash,
        "native_member_sha256": {k: digest(v) for k, v in members.items()},
        "source_text_checks": source_checks, "saved_result_sha256": digest(summary_bytes),
        "saved_case_sha256": pins, "reduced_games": len(per_game), "reduced_decisions": decisions,
        "merged_history_decisions": merged, "equal_game_nll": means,
        "mixture_gain_over_matched_control": means["representative"] - means["mixture"],
        "original_descriptive_bootstrap95": summary["phases"]["all"]["comparisons"]["representative"]["descriptive_game_bootstrap95"],
        "retained_prefix_cpu_ratio": summary["cpu_seconds_retained_prefix"]["mixture"] / summary["cpu_seconds_retained_prefix"]["representative"],
        "constructed_arithmetic": arithmetic,
        "scope": "Source-text and saved-metric review; not independent enumeration, new timing, predictions, policy or strength evidence.",
        "source_sha256": digest(Path(__file__).read_bytes()),
    }
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({k: result[k] for k in ("passed", "reduced_games", "reduced_decisions", "mixture_gain_over_matched_control")}))


if __name__ == "__main__":
    main()
