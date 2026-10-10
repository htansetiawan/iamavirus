"""Every IAmAVirus game against duck: record by version, and how each loss went."""
import collections, glob, json, os, sys
import chess
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.top6_report import loss_anatomy
from learning.move_taxonomy import fen, material
from learning.suntzu_windows import shelter, SHELTERS

OPP = sys.argv[1] if len(sys.argv) > 1 else "duck"
rows = []
for p in glob.glob(os.path.expanduser("~/git/iamavirus/data/raw/games/*/listing.json")):
    try: l = json.load(open(p))
    except Exception: continue
    if {l["white"], l["black"]} != {"IAmAVirus", OPP}: continue
    us_white = l["white"] == "IAmAVirus"
    res = l["result"]
    s = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == us_white else 0.0)
    rows.append((l["createdAt"], l["id"], us_white, l["whiteVersion"] if us_white else l["blackVersion"], s, l))
rows.sort()
by_v = collections.defaultdict(lambda: [0, 0, 0])
for _, _, _, v, s, _ in rows:
    by_v[v][0 if s == 1 else 1 if s == 0.5 else 2] += 1
print(f"{OPP}: {len(rows)} games;", ", ".join(f"v{v} {w}-{d}-{l}" for v, (w, d, l) in sorted(by_v.items())))
fell = collections.Counter(); killers = collections.Counter(); causes = collections.Counter(); phase = collections.Counter()
our_shelter_end = collections.Counter(); led = 0; clock_low = 0
print("\nid        v  side plies  -3@   -5@  maxlead  how the king fell                                        killer  our king  shelter")
for _, gid, us_white, v, s, l in rows:
    if s != 0.0: continue
    rp = os.path.expanduser(f"~/git/iamavirus/data/raw/games/{gid}/replay.json")
    try: r = json.load(open(rp))
    except Exception: continue
    a = loss_anatomy(r, "white" if us_white else "black")
    frames = r["frames"]
    b = chess.Board(fen(frames[-2]["board"])) if len(frames) > 1 else chess.Board()
    ucol = chess.WHITE if us_white else chess.BLACK
    k = b.king(ucol)
    ksq = chess.square_name(k) if k is not None else "-"
    sh = SHELTERS[shelter(b, ucol)]
    our_shelter_end[sh] += 1
    fell[a.get("king_fell", a["reason"])] += 1; killers[a.get("king_attackers", "?")] += 1
    causes[a.get("collapse_cause", "none")] += 1
    m3 = a.get("ply_minus3")
    phase["opening <30" if m3 and m3 < 30 else "middlegame 30-69" if m3 and m3 < 70 else "late 70+ or never"] += 1
    led += a["max_lead"] >= 3
    clock_low += (a.get("min_clock") or 99) <= 15
    print(f"{gid}  {v:<2} {'W' if us_white else 'B'}    {a['plies']:<5}  {str(m3):<5} {str(a.get('ply_minus5')):<5} {a['max_lead']:+.0f}      {a.get('king_fell', a['reason'])[:56]:<56} {a.get('king_attackers', ''):<6}  {ksq:<8}  {sh}")
n = sum(fell.values())
print(f"\n{n} losses. King fell: {dict(fell)}\nKiller pieces: {dict(killers)}\nWhat put us 3 down: {dict(causes.most_common(8))}\nPhase of the collapse: {dict(phase)}\nOur shelter just before the end: {dict(our_shelter_end)}\nLost after leading by 3+: {led}; clock at 15 s or less: {clock_low}")
