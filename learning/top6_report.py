"""Why we lose to the top six: a periodic, phone-readable report.

    python -m learning.top6_report [--versions 20 21] [--raw data/raw] [--output data/reports/top6-report.md]

Reads the ingested arena replays (learning.ingest) and the latest leaderboard
snapshot, and writes:

1. The ladder: the top six's ratings, ours, and the gaps to duck and Instructors.
2. Our record against each top-six team, by arena version.
3. Skill gaps: the move taxonomy (learning/move_taxonomy.py) grouped into skill
   categories, us against them, for duck + Instructors, for the other four, and
   for the TA baselines as the contrast where we win; plus the top six's own
   fingerprint in games among themselves (what winning looks like at that level).
4. Loss anatomy for the active version against the top six: how our king fell
   (attacker seen or unseen, escape available or not, self-inflicted or not),
   when and how the material went (first ply at -3 and -5 and the capture that
   did it), lost games we had been winning, and clock floors.
5. What worked: our wins and draws against them.

Pure measurement; it changes nothing.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics
import time

import chess

from .move_taxonomy import KEYS, aggregate, fen, label_game, material

TOP6 = ["Greek Gift", "Knight Vision", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"]
TARGETS = ["duck", "Instructors"]
TA = ["TA Baseline P", "TA Baseline A", "TA Baseline S"]
US = "IAmAVirus"

# Skill categories over the taxonomy tags. "higher" says which direction is good
# for the side that has it (None: descriptive only).
CATEGORIES = [
    ("Information", [("visible_mean", "squares we see (mean)", True), ("vision_gain", "vision-gaining moves", True)]),
    ("Stealth (attacking from the fog)", [("capture_unseen_share", "captures the victim's side could not see coming (share)", True),
                                          ("capture_unseen", "captures from unseen squares", True),
                                          ("fog_route", "captures after a route the other side never saw", True),
                                          ("long_strike", "long slider strikes", True)]),
    ("King pressure", [("king_threat", "moves that attack the enemy king", True),
                       ("king_threat_unseen", "...with an attacker the king's side cannot see", True),
                       ("king_hunt_sacrifice", "sacrifices that lead to a king capture", True)]),
    ("Queen activity", [("queen_raid", "queen moves into the enemy half", None)]),
    ("Discipline (not giving things away)", [("sacrifice", "material given (3+ net over two plies)", False),
                                              ("walk_into_unseen", "pieces walked onto squares hit by unseen attackers", False),
                                              ("queen_exposed_unseen", "queen left attacked by an unseen piece", False),
                                              ("back_rank_bare", "bare back rank with enemy heavy pieces alive", False)]),
    ("King handling", [("king_move", "king moves", None), ("king_leaves_home", "king moves beyond the second rank", None),
                       ("castle", "castling", None)]),
]


def score_of(listing: dict, side: str) -> float:
    res = listing.get("result")
    if res == "1/2-1/2":
        return 0.5
    return 1.0 if (res == "1-0") == (side == "white") else 0.0


def load_listings(raw: str):
    for path in glob.glob(os.path.join(raw, "games", "*", "listing.json")):
        try:
            yield path, json.load(open(path))
        except Exception:
            continue


def latest_leaderboard(raw: str):
    snaps = sorted(glob.glob(os.path.join(raw, "snapshots", "*", "leaderboard.json")))
    if not snaps:
        return None, []
    d = json.load(open(snaps[-1]))
    lb = d.get("leaderboard")
    rows = lb.get("players") if isinstance(lb, dict) else lb
    fetched = d.get("fetched", {})
    when = fetched.get("fetched_at") if isinstance(fetched, dict) else None
    return when, rows or []


def loss_anatomy(r: dict, us_side: str) -> dict:
    """How a lost game went, from our side's point of view."""
    frames = r["frames"]
    n = len(frames) - 1
    U = 0 if us_side == "white" else 1
    T = 1 - U
    ucol, tcol = (chess.WHITE, chess.BLACK) if U == 0 else (chess.BLACK, chess.WHITE)
    view = "white" if U == 0 else "black"
    boards = [chess.Board(fen(f["board"])) for f in frames]
    diff = [material(f["board"], U) - material(f["board"], T) for f in frames]
    # Sustained levels: a lead or deficit counts only if it holds for four plies,
    # so the moment between a capture and its recapture is not a swing.
    def held(k, sign):
        window = diff[k:k + 4]
        return min(window) if sign > 0 else max(window)
    out = {"plies": n, "reason": r.get("reason"), "end_diff": diff[-1],
           "max_lead": max((held(k, 1) for k in range(0, n + 1)), default=0)}
    # material collapse: first ply where we stay 3 (and 5) down for four plies, and what did it
    for threshold in (3, 5):
        at = next((k for k in range(1, n + 1) if held(k, -1) <= -threshold), None)
        out[f"ply_minus{threshold}"] = at
        if at is not None and threshold == 3:
            mv = frames[at]["move"]
            before = boards[at - 1]
            cause = "other"
            if mv:
                dst = chess.parse_square(mv[2:4])
                victim = before.piece_at(dst)
                mover_is_them = (frames[at]["ply"] % 2 == 1) == (T == 0)
                if victim is not None and mover_is_them:
                    src = chess.parse_square(mv[:2])
                    # the view our last move was chosen from: two frames before their capture
                    decision_view = frames[max(0, at - 2)][view]
                    unseen = decision_view[src] == "?"
                    walked = at >= 2 and frames[at - 1]["move"] and chess.parse_square(frames[at - 1]["move"][2:4]) == dst
                    cause = ("capturer unseen when we moved" if unseen else "capturer visible when we moved") + \
                            (", piece had just moved there" if walked else "") + f" ({victim.symbol().lower()})"
                elif not mover_is_them:
                    cause = "our own move (exchange or sacrifice)"
            out["collapse_cause"] = cause
    # clock floor
    try:
        clocks = [f.get("clocks") for f in frames if f.get("clocks")]
        out["min_clock"] = min(c[U] for c in clocks) if clocks else None
    except Exception:
        out["min_clock"] = None
    # how the king fell
    if r.get("reason") == "King capturable" and n >= 1:
        last_mover_us = (frames[n]["ply"] % 2 == 1) == (U == 0)
        before, after = boards[n - 1], boards[n]
        king_before = before.king(ucol)
        attacked_before = bool(king_before is not None and before.attackers(tcol, king_before))
        king_after = after.king(ucol)
        attackers = list(after.attackers(tcol, king_after)) if king_after is not None else []
        seen_after = [frames[n][view][a] != "?" for a in attackers]
        kinds = sorted({after.piece_at(a).symbol().lower() for a in attackers if after.piece_at(a)})
        if not last_mover_us:
            how = "unusual: game ended after their move"
        elif attacked_before:
            prev_att = list(before.attackers(tcol, king_before))
            seen_before = any(frames[n - 1][view][a] != "?" for a in prev_att)
            escape = False
            b = before.copy(stack=False)
            b.turn = ucol
            for m in b.pseudo_legal_moves:
                b.push(m)
                k = b.king(ucol)
                if k is not None and not b.attackers(tcol, k):
                    escape = True
                b.pop()
                if escape:
                    break
            if not seen_before:
                how = "king already attacked by an unseen piece" + ("" if escape else "; no escape existed")
            else:
                how = "king attacked in plain sight and not saved" + ("" if escape else " (no escape existed)")
        else:
            moved = frames[n]["move"]
            king_moved = moved and before.piece_at(chess.parse_square(moved[:2])) and \
                before.piece_at(chess.parse_square(moved[:2])).piece_type == chess.KING
            # what the bot could see when it chose the move (the view before it)
            seen = any(frames[n - 1][view][a] != "?" for a in attackers)
            if king_moved:
                how = "our king walked into an attack" + (" we could see" if seen else " from an unseen piece")
            else:
                how = "our move opened a line to our king" + (" (attacker visible)" if seen else " (attacker unseen)")
        out["king_fell"] = how
        out["king_attackers"] = "".join(kinds)
    return out


