"""King moves onto squares with open lines into the fog: immediate death rate by engine era,
split into voluntary moves (king not attacked by any piece we could see) and forced ones."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.dirname(__file__))
from king_bait import fog_lines, sq
def era(v): return "v20-v23" if v >= 20 else "v16-v19" if v >= 16 else "v4-v15"
def visible_board(view, us_white):
    b = chess.Board(None)
    for i, c in enumerate(view):
        if c not in "?-": b.set_piece_at(i, chess.Piece.from_symbol(c))
    b.turn = chess.WHITE if us_white else chess.BLACK
    return b
S = collections.defaultdict(lambda: [0, 0]); losses = collections.Counter(); games = collections.Counter()
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if "IAmAVirus" not in (l["white"], l["black"]): continue
    us_white = l["white"] == "IAmAVirus"; view = "white" if us_white else "black"
    E = era(l["whiteVersion"] if us_white else l["blackVersion"])
    lost = l["result"] == ("0-1" if us_white else "1-0"); games[E] += 1; losses[E] += lost
    try: r = json.load(open(p.replace("listing.json", "replay.json")))
    except Exception: continue
    F = r["frames"]; N = len(F) - 1; K = "K" if us_white else "k"; ucol = chess.WHITE if us_white else chess.BLACK
    for k in range(2, N + 1):
        if not ((F[k]["ply"] % 2 == 1) == us_white) or not F[k]["move"]: continue
        mv = F[k]["move"]; a, b = sq(mv[:2]), sq(mv[2:4])
        if F[k - 1]["board"][a] != K: continue
        v = F[k - 1][view]; n = fog_lines(v, b)
        vb = visible_board(v, us_white)
        forced = bool(vb.attackers(not ucol, a))
        cap = F[k - 1]["board"][b] != "-"
        died = k == N and r.get("reason") == "King capturable"
        key = (E, "capture" if cap else "quiet", "forced" if forced else "voluntary", "0" if n == 0 else "1" if n == 1 else "2+")
        S[key][0] += 1; S[key][1] += died
for E in ("v4-v15", "v16-v19", "v20-v23"):
    print(f"== {E}: {games[E]} games, {losses[E]} losses")
    tot = 0
    for key in sorted(k for k in S if k[0] == E):
        n, d = S[key]; tot += d
        if n >= 10 or d: print(f"   king {key[1]:<7} {key[2]:<9} open fog lines {key[3]:<3}: died next ply {d:>4} of {n:<5} = {d / n:5.1%}")
    print(f"   king deaths on our own king move: {tot} = {tot / max(1, losses[E]):.0%} of the era's losses")
