"""Post-hoc descriptions and a rules invariant, never an acceptance-rule change."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip
import json
import sys
from prepare import ROOT,OUT,sha,write
from model import COLUMNS
sys.path.insert(0,str(ROOT.parent/'fow-starter'))
import referee as ref

NAMES=['capture','captured_value','king_capture','knight','bishop','rook','queen','king','double_push','castle',
       'promote_queen','underpromote','forward','retreat','centre','develop','recapture','advanced_pawn','check','escape',
       'into_attack','hang_value','self_capturable','undefended','king_zone','xray_king']

def main():
    plan=json.loads((OUT/'plan.json').read_text());rows=[json.loads(s) for s in gzip.decompress((OUT/'decisions.jsonl.gz').read_bytes()).splitlines()]
    review=json.loads((OUT/'independent-review.json').read_text());assert review['passed']
    by_decision={(r['game'],r['ply']):r for r in rows};slices=defaultdict(list);teams=defaultdict(list);events=Counter();checks=0
    for g in (g for g in plan['games'] if g['split']=='test'):
        board=ref.FowBoard()
        for ply,text in enumerate(g['moves']):
            move=ref.chess.Move.from_uci(text);mover=board.turn;victim=not mover
            capture=board.is_capture(move);piece=board.piece_at(move.from_square).piece_type
            before=ref.observation(board,victim)
            count=lambda view:sum(c.isupper() if victim else c.islower() for c in view)
            old=count(before);board.push(move);after=ref.observation(board,victim)
            loss=old-count(after);assert loss==int(capture),(g['game'],ply,text,loss,capture)
            events['capture' if capture else 'quiet']+=1;checks+=1
            row=by_decision.get((g['game'],ply))
            if row is None:continue
            assert row['capture']==capture
            if not row['primary']:continue
            tags=['capture' if capture else 'quiet']
            if not capture:
                hidden=after[move.to_square]=='?';tags+=['quiet_hidden' if hidden else 'quiet_visible']
                if piece==ref.chess.KING:tags+=['quiet_king']
                if piece in (ref.chess.ROOK,ref.chess.QUEEN):tags+=['quiet_major']
                king=board.king(victim);check=king is not None and board.is_attacked_by(mover,king)
                if check:
                    tags+=['quiet_check']
                    if hidden:tags+=['quiet_hidden_check']
                    dr=move.to_square//8-move.from_square//8
                    if dr*(1 if mover else -1)<0:tags+=['quiet_retreat_check']
            for tag in tags:slices[tag].append(row)
            teams[row['team']].append(row)
    def summarize(selected):
        out=dict(decisions=len(selected),games=len({r['game'] for r in selected}))
        for F in ('14','22'):
            out[F]=dict(gain_over_base=sum(r['logp'][F]['quadratic']-r['logp'][F]['base'] for r in selected)/len(selected),
                        gain_over_linear=sum(r['logp'][F]['quadratic']-r['logp'][F]['linear'] for r in selected)/len(selected))
        return out
    selection=json.loads((OUT/'selection.json').read_text());top={}
    for key,m in selection['selected'].items():
        if m['kind']!='quadratic':continue
        terms=[];F=m['features'];names=[NAMES[i] for i in COLUMNS[:F]]
        for i,value in enumerate(m['linear']):terms.append((abs(value),names[i],value))
        for i in range(F):
            for j in range(i,F):
                value=m['quadratic'][i][j]
                if value:terms.append((abs(value),names[i]+' * '+names[j],value))
        top[key]=[dict(term=t,value=v) for _,t,v in sorted(terms,reverse=True)[:12]]
    write(OUT/'descriptive-analysis.json',dict(at=datetime.now(timezone.utc).isoformat(),posthoc=True,
          observable_capture_event=dict(actual_moves_checked=checks,events=dict(events),failures=0,
              statement='On every checked opponent move the victim observes a one-piece loss iff that move captures. This corroborates the rules proof; it is not an integrated posterior test.'),
          slices={k:summarize(v) for k,v in slices.items()},teams={k:summarize(v) for k,v in teams.items()},largest_coefficients=top,
          scope='Descriptive reused-test slices and coefficients, not additional gates, causal tactical claims or new model selection. Original overall configuration remains rejected.'))
    print(json.dumps(dict(observable_event_checks=checks,events=dict(events),slices={k:v['22']['gain_over_base'] for k,v in json.loads((OUT/'descriptive-analysis.json').read_text())['slices'].items()})),flush=True)
if __name__=='__main__':main()
