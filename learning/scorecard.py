"""Skill scorecard: every team on the same move-taxonomy metrics over the same games, our rank in a
cohort, the two reference teams and the tier-two median beside us (docs/skill-rubric-20261028.md).

    python -m learning.scorecard --raw data/raw --out data/reports/daily [--days 3] [--since DATE]
                                 [--from-table TABLE.txt --from-json GAMES.json]

Writes <out>/scorecard-<date>.md and <out>/scorecard-latest.md (plus the taxonomy table and the
labelled games under <out>/scorecard-<date>.{txt,json} when it computed them).
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import statistics as st
import subprocess
import sys

import chess

COHORT = ["Greek Gift", "Knight Vision", "Strongly Invisible", "Decent Chess Bot", "Crimson Fog", "duck",
          "Instructors", "Mist Opportunities", "HYPOTHERMIA", "IAmAVirus", "Lost Signal", "Gravel Road",
          "In Pawn Sight", "Sausage", "Mu1tip13 @g3nt$"]
TIER2 = ["Knight Vision", "Strongly Invisible", "Decent Chess Bot", "Crimson Fog"]
REFS = ["Instructors", "HYPOTHERMIA"]
US = "IAmAVirus"
# metric, +1 higher is better / -1 lower is better, category
METRICS = [("king_threat", +1, "initiative"), ("king_threat_unseen", +1, "information"),
           ("capture_unseen", +1, "information"), ("capt_unseen_share", +1, "information"),
           ("fog_route", +1, "information"), ("fog_depth", +1, "information"), ("long_strike", +1, "initiative"),
           ("victim_walked_in", +1, "initiative"), ("vision_gain", +1, "information"), ("vision_loss", -1, "information"),
           ("sacrifice", -1, "material"), ("queen_exposed_unseen", -1, "king/queen safety"),
           ("walk_into_unseen", -1, "king/queen safety"), ("back_rank_bare", -1, "king/queen safety"),
           ("king_leaves_home", -1, "king/queen safety"), ("king_move", -1, "king/queen safety")]
GAME_METRICS = [("losses ending with the king taken by a piece the loser could not see (share of losses)", "died_unseen", -1),
                ("median loss length (plies)", "loss_plies", +1),
                ("wins by king capture within 60 plies (share of wins)", "win_fast", +1),
                ("median win length (plies)", "win_plies", -1)]


def parse_table(path: str) -> dict:
    lines = [l.rstrip("\n") for l in open(path)]
    hdr = [h.strip() for h in lines[1].split("|")]
    rows = {}
    for l in lines[2:]:
        c = [x.strip() for x in l.split("|")]
        if len(c) != len(hdr):
            continue
        rows[c[0]] = {h: (float(v) if i > 0 else v) for i, (h, v) in enumerate(zip(hdr, c))}
    return rows


def board_from(s: str) -> chess.Board:  # 64 chars, rank 1 first
    b = chess.Board(None)
    for i, ch in enumerate(s):
        if ch not in "-?":
            b.set_piece_at(i, chess.Piece.from_symbol(ch))
    return b


def per_game(games: list, raw: str, cohort: list) -> dict:
    T = collections.defaultdict(lambda: {"losses": 0, "died_unseen": 0, "loss_plies": [], "wins": 0, "win_fast": 0, "win_plies": []})
    for g in games:
        res = g.get("result")
        if res not in ("1-0", "0-1"):
            continue
        winner = g["white"] if res == "1-0" else g["black"]
        loser = g["black"] if res == "1-0" else g["white"]
        if winner not in cohort and loser not in cohort:
            continue
        p = os.path.join(raw, "games", g["id"], "replay.json")
        if not os.path.exists(p):
            continue
        fr = json.load(open(p)).get("frames", [])
        if not fr:
            continue
        last = fr[-1]
        n = last.get("ply") or len(fr) - 1
        loser_white = res == "0-1"
        b = board_from(last["board"])
        view = last["white"] if loser_white else last["black"]
        k = b.king(chess.WHITE if loser_white else chess.BLACK)
        unseen = False
        if k is not None:
            att = b.attackers(chess.BLACK if loser_white else chess.WHITE, k)
            unseen = bool(att) and any(view[sq] == "?" for sq in att)
        T[loser]["losses"] += 1
        T[loser]["loss_plies"].append(n)
        T[loser]["died_unseen"] += unseen
        T[winner]["wins"] += 1
        T[winner]["win_plies"].append(n)
        T[winner]["win_fast"] += n <= 60
    out = {}
    for t in cohort:
        x = T[t]
        if x["losses"] < 20 or x["wins"] < 20:
            continue
        out[t] = {"died_unseen": x["died_unseen"] / x["losses"], "loss_plies": st.median(x["loss_plies"]),
                  "win_fast": x["win_fast"] / x["wins"], "win_plies": st.median(x["win_plies"]),
                  "losses": x["losses"], "wins": x["wins"]}
    return out


def render(rows: dict, pg: dict, since: str, n_games: int) -> str:
    cohort = [t for t in COHORT if t in rows]
    f = lambda x: f"{x:.2f}"
    out = [f"# Skill scorecard, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC",
           "", f"All arena games since {since} ({n_games} games); every team on the same metrics; rank = our position among the "
           f"{len(cohort)}-team cohort (1 is best). Rubric: docs/skill-rubric-20261028.md.", "",
           "## Per 100 own moves", "",
           f"| metric | category | us | rank /{len(cohort)} | Instructors | HYPOTHERMIA | tier-two median | Greek Gift |",
           "|---|---|---|---|---|---|---|---|"]
    weak, strong = [], []
    for m, sgn, cat in METRICS:
        if any(m not in rows[t] for t in cohort):
            continue
        order = sorted(cohort, key=lambda t: -sgn * rows[t][m])
        r = order.index(US) + 1 if US in order else None
        t2 = st.median(rows[t][m] for t in TIER2 if t in rows)
        cell = lambda t: f(rows[t][m]) if t in rows else "-"
        out.append(f"| {m} | {cat} | {cell(US)} | {r} | {cell('Instructors')} | {cell('HYPOTHERMIA')} | {f(t2)} | {cell('Greek Gift')} |")
        if r is not None:
            (weak if r >= len(cohort) - 3 else strong if r <= 4 else []).append((r, m))
    out += ["", "## Per game", "",
            f"| metric | us | rank /{len(pg)} | Instructors | HYPOTHERMIA | tier-two median | Greek Gift |", "|---|---|---|---|---|---|---|"]
    for name, key, sgn in GAME_METRICS:
        if US not in pg:
            break
        order = sorted(pg, key=lambda t: -sgn * pg[t][key])
        r = order.index(US) + 1
        t2 = st.median(pg[t][key] for t in TIER2 if t in pg)
        cell = lambda t: f(pg[t][key]) if t in pg else "-"
        out.append(f"| {name} | {cell(US)} | {r} | {cell('Instructors')} | {cell('HYPOTHERMIA')} | {f(t2)} | {cell('Greek Gift')} |")
    out += ["", "## Weakest and strongest (per 100 moves, by rank)", "",
            "- weakest: " + (", ".join(f"{m} ({r})" for r, m in sorted(weak, reverse=True)) or "none in the bottom four"),
            "- strongest: " + (", ".join(f"{m} ({r})" for r, m in sorted(strong)) or "none in the top four"), ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/reports/daily")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--since", default=None)
    ap.add_argument("--from-table", default=None)
    ap.add_argument("--from-json", default=None)
    ap.add_argument("--min-games", type=int, default=150)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    since = args.since or (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)).strftime("%Y-%m-%d")
    table, gjson = args.from_table, args.from_json
    if not table:
        table = os.path.join(args.out, f"scorecard-{today}.txt")
        gjson = os.path.join(args.out, f"scorecard-{today}.json")
        with open(table, "w") as fh:
            subprocess.run([sys.executable, "-m", "learning.move_taxonomy", "--raw", args.raw, "--all-games", "--by-team",
                            "--since", since, "--min-games", str(args.min_games), "--json", gjson], stdout=fh, check=True)
    rows = parse_table(table)
    games = json.load(open(gjson))["games"] if gjson and os.path.exists(gjson) else []
    pg = per_game(games, args.raw, [t for t in COHORT if t in rows]) if games else {}
    md = render(rows, pg, since, len(games))
    path = os.path.join(args.out, f"scorecard-{today}.md")
    open(path, "w").write(md)
    open(os.path.join(args.out, "scorecard-latest.md"), "w").write(md)
    print(path)


if __name__ == "__main__":
    main()
