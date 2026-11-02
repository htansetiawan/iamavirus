"""Freeze cached v35/v37 outcomes at the saved public leaderboard timestamp.

Descriptive opponent/version/colour adjustment, not a randomized comparison.
No new API reads, training, candidate changes, or match scheduling.
"""
from collections import Counter, defaultdict
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
TEAM = "a2c35173659545c99752376a70418438"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def record(rows):
    c = Counter(r["outcome"] for r in rows)
    n = len(rows)
    return dict(games=n, wins=c["W"], draws=c["D"], losses=c["L"],
                points=c["W"] + .5 * c["D"],
                score=(c["W"] + .5 * c["D"]) / n if n else None)


def main():
    standings = json.loads((OUT / "standings.json").read_text())
    cutoff = datetime.fromisoformat(standings["at"])
    snapshot_ours = next(p for p in standings["players"] if p["id"] == TEAM)
    assert snapshot_ours["activeVersion"] == 37
    payload = (ROOT / "data/raw/accepted.jsonl").read_bytes()
    selected = {}
    missing_dates = 0
    for line in payload.splitlines():
        r = json.loads(line)
        side = next((s for s in ("white", "black") if r.get(s + "PlayerId") == TEAM), None)
        if side is None or r.get(side + "Version") not in (35, 37):
            continue
        if not r.get("createdAt"):
            missing_dates += 1
            continue
        if datetime.fromisoformat(r["createdAt"]) > cutoff:
            continue
        other = "black" if side == "white" else "white"
        assert r["result"] in ("1-0", "0-1", "1/2-1/2")
        outcome = "D" if r["result"] == "1/2-1/2" else "W" if (r["result"] == "1-0") == (side == "white") else "L"
        row = dict(game=r["id"], at=r["createdAt"], version=r[side + "Version"],
                   colour=side, opponent=r[other], opponent_id=r.get(other + "PlayerId"),
                   opponent_version=r.get(other + "Version"), outcome=outcome,
                   points={"W": 1, "D": .5, "L": 0}[outcome], reason=r.get("reason"))
        if row["game"] in selected:
            assert selected[row["game"]] == row, row["game"]
        selected[row["game"]] = row
    rows = sorted(selected.values(), key=lambda r: (r["at"], r["game"]))
    current = [r for r in rows if r["version"] == 37]
    current_record = record(current)
    for key in ("games", "wins", "draws", "losses"):
        assert current_record[key] == snapshot_ours["activeRecord"][key], key
    replay_hashes = {}
    for r in current:
        raw = (ROOT / "data/raw/games" / r["game"] / "replay.json").read_bytes()
        replay = json.loads(raw)
        assert replay[r["colour"] + "PlayerId"] == TEAM
        assert replay[r["colour"] + "Version"] == 37
        assert replay["createdAt"] == r["at"]
        expected = "1/2-1/2" if r["outcome"] == "D" else "1-0" if (r["outcome"] == "W") == (r["colour"] == "white") else "0-1"
        assert replay["result"] == expected
        replay_hashes[r["game"]] = sha(raw)
    baseline = defaultdict(list)
    key = lambda r: (r["opponent_id"], r["opponent_version"], r["colour"])
    for r in rows:
        if r["version"] == 35:
            baseline[key(r)].append(r)
    shared = [r for r in current if key(r) in baseline]
    adjusted = sum(record(baseline[key(r)])["score"] for r in shared)
    groups = defaultdict(list)
    for r in current:
        groups[(r["opponent"], r["opponent_version"])].append(r)
    top6 = {p["id"] for p in standings["players"] if p["rank"] <= 6}
    result = dict(as_of=standings["at"], standings_sha256=sha((OUT / "standings.json").read_bytes()),
                  accepted_index_read_sha256=sha(payload), source_sha256=sha(Path(__file__).read_bytes()),
                  missing_dates=missing_dates, v37=current_record, v35_cached=record([r for r in rows if r["version"] == 35]),
                  leaderboard_counts_match=True, v37_replay_sha256=replay_hashes,
                  top6_definition="Top six in this saved snapshot, including staff/external teams; historical played versions retained.",
                  v37_against_top6=record([r for r in current if r["opponent_id"] in top6]),
                  opponents=[dict(opponent=k[0], version=k[1], **record(v)) for k, v in sorted(groups.items())],
                  adjustment=dict(strata="exact opponent ID, played opponent version, our colour", shared_v37=record(shared),
                                  expected_v35_points=adjusted, expected_v35_score=adjusted / len(shared) if shared else None,
                                  unmatched_v37=[r["game"] for r in current if key(r) not in baseline],
                                  baseline_support=[dict(opponent=s[0], version=s[1], colour=s[2], **record(baseline[s])) for s in sorted({key(r) for r in shared}, key=str)],
                                  limitation="Historical raw rates, not concurrent controls. Calendar time, game dependence, small strata and other changes remain confounders; no causal Elo estimate."))
    compressed = gzip.compress(("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n").encode(), mtime=0)
    result["selected_rows_sha256"] = sha(compressed)
    with (OUT / "arena-selected.jsonl.gz").open("xb") as f:
        f.write(compressed)
    with (OUT / "arena-panel.json").open("x") as f:
        json.dump(result, f, indent=2); f.write("\n")
    compact = {k: result[k] for k in ("as_of", "v37", "v37_against_top6", "leaderboard_counts_match")}
    compact["shared"] = result["adjustment"]["shared_v37"]
    compact["historical_v35_expected_score"] = result["adjustment"]["expected_v35_score"]
    print(json.dumps(compact))


if __name__ == "__main__":
    main()
