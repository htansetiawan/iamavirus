"""How Mist Opportunities loses and draws on the arena: its last move, the attacker, visibility, material, clock."""
import json, sys, collections, chess
ROOT = '/home/henrytan/git/iamavirus/data/raw/'
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
def board(s, turn):
    b = chess.Board(None)
    for i, c in enumerate(s):
        if c not in '-?': b.set_piece_at(i, chess.Piece.from_symbol(c))
    b.turn = turn
    return b
def material(b, colour):
    return sum(VAL[p.piece_type] for p in b.piece_map().values() if p.color == colour)
rows = [json.loads(l) for l in open(ROOT + 'accepted.jsonl') if 'Mist Opportunities' in l]
out = collections.Counter()
for r in rows:
    mw = r['white'] == 'Mist Opportunities'
    s = {'1-0': 1, '0-1': 0}.get(r['result'], 0.5); s = s if mw else 1 - s
    if s == 1: continue
    d = json.load(open(f"{ROOT}games/{r['id']}/replay.json"))
    fr = d['frames']; mc = chess.WHITE if mw else chess.BLACK; opp = r['black'] if mw else r['white']
    key = 'white' if mw else 'black'
    last = fr[-1]; before = fr[-2]
    b_after = board(last['board'], not mc); b_before = board(before['board'], mc)
    k_after = b_after.king(mc)
    mat = material(b_before, mc) - material(b_before, not mc)
    clock = before['clocks'][0 if mw else 1]
    if s == 0.5:
        print(f"DRAW vs {opp:18s} {'W' if mw else 'B'} plies {len(fr)-1:3d} material(Mist-opp) {mat:+d} clock {clock:.0f} {r['reason']}")
        continue
    # attackers of Mist's king after its move, and whether Mist's view (before the move) showed them
    view_before = before[key]
    att_after = [sq for sq in b_after.attackers(not mc, k_after)] if k_after is not None else []
    seen = [view_before[sq] not in '?' for sq in att_after]
    k_before = b_before.king(mc)
    in_check_before = bool(b_before.attackers(not mc, k_before)) if k_before is not None else False
    att_before = list(b_before.attackers(not mc, k_before)) if k_before is not None else []
    seen_before = [view_before[sq] not in '?' for sq in att_before]
    m = last['move']; piece = b_before.piece_at(chess.parse_square(m[:2]))
    kind = ('checked, did not escape' if in_check_before else 'walked into attack')
    vis = 'attacker hidden' if att_after and not any(seen) else 'attacker visible' if att_after else '?'
    out[(kind, vis)] += 1
    print(f"LOSS vs {opp:18s} {'W' if mw else 'B'} plies {len(fr)-1:3d} material(Mist-opp) {mat:+d} clock {clock:.0f} last {piece.symbol() if piece else '?'}{m} | {kind}; {vis} {[chess.square_name(q)+b_after.piece_at(q).symbol() for q in att_after]}")
print(out)
