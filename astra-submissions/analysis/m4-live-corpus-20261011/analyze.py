#!/usr/bin/env python3
"""Describe the retained audit; these truth labels are not policy inputs."""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import chess

root=Path(__file__).resolve().parent
rows=json.loads(gzip.decompress((root/'audits.json.gz').read_bytes()))
strata=defaultdict(Counter);families=Counter();cases=[]
for game in rows:
    for decision in game['decisions']:
        key='changed' if decision['opponent_move_changed_view'] else 'unchanged'
        strata[key]['decisions']+=1
        strata[key]['fatal']+=decision['immediate_loss']
        if not decision['immediate_loss']:
            continue
        board=chess.Board(decision['fen']);move=chess.Move.from_uci(decision['move'])
        king=board.piece_at(move.from_square).piece_type==chess.KING
        if decision['attackers_before']:
            family='king_moves_while_attacked' if king else 'nonking_move_leaves_existing_attack'
        else:
            family='king_enters_attack' if king else 'move_uncovers_own_king'
        families[family]+=1
        cases.append({'game':game['id'],'side':game['side'],'ply':decision['ply'],
            'move':decision['move'],'family':family,'safe_alternatives':len(decision['safe_moves']),
            'unchanged':key=='unchanged','material_cp':decision['material_cp'],
            'opponent':game['event']['opponent']})
report={'strata':dict(strata),'families':dict(families),'cases':cases,
    'limitation':'Descriptive, correlated trajectories of arena v30; not conditional causal effects or training inputs.'}
(root/'patterns.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
