"""Our king's captures in every arena game: how often the king died on the next ply, by
whether the victim had just arrived and how many open lines lead from the square into the fog."""
import collections, glob, json, os, sys
D8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
KN = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
def fog_lines(view, sq):
    f0, r0 = sq % 8, sq // 8; lines = 0
    for df, dr in D8:
        f, r = f0 + df, r0 + dr
        while 0 <= f < 8 and 0 <= r < 8:
            c = view[r * 8 + f]
            if c == "?": lines += 1; break
            if c != "-": break
            f += df; r += dr
    return lines
def fog_knights(view, sq):
    f0, r0 = sq % 8, sq // 8
    return sum(1 for df, dr in KN if 0 <= f0 + df < 8 and 0 <= r0 + dr < 8 and view[(r0 + dr) * 8 + f0 + df] == "?")
sq = lambda s: (ord(s[0]) - 97) + 8 * (int(s[1]) - 1)
stats = collections.defaultdict(lambda: [0, 0]); quiet = collections.defaultdict(lambda: [0, 0])
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if "IAmAVirus" not in (l["white"], l["black"]): continue
    us_white = l["white"] == "IAmAVirus"; view = "white" if us_white else "black"
    try: r = json.load(open(p.replace("listing.json", "replay.json")))
    except Exception: continue
    F = r["frames"]; N = len(F) - 1; mine = "KQRBNP" if us_white else "kqrbnp"; theirs = "kqrbnp" if us_white else "KQRBNP"
    for k in range(2, N + 1):
        ours = (F[k]["ply"] % 2 == 1) == us_white
        mv = F[k]["move"]
        if not ours or not mv: continue
        before = F[k - 1]["board"]; a, b = sq(mv[:2]), sq(mv[2:4])
        if before[a] != mine[0]: continue  # our king moved
        died = k == N and r.get("reason") == "King capturable"  # the referee ends the game on the move that leaves the king capturable
        v = F[k - 1][view]
        n = fog_lines(v, b); kn = fog_knights(v, b)
        key_lines = "0" if n == 0 else "1" if n == 1 else "2+"
        if before[b] in theirs:
            arrived = F[k - 1]["move"] and sq(F[k - 1]["move"][2:4]) == b
            s = stats[(("victim just arrived" if arrived else "victim was there"), key_lines)]
            s[0] += 1; s[1] += died
        else:
            q = quiet[key_lines]; q[0] += 1; q[1] += died
print("King CAPTURES: died on the very next ply")
for key in sorted(stats): n, d = stats[key]; print(f"  {key[0]:<20} open fog lines {key[1]:<3}: {d:>4} of {n:<5} = {d / n:.0%}")
print("King quiet moves (no capture): died on the very next ply")
for key in sorted(quiet): n, d = quiet[key]; print(f"  open fog lines {key:<3}: {d:>4} of {n:<6} = {d / n:.1%}")
