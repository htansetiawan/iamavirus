#!/usr/bin/env python3
"""Describe two retained early failures; hypotheses, not policy improvements."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'astra-submissions/tools')]
from learning import ingest, rules
from fresh_taxonomy_gate import exchange_probe, material

OUT = ROOT/'astra-submissions/analysis/frozen-tree-20261101'
cases = [('tjds234d',54,'b1b7','b1b3'), ('92px495s',26,'d1d5','f3d5')]
results = []
for gid, ply, move, alternative in cases:
    replay = json.loads((ROOT/'data/raw/games'/gid/'replay.json').read_text())
    states, errors = ingest.validate_replay(replay); assert not errors
    state = states[ply]; board = state.board.board_string(); probe = exchange_probe(state, move)
    reply = probe['worst_capture']; sq = rules.square_index(reply[:2]); attacker = board[sq]
    audit = json.loads((OUT/'early'/f'{gid}-{ply}.audit.json').read_text())
    results.append({'game':gid,'ply':ply,'chosen':move,'probe':probe,'alternative':alternative,
                    'alternative_probe':exchange_probe(state,alternative),
                    'material_lead_before':material(board,state.board.side),
                    'attacker':attacker,'attacker_square':reply[:2],
                    'attacker_visible':replay['frames'][ply][('white','black')[state.board.side]][sq]!='?',
                    'sample_attacker_mass':sum(s['weight'] for s in audit['samples'] if s['board'][sq]==attacker),
                    'true_board_sample_mass':sum(s['weight'] for s in audit['samples'] if s['board']==board),
                    'sample_risks_are_not_full_belief_weights':True})
(OUT/'material-focus.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
