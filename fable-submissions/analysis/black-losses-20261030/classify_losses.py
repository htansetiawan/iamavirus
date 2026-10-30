"""Classify every loss of one of our versions by its final blow.
    python3 classify_losses.py STORE.jsonl.gz RAW_GAMES_DIR VERSION OUT.json
The compact store gives the games and versions; the raw replay gives the true boards. Per loss: plies, colour,
opponent, who made the last move (we left the king capturable, or the opponent moved and we stayed capturable),
the pieces attacking our king on the final board, whether we could see the capturer's square at our last
decision and within our last four decisions, the king's file/rank, and the opening (first 4 plies).
"""
import gzip, json, os, sys
from collections import Counter
store, raw, ver, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
def attackers_of(board, target, by_white):
    res = []; tf, tr = target % 8, target // 8
    for s, ch in enumerate(board):
        if ch == '-' or ch.isupper() != by_white: continue
        f, r = s % 8, s // 8; df, dr = tf - f, tr - r; p = ch.upper(); hit = False
        if p == 'P': hit = (dr == (1 if by_white else -1)) and abs(df) == 1
        elif p == 'N': hit = (abs(df), abs(dr)) in ((1, 2), (2, 1))
        elif p == 'K': hit = max(abs(df), abs(dr)) == 1
        else:
            dirs = ([(1,1),(1,-1),(-1,1),(-1,-1)] if p in 'BQ' else []) + ([(1,0),(-1,0),(0,1),(0,-1)] if p in 'RQ' else [])
            for dx, dy in dirs:
                x, y = f + dx, r + dy
                while 0 <= x < 8 and 0 <= y < 8:
                    if (x, y) == (tf, tr): hit = True; break
                    if board[y*8+x] != '-': break
                    x += dx; y += dy
                if hit: break
        if hit: res.append((ch, s))
    return res
sqname = lambda s: 'abcdefgh'[s % 8] + str(s // 8 + 1)
rows = []; n_games = 0; missing = 0
for line in gzip.open(store, 'rt'):
    if '"IAmAVirus"' not in line: continue
    g = json.loads(line); usw = g['white'] == 'IAmAVirus'
    if (g['wver'] if usw else g['bver']) != ver: continue
    n_games += 1; res = g['result']
    if res == '1/2-1/2' or (res == '1-0') == usw: continue
    rec = {'id': g['id'], 'opp': g['black'] if usw else g['white'], 'colour': 'W' if usw else 'B', 'plies': g['plies'], 'reason': g['reason'], 'opening': ' '.join(g['moves'][:4]), 'created': g['created']}
    p = os.path.join(raw, g['id'], 'replay.json')
    if g['reason'] == 'King capturable' and os.path.exists(p):
        f = json.load(open(p))['frames']; side = 'white' if usw else 'black'
        last = len(f) - 1; last_by_us = ((last % 2 == 1) == usw)
        rec['kind'] = 'own move left king capturable' if last_by_us else 'opponent moved; king capturable'
        final = f[-1]['board']; ks = final.find('K' if usw else 'k')
        att = attackers_of(final, ks, not usw) if ks >= 0 else []
        rec['king'] = sqname(ks) if ks >= 0 else None
        rec['attackers'] = [ch.upper() + '@' + sqname(s) for ch, s in att]
        our_last = last if last_by_us else last - 1          # ply index of our last move
        o_dec = f[our_last - 1][side]                         # what we saw when deciding it
        rec['capturer_seen_at_decision'] = any(o_dec[s] != '?' for ch, s in att) if att else None
        win = [f[i][side] for i in range(max(0, our_last - 8), our_last) if (i % 2 == 1) == usw]
        rec['capturer_square_seen_in_last_4'] = any(o[s] != '?' for o in win for ch, s in att) if att else None
        rec['last_move'] = f[last]['move']; rec['our_last_move'] = f[our_last]['move']
        rec['think_last'] = round((f[our_last-1]['clocks'][0 if usw else 1] - f[our_last]['clocks'][0 if usw else 1] + 2), 1)
    elif g['reason'] == 'King capturable': missing += 1
    rows.append(rec)
json.dump({'version': ver, 'games': n_games, 'losses': len(rows), 'rows': rows}, open(out, 'w'))
kc = [r for r in rows if 'attackers' in r]
print('games', n_games, 'losses', len(rows), 'king-capturable with replay', len(kc), 'missing replays', missing, 'other reasons', Counter(r['reason'] for r in rows if r['reason'] != 'King capturable'))
for col in ('B', 'W'):
    k = [r for r in kc if r['colour'] == col]
    print(f'\n== {col}: {len(k)} losses; kind', Counter(r['kind'] for r in k))
    print('  plies <=30 / 31-60 / >60:', sum(1 for r in k if r['plies'] <= 30), sum(1 for r in k if 30 < r['plies'] <= 60), sum(1 for r in k if r['plies'] > 60))
    print('  capturer piece:', Counter(a[0] for r in k for a in r['attackers'][:1]))
    print('  capturer seen at decision:', Counter(r['capturer_seen_at_decision'] for r in k), '| its square seen in last 4 own obs:', Counter(r['capturer_square_seen_in_last_4'] for r in k))
    print('  king square:', Counter(r['king'] for r in k).most_common(8))
    print('  by opponent:', Counter(r['opp'] for r in k).most_common(9))
    print('  openings:', Counter(r['opening'] for r in k).most_common(6))
    print('  unseen capturer by piece:', Counter(a[0] for r in k if r['capturer_seen_at_decision'] is False for a in r['attackers'][:1]))
