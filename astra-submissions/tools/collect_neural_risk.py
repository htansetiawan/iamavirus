#!/usr/bin/env python3
"""Measure particle and neural danger on separate, actor-only history streams."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_games(path):
    games = defaultdict(dict)
    with gzip.open(path, 'rt') as f:
        for line in f:
            e = json.loads(line)
            game, side = e['metadata']['game_id'], e['actor']['side']
            if side in games[game] or e['metadata']['feature_version'] != 'features-v2':
                raise ValueError('duplicate actor or wrong feature contract')
            games[game][side] = e
    return dict(games)


def trajectory(actors):
    if set(actors) != {0, 1}:
        raise ValueError('both complete actor histories required')
    moves = {}
    for side, e in actors.items():
        a = e['actor']
        if len(a['decision_event_indices']) != len(a['own_actions']):
            raise ValueError('action/event mismatch')
        for event, move in zip(a['decision_event_indices'], a['own_actions']):
            ply = a['plies'][event]
            if ply % 2 != side or ply in moves:
                raise ValueError('inconsistent action ply')
            moves[ply] = move
    # Startup failures have a valid empty trajectory and no learning decisions.
    if sorted(moves) != list(range(len(moves))):
        raise ValueError('incomplete move sequence')
    return hashlib.sha256(' '.join(moves[i] for i in range(len(moves))).encode()).hexdigest()


def select_partitions(train, validation, excluded, count):
    if set(train) & set(validation) or not excluded <= set(validation):
        raise ValueError('split identity mismatch')
    train_sequences = {trajectory(a) for a in train.values()}
    sequences = {game: trajectory(a) for game, a in validation.items()}
    if train_sequences & set(sequences.values()):
        raise ValueError('training/validation duplicate trajectory')
    excluded_sequences = {sequences[g] for g in excluded}
    representatives = {}
    for game in sorted(validation):
        if sequences[game] not in excluded_sequences:
            representatives.setdefault(sequences[game], game)
    groups = sorted(representatives, key=lambda h: hashlib.sha256(('neural-risk-v1:' + h).encode()).hexdigest())
    if len(groups) < 2 * count:
        raise ValueError('insufficient unused validation trajectories')
    parts = {name: [representatives[h] for h in groups[start:start + count]]
             for name, start in (('calibration', 0), ('evaluation', count))}
    return parts, sequences


def actor_stream(game, episode, stride):
    """Neither targets nor the current/future action enters a SCORE prefix."""
    a = episode['actor']
    yield f"START {game} {a['side']}\n"
    actions = dict(zip(a['decision_event_indices'], a['own_actions']))
    decisions = {event: i for i, event in enumerate(a['decision_event_indices'])}
    if not len(a['observations']) == len(a['phases']) == len(a['plies']):
        raise ValueError('observation event arrays differ')
    for event, (view, phase, ply) in enumerate(zip(a['observations'], a['phases'], a['plies'])):
        yield f'OBS {ply} {phase} {view}\n'
        if event in decisions:
            if decisions[event] % stride == 0:
                yield f'SCORE {event}\n'
            yield f'MOVE {actions[event]}\n'
    yield 'END\n'


def join_predictions(path, games, selected, stride):
    expected = {}
    for game in selected:
        for side, episode in games[game].items():
            a = episode['actor']
            for index, event in enumerate(a['decision_event_indices']):
                if index % stride == 0:
                    expected[game, side, event] = (episode, index)
    seen = set()
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            key = row['game'], row['side'], row['event']
            if key not in expected or key in seen:
                raise ValueError('unexpected or duplicated prediction')
            seen.add(key)
            episode, i = expected[key]
            actor, targets = episode['actor'], episode['targets']
            if row['ply'] != actor['plies'][row['event']]:
                raise ValueError('prediction ply mismatch')
            candidates = row['candidates']
            legal = actor['legal_actions'][i]
            if len(candidates) != len(legal) or {c['move'] for c in candidates} != set(legal):
                raise ValueError('native and dataset candidate sets differ')
            labels = dict(zip(legal, targets['king_loss_by_action'][i]))
            if len(labels) != len(legal) or any(y not in (0, 1) for y in labels.values()):
                raise ValueError('invalid tactical labels')
            for c in candidates:
                if any(not math.isfinite(c[k]) for k in ('particle', 'neural_logit', 'policy')):
                    raise ValueError('nonfinite prediction')
                if not 0 <= c['particle'] <= 1 or not 0 <= c['policy'] <= 1:
                    raise ValueError('invalid probability')
                c['fatal'] = labels[c['move']]
            if abs(sum(c['policy'] for c in candidates) - 1) > 1e-6:
                raise ValueError('policy not normalized')
            row.update(label_valid=targets['danger_valid'][i],
                       opponent_id=episode['metadata']['opponent_id'],
                       safe_alternatives=sum(y == 0 for y in labels.values()))
            yield row
    if seen != expected.keys():
        raise ValueError('missing predicted decisions')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--train', type=Path, required=True)
    p.add_argument('--validation', type=Path, required=True)
    p.add_argument('--pilot-report', type=Path, required=True)
    p.add_argument('--probe', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--games-per-partition', type=int, default=64)
    p.add_argument('--stride', type=int, default=4)
    args = p.parse_args()
    if min(args.stride, args.games_per_partition) < 1:
        p.error('positive sample sizes required')
    model = json.loads((args.model / 'model_manifest.json').read_text())
    if model['feature_version'] != 'features-v2' or model['action_version'] != 'actions-v1':
        raise ValueError('model feature/action contract mismatch')
    if model['rules_fingerprint'] != 'fow-v1/iamavirus-rules-capi' or model['parity']['failure_count']:
        raise ValueError('model rules or export parity invalid')
    train, games = read_games(args.train), read_games(args.validation)
    excluded = set(json.loads(args.pilot_report.read_text())['by_game'])
    parts, sequences = select_partitions(train, games, excluded, args.games_per_partition)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    files = [args.train, args.validation, args.pilot_report, args.probe,
             args.probe.parent / 'probe-build.json', *(args.model / f for f in ('model_manifest.json', 'observe.onnx', 'score.onnx'))]
    settings = dict(FOW_MODE='hybrid', FOW_PARTICLES='2048', FOW_OPPONENT_PRIOR='1',
                    FOW_PREDICTION_MODE='0', FOW_HISTORY_MODE='0', FOW_FRONTIER_CAPACITY='0',
                    FOW_ROOT_MODE='0', FOW_CELL_THREADS='1', FOW_BOOK_PLIES='0')
    state = {'state': 'running', 'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(),
             'inputs': {str(x.resolve()): sha(x) for x in files}, 'settings': settings,
             'collector_sha256': sha(Path(__file__)), 'stride': args.stride,
             'excluded_architecture_pilot_games': sorted(excluded), 'test_shard_used': False,
             'parts': {n: {'games': gs, 'trajectory_sha256': {g: sequences[g] for g in gs}} for n, gs in parts.items()},
             'information_boundary': 'Native process receives actor observations and own past actions. Truth labels joined after inference.',
             'limitations': ['Validation-development experiment; no sealed-test or playing-strength claim.',
                             'Sampling by own-decision stride, without oversampling failures.',
                             'One model-training seed and one particle-filter seed.']}

    def save():
        tmp = out / 'state.tmp'
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(out / 'state.json')

    save()
    env = {k: v for k, v in os.environ.items() if not k.startswith(('FOW_', 'ASTRA_'))}
    env.update(settings)
    try:
        for name, selected in parts.items():
            start = time.monotonic()
            stream = out / (name + '.actors.txt')
            with stream.open('w') as f:
                for game in selected:
                    for side in (0, 1):
                        f.writelines(actor_stream(game, games[game][side], args.stride))
            predictions = out / (name + '.predictions.jsonl')
            command = [str(args.probe.resolve()), str(args.model.resolve())]
            with stream.open() as stdin, predictions.open('w') as stdout, (out / (name + '.stderr')).open('w') as stderr:
                subprocess.run(command, stdin=stdin, stdout=stdout, stderr=stderr, env=env, check=True, timeout=3600)
            labeled = out / (name + '.jsonl.gz')
            counts = dict(decisions=0, valid_decisions=0, candidates=0, fatal_candidates=0)
            with gzip.open(labeled, 'wt') as f:
                for row in join_predictions(predictions, games, selected, args.stride):
                    f.write(json.dumps(row, separators=(',', ':')) + '\n')
                    counts['decisions'] += 1
                    if row['label_valid']:
                        counts['valid_decisions'] += 1
                        counts['candidates'] += len(row['candidates'])
                        counts['fatal_candidates'] += sum(c['fatal'] for c in row['candidates'])
            state['parts'][name].update(state='complete', elapsed_seconds=time.monotonic() - start,
                                       counts=counts, files={str(x): sha(x) for x in (stream, predictions, labeled)})
            save()
            print(json.dumps({name: counts}), flush=True)
        if any(sha(Path(name)) != digest for name, digest in state['inputs'].items()):
            raise ValueError('input changed during collection')
        state['state'] = 'complete'
    except Exception as error:
        state.update(state='failed', error=str(error))
        raise
    finally:
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        save()


if __name__ == '__main__':
    main()
