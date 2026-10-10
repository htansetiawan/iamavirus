"""When a team can attack the enemy king from a square the enemy cannot see (a hidden check),
how often does it? Uniform-random would be (number of such moves / legal moves)."""
import collections, glob, json, os, random, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import fen
TEAMS = ["duck", "Instructors", "Knight Vision", "Greek Gift", "Decent Chess Bot", "Strongly Invisible", "Mist Opportunities", "TA Baseline S", "IAmAVirus"]
S = collections.defaultdict(lambda: [0, 0, 0.0])  # chances, taken, uniform expectation
games = collections.defaultdict(list)
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if l["createdAt"] < "2026-10-08": continue
    for T in TEAMS:
        if T in (l["white"], l["black"]): games[T].append((l, p))
rng = random.Random(1)
for T in TEAMS:
    sample = games[T]; rng.shuffle(sample)
    for l, p in sample[:250]:
        try: r = json.load(open(p.replace("listing.json", "replay.json")))
        except Exception: continue
        tw = l["white"] == T; F = r["frames"]
        enemy_view = "black" if tw else "white"
        for k in range(1, len(F)):
            if ((F[k]["ply"] % 2 == 1) == tw) is False: continue
            b = chess.Board(fen(F[k - 1]["board"])); b.turn = chess.WHITE if tw else chess.BLACK
            ek = b.king(not b.turn)
            if ek is None: continue
            seen = F[k - 1][enemy_view]
            hidden_checks = []; n = 0
            for m in b.pseudo_legal_moves:
                n += 1
                if seen[m.to_square] != "?": continue  # the enemy would see the piece arrive
                b.push(m)
                if b.is_attacked_by(not b.turn, ek) and m.to_square != ek: hidden_checks.append(m.uci())
                b.pop()
            if not hidden_checks: continue
            s = S[T]; s[0] += 1; s[1] += F[k]["move"] in hidden_checks; s[2] += len(hidden_checks) / max(1, n)
for T in TEAMS:
    c, t, u = S[T]
    if c: print(f"{T:<20} chances {c:>5}: played a hidden check {t / c:6.1%}  (uniform play {u / c:5.1%}, ratio {t / max(u, 1e-9):4.1f}x)")
