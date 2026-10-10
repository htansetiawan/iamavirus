"""In our games: at our turn, was a covered check-bait available (our move puts a piece next to the enemy king,
giving check, the enemy king can take it, and another piece of ours covers the square from where the enemy
will not see it after our move)? Did we play one? By opponent class, v20-v24."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import fen
TA = {"TA Baseline P", "TA Baseline A", "TA Baseline S"}; TOP = {"duck", "Instructors", "Knight Vision", "Greek Gift", "Decent Chess Bot", "Strongly Invisible"}
S = collections.defaultdict(lambda: [0, 0, 0, 0, 0])  # games, decisions with a bait available, played one, queen-bait available, played queen bait
def baits(b, us, them_view_after):
    out = []
    ek = b.king(not us)
    if ek is None: return out
    for m in b.pseudo_legal_moves:
        if chess.square_distance(m.to_square, ek) != 1: continue
        b.push(m)
        mover = b.piece_at(m.to_square)
        gives_check = ek in b.attacks(m.to_square)
        if gives_check and b.king(us) is not None and not b.is_attacked_by(not us, b.king(us)):
            bb = b.copy(stack=False); bb.remove_piece_at(ek); bb.remove_piece_at(m.to_square); bb.set_piece_at(m.to_square, chess.Piece(chess.KING, not us))
            cover = [c for c in bb.attackers(us, m.to_square)]
            if cover: out.append((m, mover.piece_type, cover))
        b.pop()
    return out
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if "IAmAVirus" not in (l["white"], l["black"]): continue
    w = l["white"] == "IAmAVirus"; v = l["whiteVersion"] if w else l["blackVersion"]
    if not v or v < 20: continue
    opp = l["black"] if w else l["white"]
    cls = "TA" if opp in TA else "top six" if opp in TOP else "Mist" if opp.startswith("Mist") else "rest"
    try: r = json.load(open(p.replace("listing.json", "replay.json")))
    except Exception: continue
    F = r["frames"]; us = chess.WHITE if w else chess.BLACK; them = "black" if w else "white"
    s = S[cls]; s[0] += 1
    for k in range(1, len(F)):
        if ((F[k]["ply"] % 2 == 1) == w) is False: continue
        b = chess.Board(fen(F[k - 1]["board"])); b.turn = us
        bs = baits(b, us, None)
        if not bs: continue
        # the cover must be unseen by the enemy after the move: approximate with the enemy view after our actual move
        # is not possible for unplayed moves, so require the cover square to be unseen in the enemy's current view
        view = F[k - 1][them]
        bs = [(m, pt, [c for c in cov if view[c] == "?"]) for m, pt, cov in bs]
        bs = [(m, pt) for m, pt, cov in bs if cov]
        if not bs: continue
        s[1] += 1; played = F[k]["move"] in {m.uci() for m, _ in bs}; s[2] += played
        q = [m for m, pt in bs if pt == chess.QUEEN]
        if q: s[3] += 1; s[4] += F[k]["move"] in {m.uci() for m in q}
for c, (g, n, pl, nq, plq) in S.items():
    print(f"{c:<8} {g:>4} games: decisions with a covered check-bait available {n:>4} ({n / g:.2f}/game), played {pl} ({pl / max(n, 1):.0%}); "
          f"with a QUEEN check-bait {nq} ({nq / g:.2f}/game), played {plq} ({plq / max(nq, 1):.0%})")
