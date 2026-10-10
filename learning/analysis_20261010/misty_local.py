"""Local games against the real Misty: our engine's score at each logged decision vs the true
material balance, and how the game ended."""
import glob, json, os, re, sys, statistics
sys.path.insert(0, os.path.expanduser("~/git/iamavirus"))
from learning.move_taxonomy import material
from learning.top6_report import loss_anatomy
files = sorted(glob.glob(os.path.expanduser("~/git/iamavirus/data/arena_local/builds/*-vs-misty-p*.json")))
gaps_loss, gaps_win = [], []
for f in files:
    g = json.load(open(f)); name = os.path.basename(f)
    us = "white" if "iamavirus" in g["white"] else "black"; U = 0 if us == "white" else 1
    res = g["result"]; s = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == (us == "white") else 0.0)
    diag = g.get("privateDiagnostics", {}).get(us, "")
    frames = g["frames"]; N = len(frames) - 1
    pts = []
    for line in diag.splitlines():
        m = re.search(r"\bn=(\d+)\b.*?\bscore=(-?\d+).*?\bmove=(\S+)", line)
        if not m: continue
        n, score, mv = int(m.group(1)), int(m.group(2)), m.group(3)
        ply = 2 * n - 1 if us == "white" else 2 * n
        if ply > N: continue
        md = material(frames[ply - 1]["board"], U) - material(frames[ply - 1]["board"], 1 - U)
        pts.append((ply, score, md, frames[ply]["move"] == mv))
    a = loss_anatomy(g, us) if s == 0.0 else {}
    if pts:
        gap = statistics.mean(sc / 100 - md for _, sc, md, _ in pts if abs(sc) < 5000)
        (gaps_loss if s == 0 else gaps_win).append(gap)
        first = pts[0]; last = pts[-1]
        print(f"{name[:34]:<34} {us[0].upper()} {s:<3} {N:>3} plies | logged plies {first[0]}-{last[0]}: engine score minus true material, mean {gap:+5.1f} pawns; "
              f"at the end engine {last[1] / 100:+.1f} vs true {last[2]:+d} | {a.get('collapse_cause', '')[:40]} {a.get('king_fell', '')[:40]}")
print(f"\nmean (engine score - true material): losses {statistics.mean(gaps_loss):+.2f} pawns over {len(gaps_loss)} games; wins/draws {statistics.mean(gaps_win) if gaps_win else float('nan'):+.2f} over {len(gaps_win)}")
