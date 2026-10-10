import json, os, re, subprocess, sys, concurrent.futures as cf
V5 = os.path.abspath('builds/mist-c-v5/mist'); V6 = os.path.expanduser('~/git/fowsearch-c/build/mist')
def decide(gid, binary, kappa, seed):
    g = json.load(open(f'arena26/{gid}.json')); colour = 'white' if g['white'] == 'IAmAVirus' else 'black'
    events = [e for e in g['protocol']['events'] if e['side'] == colour]
    lines, played = [], []
    for e in events:
        if e['direction'] == 'input': lines.append(e['text'])
        elif e['text'].startswith('move '): played.append(e['text'][5:])
    n = len(played)
    cl = [i for i, t in enumerate(lines) if re.fullmatch(r'[0-9.]+', t)]
    feed = '\n'.join(lines[:cl[n - 1] + 1]) + '\n'
    env = dict(os.environ, MIST_RISK='1', FOW_SEED=str(seed), MIST_FORCE_MOVES=','.join(played[:n - 1]))
    if kappa: env['MIST_KING_RISK'] = str(kappa)
    out = subprocess.run([binary], input=feed, capture_output=True, text=True, env=env, timeout=300).stderr
    risks = dict((m, float(r)) for m, r in re.findall(r'mist: risk (\S+) ([\d.]+)', out))
    m = re.search(r'mist: risk (\S+) ([\d.]+) \(chosen\)', out)
    return gid, played[-1], risks.get(played[-1]), min(risks.values()) if risks else None, (m.group(1), float(m.group(2))) if m else None
jobs = [(gid, b, k, s) for gid in ['7crrql6k', 'zn8m31zt', 'nra5paph', 'jnx42ysn', 'm2zj8p6j'] for b, k in ((V5, None), (V6, 2.0), (V6, 2.7)) for s in (21, 22)]
with cf.ProcessPoolExecutor(4) as ex:
    res = list(ex.map(decide, *zip(*jobs)))
rows = {}
for (gid, b, k, s), (g, played, prisk, least, chosen) in zip(jobs, res):
    label = 'v5' if b == V5 else f'v6 k{k}'
    rows.setdefault(gid, [played, prisk, least, {}])[3].setdefault(label, []).append(f"{chosen[0]}({chosen[1]:.3f})" if chosen else '?')
for gid, (played, prisk, least, d) in rows.items():
    print(f"{gid}: fatal move {played} (risk on v5's belief {prisk}), safest {least} | " + ' | '.join(f"{k}: {' '.join(v)}" for k, v in d.items()))
