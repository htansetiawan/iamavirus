#!/usr/bin/env python3
"""Daily insights from the mirrored arena games, token-free (run by tools/daily_refresh.sh).

Writes data/reports/daily/insights-<date>.md and insights-latest.md with:
  1. opponents' version changes in the last 7 days and our score against each version
  2. our rating point flow per opponent for the active version (Elo, K = 8), each game
     scored against the latest leaderboard snapshot before it (an approximation of the
     pre-game ratings; snapshots are a few hours apart). Until 26 October the lookup
     compared hyphenated snapshot keys with unhyphenated game keys and always took the
     latest snapshot, so earlier totals are not historical flows.
  3. first queen event per game against a fixed cohort, the 13 October top six
     (lost outright / trades / theirs); the current leaders are listed beside it
  4. king moves per 100 moves by phase, us vs that cohort in the same games, last 3 days
  5. the four-ply king-capture rate after our move by fog lines and phase (the hazard table)
  6. our losses in 20 plies or fewer, with the moves

usage: python -m learning.daily_insights [--raw data/raw] [--out data/reports/daily] [--days 7]
"""
from __future__ import annotations
import argparse, bisect, collections, datetime, glob, json, os, re, statistics, sys
import chess
from learning.move_taxonomy import fen

# A fixed cohort: the leaderboard's top six on 13 October, when the report was designed. Kept
# fixed so sections 3 and 4 compare like with like over time; the current leaders (which may
# differ, e.g. Crimson Fog and Mist Opportunities) are listed in the report next to it.
TOP6 = ["Greek Gift", "Knight Vision", "Strongly Invisible", "Decent Chess Bot", "duck", "Instructors"]
TOP6_LABEL = "the fixed 13 October top six"
VAL = {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
ME = "IAmAVirus"


def fog_lines(view, k):
    n = 0
    for df, dr in DIRS:
        f, r = k % 8 + df, k // 8 + dr
        while 0 <= f < 8 and 0 <= r < 8:
            c = view[r * 8 + f]
            if c == "?":
                n += 1; break
            if c != "-":
                break
            f += df; r += dr
    return n


def mat(b, c):
    return sum(len(b.pieces(t, c)) * v for t, v in VAL.items())


def queen_event(fr, col):
    boards = [chess.Board(fen(x["board"])) for x in fr]
    for k in range(1, len(fr)):
        bp, ba = boards[k - 1], boards[k]
        lo = bool(bp.pieces(chess.QUEEN, col)) and not ba.pieces(chess.QUEEN, col)
        lt = bool(bp.pieces(chess.QUEEN, not col)) and not ba.pieces(chess.QUEEN, not col)
        if lo or lt:
            after = boards[min(k + 2, len(fr) - 1)]
            og = not after.pieces(chess.QUEEN, col); tg = not after.pieces(chess.QUEEN, not col)
            if og and tg:
                return "trade, they took first" if lo else "trade, we took first"
            return "we lose the queen" if lo else "they lose the queen"
    return "no queen event"


def parse_utc(s):
    """UTC instant from a snapshot directory name ('2026-10-25T101243.632817Z0000') or a game's
    createdAt ('2026-10-21T12:00:03.136818998+00:00'). Preserves microseconds,
    normalizes offsets, and returns None for invalid or timezone-naive input."""
    if not isinstance(s, str):
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{6}(?:\.\d+)?Z0000", s):
        s = s[:-5] + "+00:00"
    try:
        parsed = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return parsed.astimezone(datetime.timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def rating_before(series, t):
    """The (time, rating) of the latest snapshot strictly before t, or None when no snapshot
    precedes it. series: sorted [(datetime, rating)]."""
    if t is None:
        return None
    i = bisect.bisect_left(series, (t,))
    return series[i - 1] if i > 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw"); ap.add_argument("--out", default="data/reports/daily")
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    cut7 = now - datetime.timedelta(days=args.days)
    cut3 = now - datetime.timedelta(days=3)
    snaps = sorted(glob.glob(os.path.join(args.raw, "snapshots", "*", "leaderboard.json")))
    ts = collections.defaultdict(list); active = {}; latest_t = None; latest_rows = []
    t0 = now - datetime.timedelta(days=args.days + 2)   # snapshots from before the window, for the first games
    for p in snaps:
        t = parse_utc(p.split("/")[-2])
        if t is None or t < t0 or t > now:
            continue
        try:
            d = json.load(open(p))
        except Exception:
            continue
        rows = d["leaderboard"]["players"] if isinstance(d["leaderboard"], dict) else d["leaderboard"]
        if latest_t is None or t > latest_t:
            latest_t, latest_rows = t, rows
            active = {r["name"]: r.get("activeVersion") for r in rows}
        for r in rows:
            if r.get("rating") is not None:
                ts[r["name"]].append((t, r["rating"]))
    for k in ts:
        ts[k].sort()
    leaders_now = [r["name"] for r in sorted(
        (r for r in latest_rows if r.get("rating") is not None),
        key=lambda r: -r["rating"]) if r["name"] != ME][:6]

    our_version = active.get(ME)
    listings = []
    for g in glob.glob(os.path.join(args.raw, "games", "*", "listing.json")):
        try:
            r = json.load(open(g))
        except Exception:
            continue
        completed_at = parse_utc(r.get("createdAt"))
        if completed_at is None or not cut7 <= completed_at <= now:
            continue
        r["_completed_at"] = completed_at
        listings.append(r)
    listings.sort(key=lambda r: r["_completed_at"])
    out = [f"# Arena insights, {now.strftime('%Y-%m-%d %H:%M')} UTC", "",
           f"Our active version: v{our_version}. Window: {args.days} days ({len(listings)} games of all teams).", "",
           f"Current leaders at the latest snapshot ({latest_t.strftime('%Y-%m-%d %H:%M') + ' UTC' if latest_t else 'none'}): {', '.join(leaders_now)}. "
           f"Sections 3 and 4 use {TOP6_LABEL} ({', '.join(TOP6)}), kept fixed for comparison over time"
           + (f"; not in today's top six: {', '.join(x for x in TOP6 if x not in leaders_now)}; in today's but not the cohort: {', '.join(x for x in leaders_now if x not in TOP6)}." if set(leaders_now) != set(TOP6) else ".")]

    # 1. version changes
    versions = collections.defaultdict(collections.Counter); ours_by = collections.defaultdict(lambda: [0.0, 0])
    for r in listings:
        for side in ("white", "black"):
            versions[r[side]][r.get(side + "Version")] += 1
        if ME in (r["white"], r["black"]):
            usw = r["white"] == ME; them = r["black"] if usw else r["white"]; tv = r.get("blackVersion" if usw else "whiteVersion")
            s = 1.0 if r["result"] == "1-0" else 0.0 if r["result"] == "0-1" else 0.5; s = s if usw else 1 - s
            ours_by[(them, tv)][0] += s; ours_by[(them, tv)][1] += 1
    out += ["", "## 1. Opponents' versions in the window, and our score against each", "",
            "| opponent | versions seen (games) | our score by version |", "|---|---|---|"]
    for team, c in sorted(versions.items(), key=lambda kv: -sum(kv[1].values())):
        if team == ME or len(c) < 1:
            continue
        ours = ", ".join(f"v{v}: {ours_by[(team, v)][0]:.0f}/{ours_by[(team, v)][1]}" for v in sorted(c, key=lambda x: (x is None, x)) if ours_by[(team, v)][1])
        flag = " **changed**" if len(c) > 1 else ""
        out.append(f"| {team}{flag} | " + ", ".join(f"v{v} ({n})" for v, n in sorted(c.items(), key=lambda kv: (kv[0] is None, kv[0]))) + f" | {ours} |")

    # 2. point flow (active version)
    flow = collections.defaultdict(lambda: [0, 0.0, 0.0]); gaps = []; missing = 0
    for r in listings:
        if ME not in (r["white"], r["black"]):
            continue
        usw = r["white"] == ME
        if r.get("whiteVersion" if usw else "blackVersion") != our_version:
            continue
        them = r["black"] if usw else r["white"]
        t = r["_completed_at"]
        rw = rating_before(ts.get(r["white"], []), t); rb = rating_before(ts.get(r["black"], []), t)
        s = 1.0 if r["result"] == "1-0" else 0.0 if r["result"] == "0-1" else 0.5; s = s if usw else 1 - s
        if rw is None or rb is None:
            missing += 1
            continue
        gaps.append((t - min(rw[0], rb[0])).total_seconds() / 3600)   # age of the older snapshot used
        mine, theirs = (rw[1], rb[1]) if usw else (rb[1], rw[1])
        e = 1 / (1 + 10 ** ((theirs - mine) / 400))
        f = flow[them]; f[0] += 1; f[1] += s; f[2] += s - e
    out += ["", f"## 2. Rating point flow per opponent, v{our_version} (Elo, K = 8; an approximation)", "",
            f"Each game is scored against both players' ratings in the latest leaderboard snapshot before it "
            f"({len(gaps)} games; snapshot age median {statistics.median(gaps) if gaps else 0:.1f} h, max {max(gaps) if gaps else 0:.1f} h; "
            f"{missing} games skipped with no earlier snapshot). Until 26 October this table used the latest snapshot for every game, so earlier totals are not historical flows. "
            f"Cohort: hist = {TOP6_LABEL}, now = today's top six.", "",
            "| opponent | games | score | Elo expects | net points | cohort |", "|---|---|---|---|---|---|"]
    for them, (n, s, se) in sorted(flow.items(), key=lambda kv: kv[1][2]):
        cohort = ", ".join(x for x, ok in (("hist", them in TOP6), ("now", them in leaders_now)) if ok)
        out.append(f"| {them} | {n} | {s/n:.2f} | {(s-se)/n:.2f} | {8*se:+.0f} | {cohort} |")
    out.append(f"| **total** | {sum(v[0] for v in flow.values())} | | | {8*sum(v[2] for v in flow.values()):+.0f} | |")

    # 3-6 need replays: our games of the active version in the last 3 days, and top-six games
    qe = collections.defaultdict(list); km = {"us": collections.Counter(), "them": collections.Counter()}; mv = {"us": collections.Counter(), "them": collections.Counter()}
    haz = collections.defaultdict(lambda: [0, 0]); short = []
    for r in listings:
        if r["_completed_at"] < cut3 or ME not in (r["white"], r["black"]):
            continue
        usw = r["white"] == ME; them = r["black"] if usw else r["white"]
        if r.get("whiteVersion" if usw else "blackVersion") != our_version:
            continue
        try:
            g = json.load(open(os.path.join(args.raw, "games", r["id"], "replay.json")))
        except Exception:
            continue
        fr = g["frames"]; us = "white" if usw else "black"; col = chess.WHITE if usw else chess.BLACK
        s = 1.0 if r["result"] == "1-0" else 0.0 if r["result"] == "0-1" else 0.5; s = s if usw else 1 - s
        if them in TOP6:
            qe[queen_event(fr, col)].append(s)
        lost = s == 0 and g.get("reason") == "King capturable"; end = len(fr) - 1
        if lost and end <= 20:
            short.append((r["id"], them, us, end, " ".join(x["move"] for x in fr[1:])))
        boards = [chess.Board(fen(x["board"])) for x in fr]
        for k in range(1, len(fr)):
            sw = (k % 2 == 1); who = "us" if sw == usw else "them"
            c = chess.WHITE if sw else chess.BLACK
            bp = boards[k - 1]; pc = bp.piece_at(chess.parse_square(fr[k]["move"][:2]))
            np_ = sum(len(bp.pieces(t, not c)) * v for t, v in VAL.items())
            ph = "late" if np_ <= 13 else ("middle" if k >= 30 else "opening")
            if them in TOP6:   # both sides counted from the same games, so the populations match
                mv[who][ph] += 1
                if pc and pc.piece_type == chess.KING:
                    km[who][ph] += 1
            if who == "us":
                bd = boards[k]; ks = bd.king(col)
                if ks is None:
                    continue
                L = min(fog_lines(fr[k][us], ks), 3)
                h = haz[(ph if ph != "opening" else "middle", L)]; h[0] += 1; h[1] += (lost and end - k <= 4)
    n3 = sum(len(v) for v in qe.values())
    out += ["", f"## 3. First queen event against {TOP6_LABEL}, v{our_version}, last 3 days ({n3} games)", "", "| event | games | share | our score |", "|---|---|---|---|"]
    for k, v in sorted(qe.items(), key=lambda kv: -len(kv[1])):
        out.append(f"| {k} | {len(v)} | {100*len(v)/max(1,n3):.0f}% | {sum(v)/len(v):.2f} |")
    out += ["", f"## 4. King moves per 100 moves by phase, last 3 days, in our games against {TOP6_LABEL} (both sides from the same games)", "", "| side | opening | middle | late |", "|---|---|---|---|"]
    for who, name in (("us", "IAmAVirus"), ("them", "the fixed top six")):
        out.append(f"| {name} | " + " | ".join(f"{100*km[who][ph]/max(1,mv[who][ph]):.1f}" for ph in ("opening", "middle", "late")) + " |")
    out += ["", "## 5. Our king captured within four plies of our move, by fog lines from the king (last 3 days)", "", "| phase | 0 lines | 1 | 2 | 3+ |", "|---|---|---|---|---|"]
    for ph in ("middle", "late"):
        out.append(f"| {ph} | " + " | ".join(f"{100*haz[(ph,L)][1]/max(1,haz[(ph,L)][0]):.1f}% of {haz[(ph,L)][0]}" for L in range(4)) + " |")
    out += ["", "## 6. Our losses in 20 plies or fewer, last 3 days", ""]
    out += [f"- {gid} vs {them} as {us}, {plies} plies: `{moves}`" for gid, them, us, plies, moves in short] or ["- none"]
    os.makedirs(args.out, exist_ok=True)
    text = "\n".join(out) + "\n"
    open(os.path.join(args.out, f"insights-{now.strftime('%Y-%m-%d')}.md"), "w").write(text)
    open(os.path.join(args.out, "insights-latest.md"), "w").write(text)
    print(text[:1500])


if __name__ == "__main__":
    sys.exit(main())
