"""Black conversion lane, step 3: replay the decision that allowed each loss's reversal through mist-c and classify it.
    MIST_BIN=... MIST_STOCKFISH=... MIST_HISTORY_TABLE=... python3 replay_classify.py matched-set.json RAW_GAMES_DIR OUT.json [seeds] [seconds]
Classes: (a) truth absent from P; (b) truth present, share < 1%, not sampled; (c) share >= 1%, not sampled;
(d) truth sampled, engine's move still loses material on the true board (one-ply exchange check) or is the game's move;
(e) truth sampled, engine's move keeps the material (seed noise in the recorded game).
When the truth was never sampled on any seed, classes (b)/(c) apply; sampled on at least one seed -> (d)/(e) by that
seed's move. The record keeps every seed's move and verdict.
"""
import json, os, re, subprocess, sys
VAL = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 100}
sqi = lambda n: (ord(n[0]) - 97) + 8 * (int(n[1]) - 1)
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
        if hit: res.append((ch, s))
    return res
def apply(board, uci):
    b = list(board); f, t = sqi(uci[:2]), sqi(uci[2:4]); piece = b[f]
    if piece == '-': return None
    b[t] = piece; b[f] = '-'
    if piece.lower() == 'p' and len(uci) == 5: b[t] = uci[4].upper() if piece.isupper() else uci[4]
    if piece.lower() == 'k' and abs(t - f) == 2:   # castling: move the rook
        rf, rt = (f + 3, f + 1) if t > f else (f - 4, f - 1); b[rt] = b[rf]; b[rf] = '-'
    if piece.lower() == 'p' and (t - f) % 8 != 0 and board[t] == '-':   # en passant
        b[t - 8 if piece.isupper() else t + 8] = '-'
    return ''.join(b)
