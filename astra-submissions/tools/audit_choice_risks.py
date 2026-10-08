#!/usr/bin/env python3
"""Probe both changed choices under both frozen belief configurations."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--comparison', type=Path, required=True)
    p.add_argument('--probe', type=Path, required=True)
    p.add_argument('--corpus', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = json.loads(args.comparison.read_text())
    histories = {}
    for line in args.corpus.read_text().splitlines():
        game, side, _, _, _, *moves = line.split()
        histories[(game, int(side == 'b'))] = moves
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    probe = out / 'probe'; probe.write_bytes(args.probe.read_bytes()); probe.chmod(0o755)
    state = {'state': 'running', 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
             'comparison_sha256': sha(args.comparison), 'corpus_sha256': sha(args.corpus),
             'probe_sha256': sha(probe), 'runner_sha256': sha(Path(__file__)),
             'planned_changes': len(report['fatal_changes']), 'runs': []}
    def save():
        temp = out / 'state.tmp'; temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(out / 'state.json')
    save()
    counts = Counter()
    try:
        for change in report['fatal_changes']:
            game, side, ply = change['game'], change['side'], change['ply']
            moves = out / f'{game}-{side}.moves'
            moves.write_text(' '.join(histories[(game, side)]) + '\n')
            requested = out / f'{game}-{side}.requests'
            requested.write_text(''.join(f"{ply} {change[name]['move']}\n" for name in ('control', 'candidate')))
            for name in ('control', 'candidate'):
                settings = report['arms'][report[name]]['settings']
                env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
                env.update(ASTRA_HISTORY_MODE=settings['FOW_HISTORY_MODE'],
                           ASTRA_OPPONENT_PRIOR=settings['FOW_OPPONENT_PRIOR'],
                           ASTRA_PREDICTION_MODE=settings['FOW_PREDICTION_MODE'],
                           ASTRA_FRONTIER_CAPACITY=settings.get('FOW_FRONTIER_CAPACITY', '0'),
                           ASTRA_PROBE_CANDIDATES=str(requested))
                command = [str(probe), str(moves), str(side), '777', settings['FOW_PARTICLES']]
                stem = f'{game}-{side}-{name}'
                with (out / (stem + '.jsonl')).open('w') as trace, (out / (stem + '.stderr')).open('w') as err:
                    result = subprocess.run(command, env=env, stdout=trace, stderr=err, timeout=600)
                if result.returncode:
                    raise RuntimeError(f'probe failed: {stem}')
                rows = [json.loads(line) for line in (out / (stem + '.jsonl')).read_text().splitlines()]
                row = next(r for r in rows if r['ply'] == ply)
                risks = {r['move']: r for r in row['candidate_risks']}
                for other in ('control', 'candidate'):
                    if risks[change[other]['move']]['truth_fatal'] != change[other]['king_loss']:
                        raise ValueError('probe truth disagrees with benchmark')
                selected = risks[change[name]['move']]
                if selected['risk_permille'] != change[name]['king_risk_permille']:
                    raise ValueError(f"selected risk disagrees with engine: {stem}: {selected['risk_permille']} != {change[name]['king_risk_permille']}")
                fatal = next(v for v in risks.values() if v['truth_fatal'])
                safe = next(v for v in risks.values() if not v['truth_fatal'])
                def probability(r):
                    return r['risk_particles'] / r['legal_particles'] if r['legal_particles'] else 1.0
                bad, good = probability(fatal), probability(safe)
                diagnosis = ('blind_to_fatal_move' if bad == 0 else
                             'risk_favors_fatal_move' if bad < good else
                             'risk_tied' if bad == good else 'risk_favors_safe_move')
                direction = 'new_fatal' if change['candidate']['king_loss'] else 'saved'
                counts[f'{direction}/{name}/{diagnosis}'] += 1
                state['runs'].append({'game': game, 'side': side, 'ply': ply, 'belief': name,
                                      'direction': direction, 'selected_move': selected['move'],
                                      'diagnosis': diagnosis, 'risks': risks,
                                      'truth_board_matches': row['truth_board_matches'],
                                      'particles': row['particles'], 'collapsed': row['collapsed'],
                                      'trace_sha256': sha(out / (stem + '.jsonl'))})
                save()
            print(json.dumps({'changes_completed': len(state['runs']) // 2, 'game': game}), flush=True)
        state.update(state='complete', completed_at=datetime.now(timezone.utc).isoformat(), counts=dict(counts),
                     limitations=['Selected changed-fatal cases only; diagnosis, not a new promotion sample.',
                                  'Risk-favors-safe means this safe comparator had lower model risk; it does not establish optimal play.',
                                  'Probe probabilities are checked exactly against the original engine risk trace.'])
    except BaseException as error:
        state.update(state='failed', error=repr(error)); raise
    finally:
        save()


if __name__ == '__main__':
    main()
