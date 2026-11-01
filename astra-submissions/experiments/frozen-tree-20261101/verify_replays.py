#!/usr/bin/env python3
"""Independent course-referee check of the frozen games and tactical labels."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/frozen-tree-20261101'
sys.path[:0] = [str(ROOT), str(ROOT / 'astra-submissions/tools')]
from analyze_duck import verify_with_referee

plan = json.loads((OUT / 'plan.json').read_text())
referee = ROOT.parent / 'fow-starter/referee.py'
results = []
for game in sorted({c['game'] for c in plan['cases']}):
    replay = json.loads((ROOT / 'data/raw/games' / game / 'replay.json').read_text())
    results.append({'game': game, **verify_with_referee(replay, referee)})
result = {'games': len(results), 'frames': sum(r['frames'] for r in results),
          'legal_move_survival_checks': sum(r['all_legal_move_survival_checks'] for r in results), 'results': results}
(OUT / 'referee-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v for k,v in result.items() if k != 'results'}))
