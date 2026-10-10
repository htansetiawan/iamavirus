"""For every mist-c game: replay our side with all moves forced and MIST_RISK, and compare the
belief's estimated king risk of each played move with what happened (the game ended on it)."""
import concurrent.futures as cf, glob, json, os, re, subprocess, sys
MIST = os.environ.get('MIST_BIN', os.path.expanduser('~/git/fowsearch-c/build/mist'))
def run(path):
    g = json.load(open(path))
    out = []
    for colour in ('white', 'black'):
        if not g[colour].startswith('mist-c'): continue
        opp = g['black' if colour == 'white' else 'white']
        events = [e for e in g['protocol']['events'] if e['side'] == colour]
        lines, played = [], []
        for e in events:
            if e['direction'] == 'input': lines.append(e['text'])
            elif e['text'].startswith('move '): played.append(e['text'][5:])
        clock_lines = [i for i, t in enumerate(lines) if re.fullmatch(r'[0-9.]+', t)]
        n = min(len(played), len(clock_lines))
        if n == 0: continue
        feed = '\n'.join(lines[:clock_lines[n - 1] + 1]) + '\n'
        env = dict(os.environ, MIST_RISK='1', FOW_SEED='7', MIST_FORCE_MOVES=','.join(played[:n]))
        r = subprocess.run([MIST], input=feed, capture_output=True, text=True, env=env, timeout=900)
        rows = re.findall(r'mist: played (\S+) risk ([\d.]+) least ([\d.]+) \|P\|=(\d+)(\(capped\))?', r.stderr)
        lost_by_king = g['reason'] == 'King capturable' and ((g['result'] == '0-1') == (colour == 'white'))
        for k, (mv, risk, least, P, capped) in enumerate(rows):
            last = k == n - 1 and n == len(played)
            out.append({'game': path.split('/')[-1], 'us': g[colour], 'opp': opp, 'k': k + 1, 'move': mv, 'risk': float(risk),
                        'least': float(least), 'P': int(P), 'capped': bool(capped), 'died': int(last and lost_by_king)})
    return out
paths = sorted(glob.glob(os.path.expanduser('~/git/iamavirus/data/arena_local/builds/mistc[34]-*.json')))
rows = []
with cf.ProcessPoolExecutor(6) as ex:
    for res in ex.map(run, paths): rows += res
json.dump(rows, open(sys.argv[1], 'w'))
print(len(paths), 'games', len(rows), 'decisions')
