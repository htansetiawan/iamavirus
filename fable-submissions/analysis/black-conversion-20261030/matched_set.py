"""Black conversion lane, steps 1-2: the frozen matched set and the first lasting reversal.
    python3 matched_set.py STORE.jsonl.gz RAW_GAMES_DIR OUT_DIR
Set: v35 as Black vs the top nine with net material >= +3 at ply 30 (values 1/3/3/5/9). All such losses, and wins
against the same opponent version capped at the loss count per version (random seed 1).
Reversal (losses): the first ply p > 30 such that net(q) <= net(30) - 2 for every q >= p (lasting). Also the first
king-safety event: first ply at which our king is attacked on the true board by an enemy piece on a square we could
not see at that moment. For wins: the first ply p > 30 with net(p) <= net(30) - 2 (a dip) and whether/when it recovered.
"""
import gzip, json, os, random, statistics as st, sys
from collections import Counter, defaultdict
store, raw, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
TOP = {'Strongly Invisible', 'Greek Gift', 'Decent Chess Bot', 'Knight Vision', 'duck', 'Instructors', 'Crimson Fog', 'Mist Opportunities', 'HYPOTHERMIA'}
VAL = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
def material(board, white): return sum(VAL[c.lower()] for c in board if c != '-' and c.isupper() == white)
def net(board, we_white): return material(board, we_white) - material(board, not we_white)
sqn = lambda s: 'abcdefgh'[s % 8] + str(s // 8 + 1)
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
cands = []
for line in gzip.open(store, 'rt'):
    if '"IAmAVirus"' not in line: continue
    g = json.loads(line)
    if g['black'] != 'IAmAVirus' or g['bver'] != 35 or g['white'] not in TOP: continue
    cands.append((g['id'], g['white'], g['wver'], g['result'], g['plies'], g['created']))
print('v35 Black games vs the top nine:', len(cands))
rows = []
for gid, opp, over, res, plies, created in cands:
    p = os.path.join(raw, gid, 'replay.json')
    if not os.path.exists(p): continue
    f = json.load(open(p))['frames']
    if len(f) <= 31: continue
    n30 = net(f[30]['board'], False)
    if n30 < 3: continue
    rows.append({'id': gid, 'opp': opp, 'opp_version': over, 'result': res, 'won': res == '0-1', 'lost': res == '1-0', 'net30': n30, 'plies': plies, 'created': created})
losses = [r for r in rows if r['lost']]; wins = [r for r in rows if r['won']]; draws = [r for r in rows if not r['won'] and not r['lost']]
random.seed(1); matched_wins = []
loss_by_ov = Counter((r['opp'], r['opp_version']) for r in losses)
for key, k in loss_by_ov.items():
    pool = [r for r in wins if (r['opp'], r['opp_version']) == key]; random.shuffle(pool); matched_wins += pool[:k]
print('ahead >= +3 at ply 30:', len(rows), '| losses', len(losses), 'wins', len(wins), 'draws', len(draws), '| matched wins', len(matched_wins))
def analyse(r, f):
    n30 = r['net30']; nets = [net(fr['board'], False) for fr in f]
    out = {}
    # first lasting reversal: first p > 30 with nets[q] <= n30 - 2 for all q >= p
    rev = None
    for p in range(31, len(f)):
        if nets[p] <= n30 - 2 and all(nets[q] <= n30 - 2 for q in range(p, len(f))): rev = p; break
    dip = next((p for p in range(31, len(f)) if nets[p] <= n30 - 2), None)
    recovered = dip is not None and any(nets[q] >= n30 - 1 for q in range(dip, len(f)))
    out.update({'reversal_ply': rev, 'dip_ply': dip, 'recovered': recovered, 'length': len(f) - 1, 'net_end': nets[-1]})
    # first king-safety event: our king attacked on the true board by an enemy piece on a square unseen in our view
    ks_event = None
    for p in range(1, len(f)):
        b = f[p]['board']; ks = b.find('k')
        if ks < 0: break
        att = attackers_of(b, ks, True); view = f[p]['black']
        if any(view[s] == '?' for ch, s in att): ks_event = p; break
    out['first_unseen_king_attack_ply'] = ks_event
    q = rev if rev is not None else dip
    if q is not None:
        mv = f[q]['move']; to = sqi(mv[2:4]); before = f[q-1]['board']; after = f[q]['board']
        by_white = (q % 2 == 1)
        lost_piece = before[to] if by_white else None
        prev_move = f[q-1]['move'] if q >= 1 else None
        moved_in = prev_move is not None and sqi(prev_move[2:4]) == to
        # our decision before the reversal: ply q-1 (our move) if q is White's, decided with observation f[q-2]['black']
        obs = f[q-2]['black'] if q >= 2 else None
        capturer_from = sqi(mv[0:2])
        out.update({'reversal_move': mv, 'reversal_by': 'white' if by_white else 'black', 'lost_piece': (lost_piece.upper() if lost_piece and lost_piece != '-' else None),
                    'lost_square': sqn(to), 'capturer': (before[capturer_from].upper() if by_white else None), 'we_had_just_moved_it_there': moved_in,
                    'capturer_square_seen_at_our_decision': (obs[capturer_from] != '?') if obs is not None else None,
                    'our_decision_ply': q - 1, 'our_move_before': prev_move, 'net_before': nets[q-1], 'net_after': nets[q],
                    'king_attacked_before_material': (ks_event is not None and ks_event < q)})
    return out
stats = {'losses': [], 'wins': []}
for grp, lst in (('losses', losses), ('wins', matched_wins)):
    for r in lst:
        f = json.load(open(os.path.join(raw, r['id'], 'replay.json')))['frames']
        r.update(analyse(r, f)); stats[grp].append(r)
json.dump({'set': rows, 'losses': stats['losses'], 'matched_wins': stats['wins'], 'draws': len(draws)}, open(os.path.join(outdir, 'matched-set.json'), 'w'), indent=0)
L = stats['losses']; W = stats['wins']
def q(xs): xs = sorted(xs); return (xs[len(xs)//4], xs[len(xs)//2], xs[3*len(xs)//4]) if xs else None
print('\nLOSSES', len(L), '| with a lasting material reversal', sum(1 for r in L if r['reversal_ply'] is not None), '| lost without one (king captured while ahead)', sum(1 for r in L if r['reversal_ply'] is None))
rl = [r for r in L if r['reversal_ply'] is not None]
print(' reversal ply quartiles', q([r['reversal_ply'] for r in rl]), '| relative to length', q([round(r['reversal_ply']/r['length'], 2) for r in rl]), '| length quartiles', q([r['length'] for r in L]))
print(' reversal by', Counter(r['reversal_by'] for r in rl), '| lost piece', Counter(r['lost_piece'] for r in rl), '| capturer', Counter(r['capturer'] for r in rl))
print(' we had just moved it there', Counter(r['we_had_just_moved_it_there'] for r in rl), '| capturer square seen at our decision', Counter(r['capturer_square_seen_at_our_decision'] for r in rl))
print(' king attacked from the fog before the material reversal', Counter(r['king_attacked_before_material'] for r in rl), '| first unseen king attack ply quartiles', q([r['first_unseen_king_attack_ply'] for r in L if r['first_unseen_king_attack_ply']]), '| none', sum(1 for r in L if r['first_unseen_king_attack_ply'] is None))
print('\nMATCHED WINS', len(W), '| with a dip of 2+', sum(1 for r in W if r['dip_ply'] is not None), '| recovered', sum(1 for r in W if r['recovered']), '| dip ply quartiles', q([r['dip_ply'] for r in W if r['dip_ply']]))
print(' wins: dip by', Counter(r.get('reversal_by') for r in W if r['dip_ply']), '| lost piece', Counter(r.get('lost_piece') for r in W if r['dip_ply']), '| unseen king attack at some ply', sum(1 for r in W if r['first_unseen_king_attack_ply']))
