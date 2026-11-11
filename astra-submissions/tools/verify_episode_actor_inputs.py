"""Reconcile the completed actor audit's receipts with frozen source lengths.

This is a receipt/count review, not a second feature reconstruction.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "astra-submissions/analysis/episode-actor-inputs-20261111"
PRIVATE = ROOT / "data/astra-spool/episode-actor-inputs-20261111"
COHORT = ROOT / "data/astra-spool/daily-own-cohort-20261111"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    plan, result, execution = (read(OUT / name) for name in ("plan.json", "result.json", "execution.json"))
    assert result["status"] == execution["status"] == "complete"
    assert result["plan_sha256"] == execution["plan_sha256"] == sha(OUT / "plan.json")
    assert execution["result_sha256"] == sha(OUT / "result.json")
    assert execution["seconds"] <= plan["wall_cap_seconds"]
    for path, digest in plan["source_sha256"].items():
        assert sha(Path(path)) == digest
    assert sha(PRIVATE / "episode-receipts.json") == result["receipt_sha256"]
    rows = read(PRIVATE / "episode-receipts.json")
    by_key = {(r["game"], r["side"]): r for r in rows}
    assert len(rows) == len(by_key) == 2 * len(plan["games"]) == 60
    assert set(by_key) == {(g, side) for g in plan["games"] for side in (0, 1)}
    expected = Counter()
    for game in plan["games"]:
        frames = read(COHORT / "games" / game / "replay.json")["frames"]
        events = len(frames) - 1
        for side in (0, 1):
            row = by_key[game, side]
            decisions = len(range(side, events, 2))
            assert row["events"] == events and row["decisions"] == decisions
            assert row["checked_square_events"] == 64 * events
            assert all(row[key] is True for key in ("label_intervention_passed", "future_truncation_passed", "current_action_timing_control_passed"))
            assert len(row["feature_sha256"]) == 64 and int(row["feature_sha256"], 16) > 0
            expected.update(episodes=1, events=events, decisions=decisions, checked_square_events=64 * events)
    assert dict(expected) == result["counts"] and result["interventions_per_kind"] == 60
    assert not any(r["owner"] == "astra-episode-actor-inputs-20261111"
                   for r in read(ROOT / "chatroom/cores.json")["allocation"])
    review = {"at": datetime.now(timezone.utc).isoformat(), "status": "complete_receipt_review",
              "result_sha256": sha(OUT / "result.json"), "review_source_sha256": sha(Path(__file__)),
              "source_derived_counts": dict(expected), "source_and_receipt_hashes_match": True,
              "core_lease_released": True,
              "scope": "Independent source-length/color/count and receipt reconciliation. Feature invariants and interventions ran inside the original audit; this is not a second feature pass, actual-shard audit, model/logit or strength test."}
    with (OUT / "review.json").open("x") as stream:
        stream.write(json.dumps(review, indent=2) + "\n")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
