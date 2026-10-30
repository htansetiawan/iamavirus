"""Full static exchange evaluation on the true 64-char board (a1..h8), recomputing attackers after every capture so
discovered sliders count. loses_material(board_before, our_uci): after our move, the opponent's best exchange gain over
all our pieces (least-valuable-attacker sequence, both sides may stop) minus what our move itself captured, >= 2; or
our king capturable (FoW: that ends the game)."""
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
        if hit: res.append((VAL[ch.lower()], s, ch))
    return res
def apply(board, uci):
    b = list(board); f, t = sqi(uci[:2]), sqi(uci[2:4]); piece = b[f]
    if piece == '-': return None
    b[t] = piece; b[f] = '-'
    if piece.lower() == 'p' and len(uci) == 5: b[t] = uci[4].upper() if piece.isupper() else uci[4]
    if piece.lower() == 'k' and abs(t - f) == 2:
        rf, rt = (f + 3, f + 1) if t > f else (f - 4, f - 1); b[rt] = b[rf]; b[rf] = '-'
    if piece.lower() == 'p' and (t - f) % 8 != 0 and board[t] == '-': b[t - 8 if piece.isupper() else t + 8] = '-'
    return ''.join(b)
def see(board, target, side_white):
    """material the side to move wins by starting an exchange on target (0 if it should not capture); recursive negamax
    with the least valuable attacker; a king only captures if the square is then unattacked (FoW: capturing into an
    attacked square loses the king next ply)"""
    att = attackers_of(board, target, side_white)
    if not att: return 0
    victim = board[target]
    if victim == '-': return 0
    best = 0
    for v, s, ch in sorted(att):
        nb = apply(board, 'abcdefgh'[s % 8] + str(s // 8 + 1) + 'abcdefgh'[target % 8] + str(target // 8 + 1))
        if ch.lower() == 'k' and attackers_of(nb, target, not side_white): continue
        gain = VAL[victim.lower()] - see(nb, target, not side_white)
        best = max(best, gain); break      # least valuable attacker first is the standard SEE choice
    return best
def loses_material(board_before, our_uci, we_white=False):
    to = sqi(our_uci[2:4]); cap_gain = VAL[board_before[to].lower()] if board_before[to] != '-' else 0
    b = apply(board_before, our_uci)
    if b is None: return None, None
    ks = b.find('K' if we_white else 'k')
    if ks >= 0 and attackers_of(b, ks, not we_white): return True, ('king capturable', 100, cap_gain)
    best = 0; what = None
    for s, ch in enumerate(b):
        if ch == '-' or ch.isupper() != we_white or ch.lower() == 'k': continue
        g = see(b, s, not we_white)
        if g > best: best, what = g, f"exchange on {'abcdefgh'[s % 8]}{s // 8 + 1} ({ch}) wins {g}"
    return (best - cap_gain) >= 2, (what, best, cap_gain)
