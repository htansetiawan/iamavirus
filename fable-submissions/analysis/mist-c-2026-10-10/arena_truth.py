"""At each v26 arena loss's fatal decision: |P|, capped?, rebuilds so far, and the true board's weight share in mist-c's belief."""
import json, os, re, subprocess
V5 = os.path.abspath('builds/mist-c-v5/mist')
for gid in ['7crrql6k', 'zn8m31zt', 'nra5paph', 'jnx42ysn', 'm2zj8p6j']:
    g = json.load(open(f'arena26/{gid}.json')); colour = 'white' if g['white'] == 'IAmAVirus' else 'black'
    events = [e for e in g['protocol']['events'] if e['side'] == colour]
    lines, played = [], []
    for e in events:
        if e['direction'] == 'input': lines.append(e['text'])
        elif e['text'].startswith('move '): played.append(e['text'][5:])
    n = len(played); cl = [i for i, t in enumerate(lines) if re.fullmatch(r'[0-9.]+', t)]
    feed = '\n'.join(lines[:cl[n - 1] + 1]) + '\n'
    env = dict(os.environ, MIST_RISK='1', FOW_SEED='21', MIST_FORCE_MOVES=','.join(played[:n - 1]))
    out = subprocess.run([V5], input=feed, capture_output=True, text=True, env=env, timeout=300).stderr
    P = re.findall(r'\|P\|=(\d+)(\(capped\))?', out)
    reb = len(re.findall(r'rebuilt', out))
    # the true board before our fatal move: frame of the ply where we move
    fr = g['frames']; truth = fr[-2]['board']
    first_capped = next((i for i, (p, c) in enumerate(P) if c), None)
    print(f"{gid}: fatal decision {n}: |P|={P[-1][0]}{' capped' if P[-1][1] else ''}; belief first capped at decision {first_capped + 1 if first_capped is not None else '-'}; rebuilds {reb}; |P| over the last 6 decisions {[int(p) for p, _ in P[-6:]]}")
