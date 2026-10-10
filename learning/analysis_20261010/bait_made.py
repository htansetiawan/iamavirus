"""Hidden-cover baits CREATED, by attacking team, against a set of defenders: per game, and how many the
defender's king took. A bait: after the attacker's move, one of its pieces stands next to the defender's
king, the king can take it, and the square stays covered by an attacker piece the defender cannot see."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import fen
DEF = set(sys.argv[1].split(","))
A = collections.defaultdict(lambda: [0, 0, 0, 0])  # games, baits, taken, games won
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if l["createdAt"] < "2026-10-07": continue
    for dcolour in ("white", "black"):
        if l[dcolour] not in DEF: continue
        attacker = l["black"] if dcolour == "white" else l["white"]
        try: r = json.load(open(p.replace("listing.json", "replay.json")))
        except Exception: continue
        F = r["frames"]; dcol = chess.WHITE if dcolour == "white" else chess.BLACK
        a = A[attacker]; a[0] += 1
        a[3] += l["result"] == ("0-1" if dcolour == "white" else "1-0")
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
                a[1] += 1; a[2] += F[k + 1]["move"] == chess.square_name(ks) + chess.square_name(sq)
print(f"defenders: {sorted(DEF)}")
for t, (g, n, took, won) in sorted(A.items(), key=lambda kv: -kv[1][0]):
    if g >= 30: print(f"  {t:<20} {g:>5} games, wins {won / g:5.1%}; baits per game {n / g:5.2f}; taken {took:>4} ({took / max(n, 1):5.1%}); games won by a taken bait ~{took / g:5.1%}")
