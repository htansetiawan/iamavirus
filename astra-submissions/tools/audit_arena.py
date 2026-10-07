#!/usr/bin/env python3
"""Offline, reproducible audit of public records and immutable submission ZIPs.

Reads completed-game truth only for post-game diagnosis. Nothing in this tool
is used as a bot observation, feature, or live decision input. Standard library
only; no network requests, training, uploads, or changes to shared engine files.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

TEAM = "a2c35173659545c99752376a70418438"


def square(index):
    return "abcdefgh"[index % 8] + str(index // 8 + 1)


def attackers(board, target, white):
    """Geometric attackers, including pinned pieces: Fog has no check rule."""
    found = []
    tx, ty = target % 8, target // 8
    for source, symbol in enumerate(board):
        if symbol == "-" or symbol.isupper() != white:
            continue
        sx, sy = source % 8, source // 8
        dx, dy = tx - sx, ty - sy
        ax, ay = abs(dx), abs(dy)
        kind = symbol.upper()
        if source == target:
            continue
        hits = (
            kind == "P" and ax == 1 and dy == (1 if white else -1)
            or kind == "N" and sorted((ax, ay)) == [1, 2]
            or kind == "K" and max(ax, ay) == 1
        )
        diagonal, straight = ax == ay, dx == 0 or dy == 0
        if ((kind in "BQ" and diagonal) or (kind in "RQ" and straight)):
            ux, uy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
            x, y = sx + ux, sy + uy
            hits = True
            while (x, y) != (tx, ty):
                if board[y * 8 + x] != "-":
                    hits = False
                    break
                x, y = x + ux, y + uy
        if hits:
            found.append(source)
    return found


def outcome(game, side):
    return "D" if game["result"] == "1/2-1/2" else (
        "W" if game["result"] == ("1-0" if side == "white" else "0-1") else "L")


def record(counts):
    n = sum(counts.values())
    return {"wins": counts["W"], "draws": counts["D"], "losses": counts["L"],
            "games": n, "score": (counts["W"] + counts["D"] / 2) / n if n else None}


def audit(snapshot, archives):
    games = json.loads((snapshot / "games.json").read_text())
    versions = json.loads((snapshot / "versions.json").read_text())
    groups = defaultdict(Counter)
    opponents = defaultdict(lambda: defaultdict(Counter))
    colors = defaultdict(lambda: defaultdict(Counter))
    reasons = defaultdict(Counter)
    losses, technical = [], []
    for game in games:
        side = "white" if game["whitePlayerId"] == TEAM else "black"
        assert game[side + "PlayerId"] == TEAM
        other = "black" if side == "white" else "white"
        version = game[side + "Version"]
        result = outcome(game, side)
        opponent = f"{game[other]} v{game[other + 'Version']}"
        groups[version][result] += 1
        opponents[version][opponent][result] += 1
        colors[version][side][result] += 1
        reasons[version][game["reason"]] += 1
        if version not in (5, 8):
            continue
        if game["reason"] not in ("King capturable", "Threefold repetition"):
            diag = snapshot / "diagnostics" / f"{game['id']}.json"
            reports = json.loads(diag.read_text())["reports"] if diag.exists() else []
            technical.append({"game": game["id"], "version": version,
                              "result": result, "reason": game["reason"],
                              "our_side": side,
                              "reports": [{k: r[k] for k in ("side", "code", "ply")}
                                          for r in reports]})
        if result != "L" or game["reason"] != "King capturable":
            continue
        replay = json.loads((snapshot / "replays" / f"{game['id']}.json").read_text())
        before, after = replay["frames"][-2:]
        assert after["ply"] % 2 == (1 if side == "white" else 0)
        board, obs = after["board"], before[side]
        king = board.index("K" if side == "white" else "k")
        threats = attackers(board, king, white=(side == "black"))
        assert threats, game["id"]
        move = after["move"]
        src = (int(move[1]) - 1) * 8 + ord(move[0]) - ord("a")
        dst = (int(move[3]) - 1) * 8 + ord(move[2]) - ord("a")
        king_move = before["board"][src].upper() == "K"
        losses.append({"game": game["id"], "version": version, "opponent": opponent,
                       "side": side, "decision_ply": before["ply"], "move": move,
                       "king": square(king), "king_moved": king_move,
                       "king_capture": king_move and before["board"][dst] != "-",
                       "attackers": [{"square": square(s), "piece": board[s],
                                      "hidden_before_decision": obs[s] == "?"}
                                     for s in threats],
                       "all_attackers_hidden": all(obs[s] == "?" for s in threats)})
    # Reconcile independent endpoints; do not silently combine different snapshots.
    for row in versions["versions"]:
        actual = record(groups[row["version"]])
        for key in ("wins", "draws", "losses", "games"):
            assert actual[key] == row[key], (row["version"], key, actual, row)
    a_path = archives / "iamavirus-v6-hybrid.zip"
    b_path = archives / "iamavirus-v6.1-hybrid.zip"
    with zipfile.ZipFile(a_path) as a, zipfile.ZipFile(b_path) as b:
        names = sorted(set(a.namelist()) | set(b.namelist()))
        differences = [n for n in names if n not in a.namelist() or n not in b.namelist()
                       or a.read(n) != b.read(n)]
        model_names = [n for n in a.namelist() if n.startswith("model/") and not n.endswith("/")]
        model_hashes = {n: hashlib.sha256(a.read(n)).hexdigest() for n in model_names}
        model_identical = all(n in b.namelist() and a.read(n) == b.read(n) for n in model_names)
    common = sorted(set(opponents[5]) & set(opponents[8]))
    common_records = {str(v): record(sum((opponents[v][o] for o in common), Counter()))
                      for v in (5, 8)}
    return {"team": TEAM, "games": len(games),
            "versions": {str(v): {**record(groups[v]), "by_opponent": {
                k: record(c) for k, c in sorted(opponents[v].items())},
                "by_color": {k: record(c) for k, c in colors[v].items()},
                "termination_reasons": dict(reasons[v])} for v in sorted(groups)},
            "shared_opponent_versions": common, "shared_opponent_records": common_records,
            "equal_weight_shared_opponent_score": {str(v): sum(
                record(opponents[v][o])["score"] for o in common) / len(common) for v in (5, 8)},
            "terminal_losses": losses, "technical_games": technical,
            "archives": {"sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in (a_path, b_path)},
                         "different_files": differences, "identical_models": model_identical,
                         "model_sha256": model_hashes},
            "limitations": ["Arena v8 archive identity is inferred from the local tracker, not certified by the API.",
                            "Shared-opponent aggregates still have different opponent and color weights.",
                            "Terminal truth labels describe what lost, not the bot's belief or the first strategic error.",
                            "No counterfactual playing-strength claim or new training run is made."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--snapshot", type=Path,
                        default=root / "astra-submissions/snapshots/2026-10-07-initial")
    parser.add_argument("--archives", type=Path, default=root / "submissions")
    args = parser.parse_args()
    print(json.dumps(audit(args.snapshot, args.archives), indent=2))


if __name__ == "__main__":
    main()
