#!/usr/bin/env python3
"""Explicit follow-up: same games, new earlier decisions; not independent games.

The first screen's endgame failures mostly had no immediate escape and large
material deficits. This bounded supplement covers openings and the first
substantial material loss while still competitive. No engine parameters change.
"""
import json
from pathlib import Path
import sys

import run as audit
from fresh_taxonomy_gate import material, material_horizons, protocol
from learning import ingest

BASE = audit.OUT
OUT = BASE / 'early'


def freeze():
    original = json.loads((BASE / 'plan.json').read_text())
    plan = {k:v for k,v in original.items() if k not in ('cases', 'selection', 'groups')}
    cases = []; coverage = []; OUT.mkdir(exist_ok=True)
    for group in original['groups']:
        gid = group['game']
        payload = (audit.ROOT / 'data/raw/games' / gid / 'replay.json').read_bytes()
        replay = json.loads(payload); states, errors = ingest.validate_replay(replay); assert not errors
        template = next(c for c in original['cases'] if c['game'] == gid)
        side = template['side']; own = list(range(side, len(states)-1, 2))
        # After nine moves each, or earlier for short games. Fixed independently
        # of the instrument's output and of eventual win/loss.
        control = next((p for p in own if p >= 18), own[0])
        selected = {control: ['opening_control']}
        loss_ply = None
        for ply in own:
            if not 8 <= ply <= 60:
                continue
            lead = material(replay['frames'][ply]['board'], side)
            loss = material_horizons(replay['frames'], ply, side)['3']
            if lead >= -3 and loss is not None and loss >= 3:
                loss_ply = ply; selected.setdefault(ply, []).append('first_material_loss'); break
        coverage.append({'game': gid, 'control': control, 'first_material_loss': loss_ply})
        for ply, cohorts in sorted(selected.items()):
            feed, forced = protocol(replay, ply, side)
            redacted = json.loads(payload); key = ('white', 'black')[1-side]
            for i, frame in enumerate(redacted['frames']):
                frame['board'] = 'X'*64; frame[key] = 'X'*64
                if i == 0 or (i-1) % 2 != side or i > ply:
                    frame['move'] = 'REDACTED'
            assert protocol(redacted, ply, side) == (feed, forced)
            case = {**template, 'name': f'{gid}-{ply}', 'ply': ply, 'cohorts': cohorts,
                    'input_sha256': audit.sha(feed.encode()), 'forced': forced,
                    'material_lead_before': material(replay['frames'][ply]['board'], side)}
            (OUT / (case['name']+'.input.txt')).write_text(feed); cases.append(case)
    plan.update(cases=cases, selection='One opening control at ply18/19 and first >=3-point net loss over three plies, while lead>=-3, at ply8..60; same 11 games as late audit.',
                scope='Post-hoc earlier-position mechanism supplement on the SAME games; not independent validation or a strength estimate.',
                parent_plan_sha256=audit.sha((BASE / 'plan.json').read_bytes()), coverage=coverage,
                selector_sha256=audit.sha(Path(__file__).read_bytes()))
    with (OUT / 'plan.json').open('x') as f:
        json.dump(plan, f, indent=2)
    print(json.dumps({'cases': len(cases), 'coverage': coverage}, indent=2))


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'freeze':
        freeze()
    else:
        plan = json.loads((OUT / 'plan.json').read_text())
        assert plan['selector_sha256'] == audit.sha(Path(__file__).read_bytes())
        audit.OUT = OUT
        {'run': audit.run, 'summarize': audit.summarize}[command]()
