"""Per-move determinism of each team's CURRENT arena version: among exact move histories that
occurred 2+ times with that version to move, the share answered identically every time."""
import collections, glob, json, os, sys
TEAMS = sys.argv[1:] or ["Knight Vision", "Greek Gift", "Decent Chess Bot", "Strongly Invisible", "duck", "Instructors"]
rows = collections.defaultdict(list)
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    for T in TEAMS:
        if T in (l["white"], l["black"]):
            v = l["whiteVersion"] if l["white"] == T else l["blackVersion"]
            rows[T].append((l["createdAt"], v, l, p))
for T in TEAMS:
    rs = sorted(rows[T]); cur = rs[-1][1]
    mine = [x for x in rs if x[1] == cur]
    first, last = mine[0][0][:16], mine[-1][0][:16]
    replies = collections.defaultdict(collections.Counter); losses = 0
    for _, v, l, p in mine:
        try: r = json.load(open(p.replace("listing.json", "replay.json")))
        except Exception: continue
        col = 0 if l["white"] == T else 1
        mv = tuple(f["move"] for f in r["frames"][1:])
        for k in range(col, len(mv), 2): replies[(col, mv[:k])][mv[k]] += 1
        losses += l["result"] == ("0-1" if col == 0 else "1-0")
    out = []
    for lo, hi in ((0, 3), (3, 6), (6, 12), (12, 99)):
        same = tot = 0
        for (col, h), c in replies.items():
            d = len(h) // 2
            if lo <= d < hi and sum(c.values()) >= 2: tot += 1; same += len(c) == 1
        out.append(f"moves {lo + 1}-{hi if hi < 99 else '+'}: {same}/{tot}" + (f" ({same / tot:.0%})" if tot else ""))
    print(f"{T} v{cur}: {len(mine)} games {first}..{last}, {losses} losses; identical answers " + "; ".join(out))
