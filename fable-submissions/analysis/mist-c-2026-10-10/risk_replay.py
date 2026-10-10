import json, os, re, subprocess, sys
MIST = os.environ.get('MIST_BIN', os.path.expanduser('~/git/fowsearch-c/build/mist'))
def feed_for(game, colour, n):
    events = [e for e in game['protocol']['events'] if e['side'] == colour]
    lines, played = [], []
    for e in events:
        if e['direction'] == 'input': lines.append(e['text'])
        elif e['text'].startswith('move '):
            played.append(e['text'][5:])
            if len(played) == n: break
    clock_lines = [i for i, t in enumerate(lines) if re.fullmatch(r'[0-9.]+', t)]
    return '\n'.join(lines[:clock_lines[n - 1] + 1]) + '\n', played
for spec in sys.argv[1:]:
    path, colour, n = spec.split(':'); n = int(n)
    game = json.load(open(path))
    feed, played = feed_for(game, colour, n)
    env = dict(os.environ, MIST_RISK='1', MIST_MAX_SECONDS='3', FOW_SEED='7', MIST_FORCE_MOVES=','.join(played[:n-1]))
    out = subprocess.run([MIST], input=feed, capture_output=True, text=True, env=env, timeout=120)
    risks = {}
    chosen = None
    for l in out.stderr.splitlines():
        m = re.match(r'mist: risk (\S+) ([\d.]+)( \(chosen\))?', l)
        if m:
            risks[m.group(1)] = float(m.group(2))
            if m.group(3): chosen = m.group(1)
        elif l.startswith('mist: n='): summary = l
    print(f"== {path.split('/')[-1]} {colour} decision {n}: game played {played[n-1]} (risk {risks.get(played[n-1])}), replay chose {chosen} (risk {risks.get(chosen)})")
    print('   ', summary[:160])
    safe = sorted(risks.items(), key=lambda kv: kv[1])
    print('    lowest risk:', ', '.join(f'{k} {v:.3f}' for k, v in safe[:6]), '| moves with risk 0:', sum(v == 0 for v in risks.values()), 'of', len(risks))
