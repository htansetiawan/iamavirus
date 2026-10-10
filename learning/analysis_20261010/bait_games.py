"""Games where TEAM's king took bait and died: the last plies from the winner's side, and the setup."""
import glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.top6_report import loss_anatomy
from learning.move_taxonomy import fen, material
T = sys.argv[1]
for p in sorted(glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json"))):
    l = json.load(open(p))
    if T not in (l["white"], l["black"]): continue
    tw = l["white"] == T
    if l["result"] != ("0-1" if tw else "1-0"): continue
    r = json.load(open(p.replace("listing.json", "replay.json")))
    a = loss_anatomy(r, "white" if tw else "black")
    if "bait" not in a.get("king_fell", ""): continue
    F = r["frames"]; N = len(F) - 1
    winner = l["black"] if tw else l["white"]
    b = chess.Board(fen(F[N - 1]["board"]))
    last = F[N]["move"]; bait_sq = chess.parse_square(last[2:4])
    victim = b.piece_at(bait_sq)
    after = chess.Board(fen(F[N]["board"])); k = after.king(chess.WHITE if tw else chess.BLACK)
    att = [chess.square_name(s) + after.piece_at(s).symbol() for s in after.attackers(chess.BLACK if tw else chess.WHITE, k)]
    # when did the bait arrive, and was it a capture or a quiet offer?
    k_bait = max(i for i in range(1, N) if F[i]["move"][2:4] == last[2:4])
    prev = chess.Board(fen(F[k_bait - 1]["board"])); bm = F[k_bait]["move"]
    took = prev.piece_at(chess.parse_square(bm[2:4]))
    print(f"{l['id']} {T} {'W' if tw else 'B'} lost to {winner} in {N} plies: {T}'s king took {victim.symbol() if victim else '?'} on {last[2:4]} "
          f"(bait arrived ply {k_bait} by {bm}{' capturing ' + took.symbol() if took else ', a quiet offer'}); killed by {', '.join(att)}; "
          f"material before the bait {material(F[k_bait - 1]['board'], 0 if tw else 1) - material(F[k_bait - 1]['board'], 1 if tw else 0):+d} for {T}")