def loses_material(board_before_our_move, our_uci, we_white=False):
    """one-ply check on the true board: after our move, the opponent's best capture gain (value taken minus the capturer's
    value if we can recapture) >= 2, or our king is capturable"""
    b = apply(board_before_our_move, our_uci)
    if b is None: return None, 'illegal piece'
    ks = b.find('K' if we_white else 'k')
    if ks >= 0 and attackers_of(b, ks, not we_white): return True, 'king capturable'
    best = 0; what = None
    for s, ch in enumerate(b):
        if ch == '-' or ch.isupper() != we_white or ch.lower() == 'k': continue
        for cch, cs in attackers_of(b, s, not we_white):
            after = apply(b, 'abcdefgh'[cs % 8] + str(cs // 8 + 1) + 'abcdefgh'[s % 8] + str(s // 8 + 1))
            recap = attackers_of(after, s, we_white)
            gain = VAL[ch.lower()] - (VAL[cch.lower()] if recap else 0)
            if gain > best: best, what = gain, f"{cch}x{ch}@{'abcdefgh'[s % 8]}{s // 8 + 1}"
    return best >= 2, what
setf, raw, out = sys.argv[1], sys.argv[2], sys.argv[3]; seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 2; secs = sys.argv[5] if len(sys.argv) > 5 else '4'
data = json.load(open(setf)); losses = data['losses']
results = []
for k, r in enumerate(losses):
    f = json.load(open(os.path.join(raw, r['id'], 'replay.json')))['frames']
    q = r['reversal_ply'] if r['reversal_ply'] is not None else len(f) - 1       # king captured while ahead: the final ply
    dec = q - 1 if q % 2 == 1 else q                                              # our decision ply (Black moves on even plies)
    if dec % 2 == 1: dec -= 1
    feed = ['fow', 'b 180 2']; forced = []
    for p in range(dec):
        feed.append(f[p]['black'])
        if p % 2 == 0: continue
        feed.append('%.9f' % f[p]['clocks'][1]); forced.append(f[p + 1]['move'])
    forced = forced[:-1]
    env = dict(os.environ, MIST_FORCE_MOVES=','.join(forced), MIST_MAX_SECONDS=secs, MIST_TRUTH_SEQ=','.join(x['board'] for x in f[:dec]), MIST_PIECE_GUARD='-1')
    board_before = f[dec - 1]['board']; game_move = f[dec]['move']
    game_loses, game_what = loses_material(board_before, game_move)
    rec = {'id': r['id'], 'opp': r['opp'], 'opp_version': r['opp_version'], 'reversal_ply': r['reversal_ply'], 'decision_ply': dec, 'game_move': game_move,
           'game_move_loses': game_loses, 'game_move_how': game_what, 'lost_piece': r.get('lost_piece'), 'capturer': r.get('capturer'), 'seeds': []}
    for s in range(1, seeds + 1):
        env['FOW_SEED'] = str(s)
        try:
            o = subprocess.run([os.environ['MIST_BIN']], input='\n'.join(feed) + '\n', capture_output=True, text=True, env=env, timeout=400)
        except subprocess.TimeoutExpired:
            rec['seeds'].append({'seed': s, 'error': 'timeout'}); continue
        err = o.stderr.splitlines(); moves = re.findall(r'^move (\S+)', o.stdout, re.M)
        truth = [l for l in err if l.startswith('mist: truth v=')]; samp = [l for l in err if l.startswith('mist: truth sampled=')]
        decl = [l for l in err if l.startswith('mist: n=')]
        t = truth[-1] if truth else ''; m = re.search(r'share=([0-9.]+) rank=(\d+)', t)
        sm = re.search(r'sampled=(\d+) of (\d+) weight=([0-9.]+)', samp[-1]) if samp else None
        mv = moves[-1] if moves else None
        lose, how = loses_material(board_before, mv) if mv else (None, None)
        rec['seeds'].append({'seed': s, 'move': mv, 'loses': lose, 'how': how, 'truth_lost': 'LOST' in t, 'share': float(m.group(1)) if m else None, 'rank': int(m.group(2)) if m else None,
                             'P': int(re.search(r'\|P\|=(\d+)', t).group(1)) if re.search(r'\|P\|=(\d+)', t) else None,
                             'sampled': int(sm.group(1)) if sm else None, 'K': int(sm.group(2)) if sm else None, 'sampled_weight': float(sm.group(3)) if sm else None,
                             'decision': decl[-1][:160] if decl else None, 'guards': [l for l in err if 'guard left out' in l][-2:]})
    ok = [x for x in rec['seeds'] if 'error' not in x and x['move']]
    if not ok: rec['cls'] = 'error'
    elif all(x['truth_lost'] for x in ok): rec['cls'] = 'a: truth absent'
    else:
        sampled_any = any((x['sampled'] or 0) > 0 for x in ok)
        if not sampled_any:
            share = max((x['share'] or 0) for x in ok)
            rec['cls'] = 'b: truth present, share < 1%, not sampled' if share < 0.01 else 'c: share >= 1%, not sampled'
        else:
            s_ok = [x for x in ok if (x['sampled'] or 0) > 0]
            if all(x['loses'] for x in s_ok): rec['cls'] = 'd: truth sampled, engine move still loses'
            elif all(not x['loses'] for x in s_ok): rec['cls'] = 'e: truth sampled, engine keeps the material'
            else: rec['cls'] = 'd/e mixed: sampled, loses on some seeds'
    results.append(rec)
    print(k + 1, rec['id'], 'ply', dec, 'game', game_move, 'loses' if game_loses else 'ok', '|', ' '.join(f"s{x['seed']}:{x.get('move')}{'L' if x.get('loses') else 'k'} sh={x.get('share')} smp={x.get('sampled')}" for x in rec['seeds']), '->', rec['cls'], flush=True)
    json.dump(results, open(out, 'w'), indent=0)
from collections import Counter
print('\nCLASSES', Counter(r['cls'] for r in results))
print('game move loses on the true board by the one-ply check:', Counter(r['game_move_loses'] for r in results))
