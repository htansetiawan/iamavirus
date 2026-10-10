"""Hidden-cover bait, by defending team: after the attacker's move, a piece of the attacker stands next to the
defender's king, the king can take it, and the square is covered by an attacker piece the defender cannot see.
How often does the defender's king take it (and lose)?"""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import fen
TEAMS = ["Mist Opportunities", "duck", "Instructors", "Knight Vision", "Greek Gift", "Decent Chess Bot", "Strongly Invisible", "TA Baseline P", "TA Baseline A", "TA Baseline S", "IAmAVirus"]
S = collections.defaultdict(lambda: [0, 0])
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if l["createdAt"] < "2026-10-07": continue
    sides = [(c, l[c]) for c in ("white", "black") if l[c] in TEAMS]
    if not sides: continue
    try: r = json.load(open(p.replace("listing.json", "replay.json")))
    except Exception: continue
    F = r["frames"]
    for colour, team in sides:
        dcol = chess.WHITE if colour == "white" else chess.BLACK
        for k in range(1, len(F) - 1):
            # position after the attacker's move k, defender to move at k+1
            if ((F[k + 1]["ply"] % 2 == 1) == (dcol == chess.WHITE)) is False: continue
            b = chess.Board(fen(F[k]["board"])); b.turn = dcol
            ks = b.king(dcol)
            if ks is None: continue
            view = F[k][colour]
            for sq in chess.SquareSet(chess.BB_KING_ATTACKS[ks]):
                pc = b.piece_at(sq)
                if pc is None or pc.color == dcol: continue
                # after Kx sq, is sq attacked by an attacker piece the defender does not see now?
                bb = b.copy(stack=False); bb.remove_piece_at(sq); bb.remove_piece_at(ks); bb.set_piece_at(sq, chess.Piece(chess.KING, dcol))
                cover = [c for c in bb.attackers(not dcol, sq) if view[c] == "?"]
                if not cover: continue
                S[team][0] += 1
                S[team][1] += F[k + 1]["move"] == chess.square_name(ks) + chess.square_name(sq)
for t in TEAMS:
    n, took = S[t]
    if n: print(f"{t:<20} hidden-cover baits faced {n:>5}; king took it {took:>4} = {took / n:6.1%}")
