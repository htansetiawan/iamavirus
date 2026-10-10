"""Take rate of hidden-cover baits next to the king, by defender class x (gives check?) x bait piece,
weighted afterwards by how often we meet each class. Feeds the engine's bait probability table."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import fen
TA = {"TA Baseline P", "TA Baseline A", "TA Baseline S"}; TOP = {"duck", "Instructors", "Knight Vision", "Greek Gift", "Decent Chess Bot", "Strongly Invisible"}
def cls(t): return "TA" if t in TA else "top six" if t in TOP else "Mist" if t.startswith("Mist") else "rest"
S = collections.defaultdict(lambda: [0, 0])
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if l["createdAt"] < "2026-10-07": continue
    try: r = json.load(open(p.replace("listing.json", "replay.json")))
    except Exception: continue
    F = r["frames"]
    for dcolour in ("white", "black"):
        c = cls(l[dcolour]); dcol = chess.WHITE if dcolour == "white" else chess.BLACK
        if l[dcolour] == "IAmAVirus": continue
        for k in range(1, len(F) - 1):
            if ((F[k + 1]["ply"] % 2 == 1) == (dcol == chess.WHITE)) is False: continue
            b = chess.Board(fen(F[k]["board"])); ks = b.king(dcol)
            if ks is None: continue
            view = F[k][dcolour]
            for sq in chess.SquareSet(chess.BB_KING_ATTACKS[ks]):
                pc = b.piece_at(sq)
                if pc is None or pc.color == dcol or pc.piece_type == chess.KING: continue
                bb = b.copy(stack=False); bb.remove_piece_at(sq); bb.remove_piece_at(ks); bb.set_piece_at(sq, chess.Piece(chess.KING, dcol))
                if not [x for x in bb.attackers(not dcol, sq) if view[x] == "?"]: continue
                key = (c, "check" if ks in b.attacks(sq) else "quiet", "QRBNP"[[5, 4, 3, 2, 1].index(pc.piece_type)])
                S[key][0] += 1; S[key][1] += F[k + 1]["move"] == chess.square_name(ks) + chess.square_name(sq)
mix = {"TA": 0.40, "top six": 0.35, "Mist": 0.12, "rest": 0.13}  # roughly our recent opponent mix
print("class     kind   piece   baits  taken")
for key in sorted(S):
    n, t = S[key]
    if n >= 8: print(f"{key[0]:<9} {key[1]:<6} {key[2]:<5} {n:>6} {t / n:6.1%}")
print("\nmix-weighted take rate (TA .40, top six .35, Mist .12, rest .13):")
for kind in ("check", "quiet"):
    for piece in "QRBNP":
        num = den = 0.0
        for c, wgt in mix.items():
            n, t = S[(c, kind, piece)]
            if n >= 8: num += wgt * t / n; den += wgt
        if den: print(f"  {kind:<6} {piece}: {num / den:5.1%}")
