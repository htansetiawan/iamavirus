"""Import a frozen completed-game window through the standard RawStore path.

Reuse checkpoint responses, bound new public requests, and preserve the old
journal prefix. This collects evidence; it does not export or fit a model.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--spool", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    args = parser.parse_args(argv)
    from learning import _native, api_client, dataset, ingest

    started = time.monotonic()
    plan_bytes = args.plan.read_bytes()
    plan = json.loads(plan_bytes)
    require(sha(args.native.read_bytes()) == plan["native_sha256"], "native source differs")
    require(sha(Path(ingest.__file__).read_bytes()) == plan["root_ingest_sha256"], "ingest source differs")
    require(_native._library is None, "native library already initialized")
    _native.ensure_built = lambda verbose=True: args.native.resolve()
    page_bytes = (args.spool / "games-page.json").read_bytes()
    require(sha(page_bytes) == plan["listing_sha256"], "listing snapshot differs")
    ids = set(plan["completed_game_ids"])
    selected = [game for game in json.loads(page_bytes)["games"] if game["id"] in ids]
    require(len(selected) == len(ids) == 68, "frozen game identities differ")
    args.out.mkdir(parents=True, exist_ok=False)
    store = ingest.RawStore(args.root / "data/raw")
    require(not os.statvfs(store.root).f_flag & os.ST_RDONLY, "host archive is read-only")
    known = store.accepted_ids()
    with store.writer():
        _, before = dataset.dataset_source_rows(store.accepted)
    require(before == plan["source_journal_before"], "journal changed since preflight; review before writing")
    require(set(plan["initial_missing_ids"]) == ids - known, "accepted identities changed since preflight")
    cache = {record["id"]: record for record in json.loads((args.spool / "duck-receipts.json").read_text())}
    listing_receipt = json.loads((args.spool / "receipts.json").read_text())[1]

    class BudgetClient(api_client.ApiClient):
        def _pace(self):
            if self.requests_made >= plan["maximum_HTTP_attempts"]:
                raise RuntimeError("HTTP request budget reached")
            super()._pace()

    client = BudgetClient(cache_dir=store.root, min_interval=plan["minimum_request_interval_seconds"], timeout=20)
    counts = {"accepted": 0, "recovered": 0, "already_accepted": 0,
              "checkpoint_cache": 0, "canonical_cache": 0, "quarantined": 0}
    receipts = []
    stop_reason = "completed frozen window"
    # Archive the already captured leaderboard using the normal snapshot shape.
    lb_receipt = json.loads((args.spool / "receipts.json").read_text())[0]
    lb_bytes = (args.spool / "leaderboard.json").read_bytes()
    require(sha(lb_bytes) == lb_receipt["sha256"], "cached leaderboard differs")
    stamp = lb_receipt["fetched_at"].replace(":", "").replace("+", "Z")
    snapshot = store.snapshots / stamp / "leaderboard.json"
    envelope = {"fetched": lb_receipt, "leaderboard": json.loads(lb_bytes)}
    if snapshot.exists():
        require(json.loads(snapshot.read_text()) == envelope, "existing snapshot differs")
    else:
        store.write_json(snapshot, envelope)
    for listing in selected:
        if time.monotonic() - started >= plan["soft_wall_seconds"]:
            stop_reason = "soft wall budget before starting another game"
            break
        game = listing["id"]
        required = ["replay.json", "fetch_metadata.json", "listing.json"]
        if game == "rdbx11vy":
            required.append("diagnostics.json")
        if game in known and all((store.games / game / name).is_file() for name in required):
            counts["already_accepted"] += 1
            receipts.append({"id": game, "status": "already_accepted"})
            continue
        try:
            if game in cache:
                payload = (args.spool / f"{game}-replay.json").read_bytes()
                require(sha(payload) == cache[game]["sha256"], f"cached replay differs: {game}")
                replay = json.loads(payload)
                record = {key: cache[game][key] for key in ("url", "fetched_at", "sha256", "status", "attempts")}
                counts["checkpoint_cache"] += 1
            else:
                replay, fetched, cached = client.replay(game)
                record = asdict(fetched)
                counts["canonical_cache"] += int(cached)
            for key in ("id", "white", "black", "result", "reason", "whitePlayerId", "blackPlayerId", "whiteVersion", "blackVersion"):
                require(replay.get(key) == listing.get(key), f"listing/replay differs: {game}/{key}")
            require(len(replay["frames"]) - 1 == listing["plies"], f"ply count differs: {game}")
            fetch = {"replay": record, "listing_source": listing_receipt["url"],
                     "listing_snapshot_sha256": plan["listing_sha256"], "checkpoint_plan_sha256": sha(plan_bytes)}
            diagnostics = None
            if game == "rdbx11vy":
                diag_bytes = (args.spool / "rdbx11vy-diagnostics.json").read_bytes()
                diag_receipt = json.loads((args.spool / "diagnostics-receipt.json").read_text())
                require(sha(diag_bytes) == diag_receipt["sha256"], "cached diagnostics differ")
                diagnostics = json.loads(diag_bytes)
                fetch["diagnostics"] = diag_receipt
            problems = ingest.ingest_replay(store, replay, listing, fetch, diagnostics)
            if problems:
                counts["quarantined"] += 1
                receipts.append({"id": game, "status": "quarantined", "problems": list(problems), "fetch": record})
                stop_reason = "first validator rejection"
                break
            status = "already_accepted" if problems.cached else "recovered" if problems.recovered else "accepted"
            counts[status] += 1
            known.add(game)
            receipts.append({"id": game, "status": status, "fetch": record})
            if len(receipts) % 10 == 0:
                print(f"{len(receipts)}/68 sources; {client.requests_made} HTTP attempts", flush=True)
        except Exception as error:
            receipts.append({"id": game, "status": "error", "error": f"{type(error).__name__}: {error}"})
            stop_reason = "first collection error"
            break
    with store.writer():
        final_rows, after = dataset.dataset_source_rows(store.accepted)
        prefix = hashlib.sha256()
        with store.accepted.open("rb") as stream:
            remaining = before["bytes"]
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                require(bool(chunk), "old journal prefix was truncated")
                prefix.update(chunk)
                remaining -= len(chunk)
    require(prefix.hexdigest() == before["sha256"], "old journal prefix changed")
    present = {row["id"] for row in final_rows} & ids
    result = {"at": datetime.now(timezone.utc).isoformat(), "stop_reason": stop_reason,
              "complete": present == ids and stop_reason == "completed frozen window", "counts": counts,
              "planned": len(ids), "planned_present": len(present), "remaining_ids": sorted(ids - present),
              "HTTP_attempts": client.requests_made, "elapsed_seconds": time.monotonic() - started,
              "journal_before": before, "journal_after": after, "old_journal_prefix_preserved": True,
              "accepted_ID_index_bytes_read": store._index_bytes_read, "snapshot": str(snapshot),
              "plan_sha256": sha(plan_bytes), "producer_sha256": sha(Path(__file__).read_bytes()),
              "native_sha256": plan["native_sha256"], "receipts": receipts,
              "scope": "Canonical completed replay ingestion only; no training export, fit, GPU, model, match, ZIP/version, service or deployment change."}
    with (args.out / "result.json").open("x") as stream:
        json.dump(result, stream, indent=1, sort_keys=True)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("complete", "counts", "planned_present", "HTTP_attempts", "elapsed_seconds")}), flush=True)
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