def fmt(x, digits=1):
    return "–" if x is None else (f"{x:.{digits}f}" if isinstance(x, float) else str(x))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--versions", type=int, nargs="*", default=None,
                    help="our arena versions to analyse together, e.g. 20 21 for a re-upload of the same bytes (default: the active one)")
    ap.add_argument("--output", default="data/reports/top6-report.md")
    ap.add_argument("--peer-games", type=int, default=400, help="recent top-six-vs-top-six games for their fingerprint")
    args = ap.parse_args(argv)

    fetched_at, board = latest_leaderboard(args.raw)
    ratings = {row.get("name"): row.get("rating") for row in board}
    ours_row = next((row for row in board if row.get("name") == US), {})
    vset = set(args.versions) if args.versions else {ours_row.get("activeVersion")}
    version = "+".join(str(v) for v in sorted(vset))

    # select games from the listings
    ours = []          # (listing, our side, opponent, version, replay path)
    peers = []         # top six vs top six
    for path, l in load_listings(args.raw):
        w, b = l.get("white"), l.get("black")
        if US in (w, b):
            side = "white" if w == US else "black"
            ours.append((l, side, b if side == "white" else w, l.get(f"{side}Version"), path.replace("listing.json", "replay.json")))
        elif w in TOP6 and b in TOP6:
            peers.append((l.get("createdAt", ""), path.replace("listing.json", "replay.json")))

    lines = [f"# Against the top six", "",
             f"Updated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}; leaderboard fetched {fetched_at[:16] if fetched_at else '?'}. "
             f"Active version: v{version}. Measurement only.", ""]

    # 1. ladder
    lines += ["## Ladder", "", "| team | rating | gap to us |", "| --- | --- | --- |"]
    us_rating = ratings.get(US)
    for name in TOP6 + ["TA Baseline S", US, "TA Baseline A", "TA Baseline P"]:
        rt = ratings.get(name)
        if rt is None:
            continue
        gap = "" if name == US or us_rating is None else f"{rt - us_rating:+.0f}"
        lines.append(f"| {'**' + name + '**' if name in TARGETS or name == US else name} | {rt:.0f} | {gap} |")
    lines.append("")

    # 2. records by version
    versions = sorted({v for _, _, _, v, _ in ours if v}, reverse=True)[:6]
    rec = collections.defaultdict(lambda: [0, 0, 0])
    for l, side, opp, v, _ in ours:
        if opp in TOP6 + TA and v in versions:
            s = score_of(l, side)
            rec[(opp, v)][0 if s == 1 else 1 if s == 0.5 else 2] += 1
    lines += ["## Record by version (W-D-L)", "", "| opponent | " + " | ".join(f"v{v}" for v in versions) + " |",
              "| --- | " + " | ".join("---" for _ in versions) + " |"]
    for opp in TOP6 + TA:
        cells = []
        for v in versions:
            w, d, L = rec[(opp, v)]
            cells.append(f"{w}-{d}-{L}" if w + d + L else "")
        lines.append(f"| {'**' + opp + '**' if opp in TARGETS else opp} | " + " | ".join(cells) + " |")
    lines.append("")

    # 3. skill gaps
    def label_set(selector):
        labelled, roles = [], []
        for l, side, opp, v, rp in ours:
            if v in vset and selector(opp):
                try:
                    r = json.load(open(rp))
                except Exception:
                    continue
                if r.get("frames") and len(r["frames"]) >= 3:
                    labelled.append(label_game(r))
                    roles.append(side)
        return labelled, roles

    groups = [("duck + Instructors", lambda o: o in TARGETS), ("other four", lambda o: o in TOP6 and o not in TARGETS),
              ("TA baselines (contrast)", lambda o: o in TA)]
    fps = {}
    for name, sel in groups:
        labelled, roles = label_set(sel)
        if not labelled:
            continue
        idx = {id(g): roles[i] for i, g in enumerate(labelled)}
        us_fp = aggregate(labelled, lambda g: idx[id(g)])
        them_fp = aggregate(labelled, lambda g: "black" if idx[id(g)] == "white" else "white")
        fps[name] = (us_fp, them_fp, len(labelled))
    peer_fp = None
    if peers:
        peer_labelled = []
        for _, rp in sorted(peers, reverse=True)[: args.peer_games]:
            try:
                r = json.load(open(rp))
            except Exception:
                continue
            if r.get("frames") and len(r["frames"]) >= 3:
                peer_labelled.append(label_game(r))
        if peer_labelled:
            # both sides of every top-six game: aggregate white and black separately and average by moves
            w = aggregate(peer_labelled, lambda g: "white")
            b = aggregate(peer_labelled, lambda g: "black")
            peer_fp = {k: (w[k] * w["moves"] + b[k] * b["moves"]) / max(1, w["moves"] + b["moves"])
                       for k in w if isinstance(w[k], (int, float))}
            peer_fp["games"] = len(peer_labelled)

    lines += ["## Skill gaps (rates per 100 moves unless noted)", "",
              f"Active version v{version}. \"them\" is the opponent in those games; \"top six among themselves\" is "
              f"both sides of the {peer_fp['games'] if peer_fp else 0} most recent games between top-six teams.", ""]
    header = ["skill", "measure"]
    for name in fps:
        header += [f"us vs {name}", "them"]
    if peer_fp:
        header.append("top six among themselves")
    lines += ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for cat, measures in CATEGORIES:
        for key, label, higher in measures:
            row = [cat, label]
            for name, (u, t, _) in fps.items():
                uv, tv = u.get(key), t.get(key)
                flag = ""
                if higher is not None and uv is not None and tv is not None:
                    worse = (uv < tv) if higher else (uv > tv)
                    big = abs(uv - tv) >= max(0.2 * max(abs(tv), 1e-9), 0.05 if key.endswith("share") else 1.0)
                    flag = " ⚠" if worse and big else ""
                digits = 2 if key.endswith("share") else 1
                row += [fmt(uv, digits) + flag, fmt(tv, digits)]
            if peer_fp:
                row.append(fmt(peer_fp.get(key), 2 if key.endswith("share") else 1))
            lines.append("| " + " | ".join(row) + " |")
            cat = ""
    lines += ["", "⚠ marks a gap of 20% or more in the direction that hurts us.", ""]

    # 4. loss anatomy
    anat = []
    results = collections.Counter()
    for l, side, opp, v, rp in ours:
        if v not in vset or opp not in TOP6:
            continue
        s = score_of(l, side)
        results["W" if s == 1 else "D" if s == 0.5 else "L"] += 1
        if s != 0.0:
            continue
        try:
            r = json.load(open(rp))
        except Exception:
            continue
        a = loss_anatomy(r, side)
        a["opp"] = opp
        a["id"] = l.get("id")
        a["phase"] = "opening (ply < 30)" if (a.get("ply_minus3") or 999) < 30 else "middlegame (30-69)" if (a.get("ply_minus3") or 999) < 70 else "late (70+) or never 3 down"
        anat.append(a)
    lines += [f"## Loss anatomy: v{version} against the top six", "",
              f"Record {results['W']}-{results['D']}-{results['L']}; {len(anat)} losses analysed.", ""]
    if anat:
        how = collections.Counter(a.get("king_fell", a["reason"]) for a in anat)
        how_t = collections.Counter(a.get("king_fell", a["reason"]) for a in anat if a["opp"] in TARGETS)
        lines += ["**How our king fell**", "", "| ending | all top six | of which duck + Instructors |", "| --- | --- | --- |"]
        for k, c in how.most_common():
            lines.append(f"| {k} | {c} | {how_t.get(k, 0)} |")
        att = collections.Counter(a.get("king_attackers", "") for a in anat if a.get("king_attackers"))
        lines += ["", "Pieces that took our king: " + ", ".join(f"{k or '?'} {c}" for k, c in att.most_common()), ""]
        causes = collections.Counter(a.get("collapse_cause") for a in anat if a.get("collapse_cause"))
        m3 = [a["ply_minus3"] for a in anat if a.get("ply_minus3")]
        m5 = [a["ply_minus5"] for a in anat if a.get("ply_minus5")]
        phases = collections.Counter(a["phase"] for a in anat)
        lines += ["**When the material went** (levels held for four plies, so exchanges are not swings)", "",
                  "- Phase of the collapse: " + ", ".join(f"{k} {c}" for k, c in phases.most_common()) + ".",
                  f"- Down 3 or more at some point in {len(m3)} of {len(anat)} losses; median first ply {statistics.median(m3) if m3 else '–'}.",
                  f"- Down 5 or more in {len(m5)}; median first ply {statistics.median(m5) if m5 else '–'}.",
                  f"- Lost although we had led by 3 or more: {sum(1 for a in anat if a['max_lead'] >= 3)} of {len(anat)}.",
                  f"- Our clock at 15 s or less: {sum(1 for a in anat if a.get('min_clock') is not None and a['min_clock'] <= 15)} of {len(anat)}.",
                  f"- Median length {statistics.median([a['plies'] for a in anat])} plies.", "",
                  "| what put us 3 down | losses |", "| --- | --- |"]
        for k, c in causes.most_common():
            lines.append(f"| {k} | {c} |")
        lines.append("")
    # 5. what worked
    good = [(l, side, opp) for l, side, opp, v, _ in ours if v in vset and opp in TOP6 and score_of(l, side) > 0]
    lines += [f"## What worked: v{version}'s wins and draws against the top six", ""]
    if good:
        lines += ["| id | opponent | us | result | plies | reason |", "| --- | --- | --- | --- | --- | --- |"]
        for l, side, opp in sorted(good, key=lambda x: x[0].get("createdAt", "")):
            lines.append(f"| {l.get('id')} | {opp} | {side[0].upper()} | {'win' if score_of(l, side) == 1 else 'draw'} | {l.get('plies')} | {l.get('reason')} |")
    else:
        lines.append("None yet.")
    lines.append("")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.output}: v{version} vs top six {results['W']}-{results['D']}-{results['L']}")


if __name__ == "__main__":
    main()
