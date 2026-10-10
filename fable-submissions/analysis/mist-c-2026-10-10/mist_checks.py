"""Hidden checks in Mist Opportunities' arena games: given by each side, and how often the checked side escaped."""
import json, collections, chess
ROOT = '/home/henrytan/git/iamavirus/data/raw/'
VAL = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
def board(s):
    b = chess.Board(None)
    for i, c in enumerate(s):
        if c not in '-?': b.set_piece_at(i, chess.Piece.from_symbol(c))
    return b
def mat(s, white):
    return sum(VAL[c.lower()] for c in s if c not in '-?' and c.isupper() == white)
rows = [json.loads(l) for l in open(ROOT + 'accepted.jsonl') if 'Mist Opportunities' in l]
group = lambda o: 'IAmAVirus' if o == 'IAmAVirus' else 'top six' if o in ('Greek Gift', 'Strongly Invisible', 'Decent Chess Bot', 'Knight Vision', 'duck', 'Instructors') else 'TA baselines' if o.startswith('TA') else 'rest'
st = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    mw = r['white'] == 'Mist Opportunities'; opp = r['black'] if mw else r['white']; g = group(opp)
    fr = json.load(open(f"{ROOT}games/{r['id']}/replay.json"))['frames']
    st[g]['games'] += 1
    s = {'1-0': 1, '0-1': 0}.get(r['result'], 0.5); st[g]['mist points'] += s if mw else 1 - s
    for i in range(1, len(fr)):
        mover_white = i % 2 == 1
        who = 'mist' if mover_white == mw else 'opp'
        b = board(fr[i]['board']); victim_white = not mover_white
        k = b.king(chess.WHITE if victim_white else chess.BLACK)
        if k is None: continue
        att = b.attackers(chess.WHITE if mover_white else chess.BLACK, k)
        if not att: continue
        view = fr[i]['white' if victim_white else 'black']
        if any(view[q] != '?' for q in att): continue      # the checked side can see an attacker
        st[g][who + ' gave hidden checks'] += 1
        if i + 1 >= len(fr):   # game ended on the checking move? (it doesn't; the checked side moves next)
            continue
        # escaped if the checked side's reply did not end the game by king capture
        ended = i + 1 == len(fr) - 1 and r['reason'] == 'King capturable'
        if not ended: st[g][who + ' checks escaped'] += 1
        # material lead of the checked side at that moment
for g in ('IAmAVirus', 'top six', 'TA baselines', 'rest'):
    c = st[g]; n = c['games']
    if not n: continue
    def rate(who):
        given = c[who + ' gave hidden checks']; esc = c[who + ' checks escaped']
        return f"{given/n:.2f}/game, escaped {esc}/{given} ({(given-esc)/max(given,1):.0%} fatal)"
    print(f"vs {g:12s} games {n:3d}  Mist score {c['mist points']/n:.2f} | Mist's hidden checks: {rate('mist')} | opponent's hidden checks on Mist: {rate('opp')}")
