"""Replays chosen decisions with several kappa values and reports how often the move changes."""
import concurrent.futures as cf, json, os, re, subprocess, sys, random
MIST = os.path.expanduser('~/git/fowsearch-c/build/mist-k')
B = os.path.expanduser('~/git/iamavirus/data/arena_local/builds/')
rows = json.load(open(sys.argv[1]))
def colour_of(r):
    g = json.load(open(B + r['game']))
    return 'white' if g['white'] == r['us'] else 'black'
deaths = [r for r in rows if r['died'] and r['risk'] > r['least'] + 0.01]
alive = [r for r in rows if not r['died'] and r['risk'] > r['least'] + 0.01]
random.seed(1); alive = random.sample(alive, min(len(alive), 24))
def decide(r, kappa, seed):
    g = json.load(open(B + r['game'])); colour = 'white' if g['white'] == r['us'] else 'black'
    events = [e for e in g['protocol']['events'] if e['side'] == colour]
    lines, played = [], []
    for e in events:
        if e['direction'] == 'input': lines.append(e['text'])
        elif e['text'].startswith('move '):
            played.append(e['text'][5:])
            if len(played) == r['k']: break
    cl = [i for i, t in enumerate(lines) if re.fullmatch(r'[0-9.]+', t)]
    feed = '\n'.join(lines[:cl[r['k'] - 1] + 1]) + '\n'
    env = dict(os.environ, MIST_RISK='1', MIST_MAX_SECONDS='3', FOW_SEED=str(seed), MIST_KING_RISK=str(kappa), MIST_FORCE_MOVES=','.join(played[:r['k'] - 1]))
    out = subprocess.run([MIST], input=feed, capture_output=True, text=True, env=env, timeout=300).stderr
    m = re.search(r'mist: risk (\S+) ([\d.]+) \(chosen\)', out)
    return (m.group(1), float(m.group(2))) if m else (None, None)
jobs = [(r, kappa, seed) for r in deaths + alive for kappa in (1.0, 2.7) for seed in (11, 12)]
with cf.ProcessPoolExecutor(7) as ex:
    res = list(ex.map(decide, *zip(*jobs)))
out = {}
for (r, kappa, seed), (mv, risk) in zip(jobs, res):
    out.setdefault((r['game'], r['k']), {'row': r}).setdefault(kappa, []).append((mv, risk))
for label, group in (('died in the game', deaths), ('survived in the game', alive)):
    print(f'== {label}: {len(group)} decisions')
    changed = {1.0: 0, 2.7: 0}; mean_risk = {1.0: [], 2.7: []}
    for r in group:
        o = out[(r['game'], r['k'])]
        line = []
        for kappa in (1.0, 2.7):
            for mv, risk in o[kappa]:
                changed[kappa] += mv != r['move']; mean_risk[kappa].append(risk if risk is not None else 0)
            line.append(f"k{kappa}: " + ' '.join(f"{mv}({risk:.3f})" for mv, risk in o[kappa]))
        print(f"   {r['game'][:30]:30s} d{r['k']:3d} played {r['move']} risk {r['risk']:.3f} least {r['least']:.3f} | " + ' | '.join(line))
    for kappa in (1.0, 2.7):
        n = len(mean_risk[kappa])
        print(f"   kappa {kappa}: replays choosing another move than the game's {changed[kappa]}/{n}; mean risk of the chosen move {sum(mean_risk[kappa])/max(n,1):.3f}")
