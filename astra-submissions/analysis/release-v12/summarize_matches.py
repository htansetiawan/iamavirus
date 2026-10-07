"""Summarize the predeclared two-pair release check; never infer Elo from it."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
MATCHES = ROOT / "real-clock"
seeds = (3100, 4100)
pairs = [json.loads((MATCHES / f"pair-{seed}-summary.json").read_text())
         for seed in seeds]
games = []
for pair in pairs:
    assert len(pair["games"]) == 2
    for game in pair["games"]:
        path = MATCHES / game["replay"]
        replay = json.loads(path.read_text())
        diagnostics = replay.get("privateDiagnostics", {})
        hybrid = {side: len(re.findall(r"mode=hybrid", diagnostics.get(side, "")))
                  for side in ("white", "black")}
        fallback = [line for log in diagnostics.values() for line in log.splitlines()
                    if any(marker in line for marker in
                           ("model unavailable", "inference failed", "scoring failed", "mode=cpp"))]
        assert replay["result"] == game["result"]
        assert not replay.get("failedSide"), replay
        assert all(hybrid.values()), hybrid
        assert not fallback, fallback
        assert replay["reason"] in ("King capturable", "King captured", "Stalemate",
                                    "Fifty-move rule", "Threefold repetition", "Ply limit",
                                    "Insufficient material"), replay["reason"]
        games.append({**game, "seed_pair": pair["seed"],
                      "replay_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "hybrid_turns_in_diagnostic_tail": hybrid,
                      "protocol_truncated": replay.get("protocol", {}).get("truncated"),
                      "warnings": replay.get("warnings", [])})
scores = [g["score"] for g in games]
report = {
    "candidate_archive": "astra-submissions/iamavirus-v12-hybrid.zip",
    "candidate_archive_sha256": "a5f806d0039f514006f3af902767557ad35137d9d02e2779181d438eb5b47cf3",
    "opponent": "archived arena v10 (6f57a44ec814), not Duck or TA executables",
    "time_control": "180+2", "pairs": len(pairs), "games": games,
    "record": {"wins": scores.count(1.0), "draws": scores.count(0.5), "losses": scores.count(0.0)},
    "score_rate": sum(scores) / len(scores),
    "pair_scores": [p["paired_score"] for p in pairs],
    "protocol_failures": 0,
    "limitations": [
        "Four games are a bounded release check, not an Elo estimate or resolved strength comparison.",
        "No direct match against Duck or TA A/S is possible with their public replay API alone.",
        "Bot diagnostics are bounded stderr tails; final protocol results cover complete games.",
        "Wall-clock search depends on local hardware and load despite separated CPU affinity.",
    ],
}
(MATCHES / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "games"}, indent=2))
