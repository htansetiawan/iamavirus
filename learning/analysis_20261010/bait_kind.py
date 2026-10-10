"""Hidden-cover baits against TA Baselines P and A: take rate by whether the bait gives check, by its piece,
and whether the defender had any other legal move that escaped every visible attacker."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import fen
DEF = {"TA Baseline P", "TA Baseline A"}
S = collections.defaultdict(lambda: [0, 0]); WHO = collections.defaultdict(lambda: collections.Counter())
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if l["createdAt"] < "2026-10-07": continue
    for dcolour in ("white", "black"):
        if l[dcolour] not in DEF: continue
        attacker = l["black"] if dcolour == "white" else l["white"]
        grp = "IAmAVirus" if attacker == "IAmAVirus" else "top six" if attacker in {"duck", "Instructors", "Knight Vision", "Greek Gift", "Decent Chess Bot", "Strongly Invisible"} else None
        if grp is None: continue
        try: r = json.load(open(p.replace("listing.json", "replay.json")))
        except Exception: continue
        F = r["frames"]; dcol = chess.WHITE if dcolour == "white" else chess.BLACK
        for k in range(1, len(F) - 1):
            if ((F[k + 1]["ply"] % 2 == 1) == (dcol == chess.WHITE)) is False: continue
            b = chess.Board(fen(F[k]["board"])); ks = b.king(dcol)
            if ks is None: continue
            view = F[k][dcolour]
            for sq in chess.SquareSet(chess.BB_KING_ATTACKS[ks]):
                pc = b.piece_at(sq)
                if pc is None or pc.color == dcol: continue
                bb = b.copy(stack=False); bb.remove_piece_at(sq); bb.remove_piece_at(ks); bb.set_piece_at(sq, chess.Piece(chess.KING, dcol))
                if not [c for c in bb.attackers(not dcol, sq) if view[c] == "?"]: continue
                check = ks in b.attacks(sq)
                took = F[k + 1]["move"] == chess.square_name(ks) + chess.square_name(sq)
                for key in ((grp, "gives check" if check else "no check"), (grp, "piece " + pc.symbol().upper())):
                    S[key][0] += 1; S[key][1] += took
                WHO[grp]["check" if check else "quiet"] += 1
for key in sorted(S):
    n, t = S[key]
    if n >= 5: print(f"{key[0]:<10} {key[1]:<12} {n:>4} baits, taken {t:>3} = {t / n:5.1%}")
print({g: dict(c) for g, c in WHO.items()})
