"""Export the sealed 164-game recovery into a portable, metadata-only overlay.

This reconciles saved bytes and prior review receipts; it makes no API request
and does not repeat the earlier board/view or rules audits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.metadata_overlay import FIELDS, FORMAT, load_metadata_overlay

REVIEW_SHA256 = "793e8c9ce466679173bba99df1f42f8d6bede2b35c2fe4c8f347a797884bbb5c"
EXPECTED_GAMES = 164


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def indexed(records, key):
    result = {}
    for record in records:
        identity = key(record)
        require(identity not in result, f"duplicate recovery record {identity}")
        result[identity] = record
    return result


def export_overlay(root: Path, output: Path) -> dict:
    root = root.resolve()
    reviewed = root / "astra-submissions/analysis/corpus-metadata-recovery-20261111"
    bundle = root / "data/astra-spool/corpus-metadata-recovery-20261111"
    review_bytes = (reviewed / "review.json").read_bytes()
    require(sha(review_bytes) == REVIEW_SHA256, "historical review hash differs")
    review = json.loads(review_bytes)
    require(review["all_164_recovered"] is True and review["recovered"] == EXPECTED_GAMES,
            "historical recovery review is incomplete")
    # Resolve only immutable evidence files. The review also pins the OLD
    # importer source; its historical hash must not be compared to today's fix.
    paths = {
        "plan.json": reviewed / "plan.json", "result.json": reviewed / "result.json",
        "execution.json": reviewed / "execution.json",
        "supplement.json": bundle / "supplement.json",
        "sources.json": bundle / "sources.json", "receipts.jsonl": bundle / "receipts.jsonl",
    }
    payloads = {name: path.read_bytes() for name, path in paths.items()}
    result = json.loads(payloads["result.json"])
    hashes = {Path(path).name: digest for path, digest in review["hashes"].items()}
    hashes.update({Path(path).name: digest for path, digest in result["hashes"].items()})
    for name, payload in payloads.items():
        require(sha(payload) == hashes[name], f"historical evidence hash differs: {name}")
    require(result["recovered"] == EXPECTED_GAMES and result["remaining"] == 0,
            "historical recovery result is incomplete")
    supplements = indexed(json.loads(payloads["supplement.json"]), lambda x: x["id"])
    sources = indexed(json.loads(payloads["sources.json"]), lambda x: x["row"]["id"])
    receipts = indexed([json.loads(line) for line in payloads["receipts.jsonl"].splitlines()],
                       lambda x: x["id"])
    require(len(supplements) == EXPECTED_GAMES and supplements.keys() == sources.keys() == receipts.keys(),
            "recovery identity sets differ")
    records = []
    for game, supplement in sorted(supplements.items()):
        source, receipt = sources[game], receipts[game]
        original_bytes = (bundle / "originals" / f"{game}.json").read_bytes()
        response_bytes = (bundle / "responses" / f"{game}.json").read_bytes()
        original, response = json.loads(original_bytes), json.loads(response_bytes)
        require(original["id"] == response["id"] == game, f"saved game ID differs: {game}")
        require(sha(original_bytes) == source["sha256"] == supplement["original_sha256"]
                == receipt["original_sha256"], f"original replay hash differs: {game}")
        require(sha(response_bytes) == supplement["response_sha256"] == receipt["fetch"]["sha256"],
                f"response hash differs: {game}")
        require(receipt["status"] == "accepted" and receipt["fetch"]["status"] == 200,
                f"unaccepted response: {game}")
        require(receipt["response_bytes"] == len(response_bytes), f"response length differs: {game}")
        for replay in (original, response):
            moves = " ".join(frame["move"] for frame in replay["frames"] if frame.get("move"))
            require(sha(moves.encode()) == supplement["moves_sha256"] == source["row"]["moves_sha256"],
                    f"saved move identity differs: {game}")
        require(supplement["metadata"] == receipt["metadata"], f"metadata receipt differs: {game}")
        for field, value in supplement["metadata"].items():
            require(response.get(field) == value, f"response metadata differs: {game}/{field}")
        require(FIELDS <= supplement["metadata"].keys(), f"incomplete metadata: {game}")
        records.append({key: supplement[key] for key in
                        ("id", "original_sha256", "moves_sha256", "response_sha256")})
        records[-1]["metadata"] = {key: supplement["metadata"][key] for key in sorted(FIELDS)}
    overlay = {
        "format": FORMAT,
        "provenance": {
            "review_sha256": REVIEW_SHA256, "reviewed_at": review["at"],
            "evidence_sha256": {name: sha(payload) for name, payload in payloads.items()},
            "scope": "Saved-byte/receipt reconciliation of the previously reviewed recovery; no new API or rules audit.",
        },
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write((json.dumps(overlay, indent=1, sort_keys=True) + "\n").encode())
    checked = load_metadata_overlay(output)
    return {"path": str(output), "sha256": checked.sha256, "records": len(checked.records),
            "fields": sorted(FIELDS), "bytes": output.stat().st_size}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(export_overlay(args.root, args.out), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
