"""Versioned, retrospective taxonomy of the complete reviewed field snapshot.

Uses the existing v0 and tested isolated EP correction. No fit, actor input,
new game, shared-report mutation, network request or deployment is performed.
"""
from argparse import ArgumentParser
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

import chess

ROOT = Path(__file__).resolve().parents[2]
FIELD = ROOT / 'data/astra-spool/field-snapshot-20261111'
REVIEW = ROOT / 'astra-submissions/analysis/field-snapshot-20261111'
LABELS = ROOT / 'astra-submissions/experiments/taxonomy-en-passant-20261111'
OUT = ROOT / 'astra-submissions/analysis/field-taxonomy-20261111'
STORE = ROOT / 'data/astra-spool/field-taxonomy-20261111'
OWNER = 'astra-field-taxonomy-20261111'
OURS = 'a2c35173659545c99752376a70418438'
CAPTURE_TAGS = {'capture', 'quiet', 'capture_unseen', 'victim_walked_in', 'long_strike', 'fog_route', 'forcing_chain'}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def labelers():
    return load('field_taxonomy_v0', LABELS / 'baseline.py'), load('field_taxonomy_ep_v1', LABELS / 'move_taxonomy.py')


def checked_labels(replay, baseline, fixed):
    old, new = baseline.label_game(replay), fixed.label_game(replay)
    assert new['taxonomy_version'] == 'astra-ep-v1'
    comparable = {k: v for k, v in new.items() if k != 'taxonomy_version'}
    board = chess.Board()
    truth, changes = [], []
    for frame in replay['frames'][1:]:
        move = chess.Move.from_uci(frame['move'])
        capture, ep = board.is_capture(move), board.is_en_passant(move)
        victim = move.to_square + (-8 if board.turn else 8) if ep else move.to_square if capture else None
        truth.append(dict(capture=capture, ep=ep, victim=victim, source=move.from_square))
        board.push(move)
        actual = ''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64))
        assert actual == frame['board'], (replay['id'], frame['ply'], 'history capture oracle board')
    assert len(old['moves']) == len(new['moves']) == len(truth) == len(replay['frames']) - 1
    ep_count = sum(t['ep'] for t in truth)
    if ep_count == 0:
        assert old == comparable, (replay['id'], 'non-EP game changed')
    for i, (a, b, t) in enumerate(zip(old['moves'], new['moves'], truth, strict=True)):
        assert all(a[k] == b[k] for k in ('ply', 'side', 'move', 'piece'))
        tags, prior = set(b['tags']), set(a['tags'])
        assert ('capture' in tags) == t['capture'] and ('quiet' in tags) == (not t['capture'])
        assert tags - CAPTURE_TAGS == prior - CAPTURE_TAGS
        chain = i + 2 < len(truth) and all(x['capture'] for x in truth[i:i + 3])
        assert ('forcing_chain' in tags) == chain
        if t['capture']:
            view = replay['frames'][i]['black' if b['side'] == 0 else 'white']
            assert ('capture_unseen' in tags) == (view[t['source']] == '?')
            previous = replay['frames'][i]['move']
            arrived = previous is not None and chess.parse_square(previous[2:4]) == t['victim']
            assert ('victim_walked_in' in tags) == arrived
        if tags != prior:
            permitted = CAPTURE_TAGS if t['ep'] else {'forcing_chain'}
            assert tags.symmetric_difference(prior) <= permitted
            if not t['ep']:
                assert any(x['ep'] for x in truth[i:i + 3])
            changes.append(dict(ply=b['ply'], move=b['move'], before=a['tags'], after=b['tags']))
    for side, color in [('white', 0), ('black', 1)]:
        rows = [m for m in new['moves'] if m['side'] == color]
        assert new['counts'][side].get('moves', 0) == len(rows)
        expected = Counter(tag for m in rows for tag in m['tags'])
        for tag in set(expected) | set(fixed.KEYS) | {'quiet', 'king_capture'}:
            assert new['counts'][side].get(tag, 0) == expected[tag]
    return new, old['counts'], ep_count, changes


def terminal_context(replay, row, fixed):
    """Existing terminal geometry classes, without a new safety/search test."""
    if replay['reason'] != 'King capturable':
        return None
    frames = replay['frames']
    previous, final = frames[-2], frames[-1]
    side = 'white' if final['ply'] % 2 else 'black'
    color = side == 'white'
    assert replay['result'] == ('0-1' if color else '1-0')
    before, after = chess.Board(fixed.fen(previous['board'])), chess.Board(fixed.fen(final['board']))
    move = chess.Move.from_uci(final['move'])
    moved = before.piece_at(move.from_square)
    king_before, king_after = before.king(color), after.king(color)
    assert moved is not None and moved.color == color and king_before is not None and king_after is not None
    already_attacked = bool(before.attackers(not color, king_before))
    attackers = list(after.attackers(not color, king_after))
    assert attackers
    king_move = moved.piece_type == chess.KING
    mechanism = ('king_move_from_existing_attack' if already_attacked else 'king_move_into_attack') if king_move else ('nonking_move_did_not_resolve_attack' if already_attacked else 'nonking_move_opened_attack')
    hidden = [sq for sq in attackers if previous[side][sq] == '?']
    balance = fixed.material(previous['board'], 0 if color else 1) - fixed.material(previous['board'], 1 if color else 0)
    return dict(game=row['id'], team_id=row[side + 'PlayerId'], team=row[side], version=row[side + 'Version'], side=side,
                opponent_id=row[('black' if color else 'white') + 'PlayerId'],
                opponent=row['black' if color else 'white'], opponent_version=row[('black' if color else 'white') + 'Version'],
                ply=final['ply'], move=final['move'], mechanism=mechanism, king_was_attacked_before=already_attacked,
                before_material_balance=balance, any_attacker_hidden_in_decision_view=bool(hidden),
                all_attackers_hidden_in_decision_view=len(hidden) == len(attackers),
                attackers=[dict(square=chess.square_name(s), piece=after.piece_at(s).symbol(), hidden_before=s in hidden) for s in attackers])


def prepare():
    closed = read(REVIEW / 'closure-review.json')
    assert closed['status'] == 'complete' and closed['games'] == 6000
    for rel, digest in closed['artifact_sha256'].items():
        assert sha(ROOT / rel) == digest, rel
    origin = read(LABELS / 'origin.json')
    assert sha(ROOT / origin['source']) == sha(LABELS / 'baseline.py') == origin['sha256']
    patch_review = read(ROOT / 'astra-submissions/analysis/taxonomy-en-passant-20261111/result.json')
    for path, digest in patch_review['source_sha256'].items():
        assert sha(path) == digest, path
    baseline, fixed = labelers()
    listing = read(FIELD / 'listing.json')
    preflight = []
    for row in listing[:2]:
        labels, _, eps, changes = checked_labels(read(FIELD / 'raw/games' / row['id'] / 'replay.json'), baseline, fixed)
        preflight.append(dict(game=row['id'], moves=len(labels['moves']), ep_captures=eps, label_changes=len(changes)))
    dependencies = [Path(__file__), LABELS / 'baseline.py', LABELS / 'move_taxonomy.py', LABELS / 'origin.json',
                    ROOT / 'learning/move_taxonomy.py', ROOT / 'astra-submissions/analysis/taxonomy-en-passant-20261111/result.json',
                    REVIEW / 'closure-review.json', REVIEW / 'review-result.json', REVIEW / 'listing-review.json',
                    FIELD / 'listing.json', FIELD / 'validation.jsonl', FIELD / 'leaderboard.json', Path(chess.__file__)]
    plan = dict(at=now(), games=6000, wall_seconds=1800, cores=[6],
                selection='All 6000 reviewed IDs in frozen listing order, all teams, outcomes and lengths. No performance-based exclusion.',
                taxonomy_versions=['v0', fixed.TAXONOMY_VERSION],
                aggregates='One-pass raw counts by exact team ID, played version, color; opponent/version/color cells retained. All actual game IDs count, with duplicate full sequences disclosed.',
                terminal_diagnostics='Four existing last-move geometry classes, attacker visibility in the predecision view, true material before the fatal move. No safe-reply search or causal attribution.',
                dependencies={str(p): sha(p) for p in dependencies},
                antecedents=['chatroom/015-fable-move-taxonomy-capability-map-and-gym.md', 'chatroom/189-astra-daily-intel-maintenance.md', 'chatroom/216-astra-taxonomy-use-and-refresh.md', 'chatroom/327-astra-terminal-pattern-refresh.md', 'chatroom/368-astra-tested-ep-taxonomy-reporting-patch.md'],
                difference='Refresh existing diagnostics on the fully reviewed 6000-game local snapshot; measure EP label deltas against the frozen v0, with separate version/color denominators. No new strategy algorithm.',
                scope='Retrospective local data analysis only. No actor features, model fitting, split assignment, bot search, new game, shared report replacement, network, GPU, package, commit, push or deployment.')
    OUT.mkdir(exist_ok=False)
    save(OUT / 'plan.json', plan)
    save(OUT / 'preflight.json', dict(at=now(), games=preflight, checks='Both labelers plus full-history capture oracle and per-tag counts on original first two games.', scope=plan['scope']))
    print(json.dumps(dict(plan_sha256=sha(OUT / 'plan.json'), preflight=preflight)), flush=True)


@contextmanager
def lease(cores):
    path = ROOT / 'chatroom/cores.json'
    def change(take):
        with open('/tmp/iamavirus-cores-json.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = read(path)
            if take:
                assert not any(set(r['cores']) & set(cores) for r in state['allocation'])
                state['allocation'].append(dict(owner=OWNER, cores=cores, pid=os.getpid(), at=now(), purpose='bounded retrospective field taxonomy'))
            else:
                state['allocation'] = [r for r in state['allocation'] if not (r['owner'] == OWNER and r.get('pid') == os.getpid())]
            state['updated'] = now()
            atomic(path, state)
    change(True)
    try:
        yield
    finally:
        change(False)


def accumulate(groups, key, row, side, new, old, sequence, terminal):
    other = 'black' if side == 'white' else 'white'
    group = groups.setdefault(key, dict(team_id=row[side + 'PlayerId'], team=row[side], version=row[side + 'Version'], side=side,
                                       games=0, counts=Counter(), baseline_counts=Counter(), outcomes=Counter(),
                                       opponents=Counter(), sequences=set(), terminal=Counter()))
    group['games'] += 1
    group['counts'].update(new)
    group['baseline_counts'].update(old)
    group['sequences'].add(sequence)
    group['opponents'][(row[other + 'PlayerId'], row[other + 'Version'])] += 1
    won = row['result'] == ('1-0' if side == 'white' else '0-1')
    group['outcomes']['draws' if row['result'] == '1/2-1/2' else 'wins' if won else 'losses'] += 1
    if terminal and terminal['side'] == side:
        group['terminal'][terminal['mechanism']] += 1
        group['terminal']['any_attacker_hidden_before'] += terminal['any_attacker_hidden_in_decision_view']
        group['terminal']['all_attackers_hidden_before'] += terminal['all_attackers_hidden_in_decision_view']
        group['terminal']['material_down_three_before'] += terminal['before_material_balance'] <= -3


def export(group, keys):
    count, old = group['counts'], group['baseline_counts']
    n = count.get('moves', 0)
    return {**group, 'counts': dict(count), 'baseline_counts': dict(old), 'outcomes': dict(group['outcomes']),
            'terminal': dict(group['terminal']), 'unique_full_sequences': len(group['sequences']), 'sequences': None,
            'opponents': [dict(team_id=t, version=v, games=k) for (t, v), k in sorted(group['opponents'].items(), key=lambda x: repr(x[0]))],
            'rates_per_100_moves': {k: 100 * count.get(k, 0) / n if n else None for k in keys},
            'ep_fix_count_deltas': {k: count.get(k, 0) - old.get(k, 0) for k in sorted(set(count) | set(old)) if count.get(k, 0) != old.get(k, 0)},
            'visible_mean': count.get('vision_total', 0) / n if n else None}


def run():
    plan = read(OUT / 'plan.json')
    for p, digest in plan['dependencies'].items():
        assert sha(p) == digest, p
    listing = read(FIELD / 'listing.json')
    validated = [json.loads(s) for s in (FIELD / 'validation.jsonl').read_text().splitlines()]
    assert len(listing) == len(validated) == plan['games'] == 6000
    assert [r['id'] for r in listing] == [r['id'] for r in validated]
    baseline, fixed = labelers()
    groups, pairs, sequences = {}, {}, Counter()
    total, deltas, source_hashes = Counter(), Counter(), []
    state = dict(at=now(), status='running', completed=0, plan_sha256=sha(OUT / 'plan.json'))
    save(OUT / 'execution.json', state)
    STORE.mkdir(exist_ok=False)
    os.sched_setaffinity(0, set(plan['cores']))
    def timeout(*_):
        raise TimeoutError('field taxonomy reached original wall limit')
    signal.signal(signal.SIGALRM, timeout)
    signal.signal(signal.SIGTERM, timeout)
    signal.alarm(plan['wall_seconds'])
    started = time.monotonic()
    try:
        with lease(plan['cores']), (STORE / 'games.jsonl').open('x') as journal, (STORE / 'terminal.jsonl').open('x') as terminals:
            for meta, valid in zip(listing, validated, strict=True):
                path = FIELD / 'raw/games' / meta['id'] / 'replay.json'
                digest = sha(path)
                assert digest == valid['replay_sha256'] and valid['accepted'] and not valid['problems']
                replay = read(path)
                for k in ('id', 'white', 'black', 'whiteVersion', 'blackVersion', 'whitePlayerId', 'blackPlayerId', 'result', 'reason'):
                    assert replay[k] == meta[k], (meta['id'], k)
                new, old, ep_count, changes = checked_labels(replay, baseline, fixed)
                terminal = terminal_context(replay, meta, fixed)
                sequence = valid['moves_sha256']
                for side in ('white', 'black'):
                    other = 'black' if side == 'white' else 'white'
                    key = (meta[side + 'PlayerId'], meta[side + 'Version'], side)
                    accumulate(groups, key, meta, side, new['counts'][side], old[side], sequence, terminal)
                    pair_key = key + (meta[other + 'PlayerId'], meta[other + 'Version'])
                    accumulate(pairs, pair_key, meta, side, new['counts'][side], old[side], sequence, terminal)
                record = dict(**new, metadata=meta, baseline_counts=old, replay_sha256=digest, sequence_sha256=sequence,
                              ep_captures=ep_count, label_changes=changes)
                journal.write(json.dumps(record, allow_nan=False) + '\n')
                if terminal:
                    terminals.write(json.dumps(terminal, allow_nan=False) + '\n')
                    total['king_capturable_games'] += 1
                total.update(games=1, moves=len(new['moves']), frames=len(replay['frames']), ep_captures=ep_count,
                             games_with_ep=int(ep_count > 0), changed_move_labels=len(changes), games_with_label_changes=int(bool(changes)))
                sequences[sequence] += 1
                source_hashes.append(dict(game=meta['id'], replay_sha256=digest, sequence_sha256=sequence))
                for side in ('white', 'black'):
                    deltas.update({k: new['counts'][side].get(k, 0) - old[side].get(k, 0) for k in set(new['counts'][side]) | set(old[side])})
                if total['games'] % 250 == 0:
                    journal.flush(); terminals.flush()
                    state['completed'] = total['games']
                    atomic(OUT / 'execution.json', state)
                    print(json.dumps(dict(completed=total['games'], moves=total['moves'], ep_captures=total['ep_captures'])), flush=True)
        review = read(REVIEW / 'review-result.json')
        assert total['frames'] == review['totals']['frames'] == 459622
        assert len(sequences) == review['unique_trajectories'] == 5872
        assert total['moves'] == total['frames'] - total['games'] == 453622
        assert sum(g['games'] for g in groups.values()) == 12000
        assert sum(g['counts'].get('moves', 0) for g in groups.values()) == total['moves']
        assert sum(g['games'] for g in groups.values() if g['team_id'] == OURS) == 345
        for p, digest in plan['dependencies'].items():
            assert sha(p) == digest, p
        save(STORE / 'source-hashes.json', source_hashes)
        save(STORE / 'opponent-cells.json', [export(pairs[k], fixed.KEYS) for k in sorted(pairs, key=repr)])
        leader_record = read(FIELD / 'leaderboard.json')
        ranked = sorted((p for p in leader_record['data']['players'] if p.get('rating') is not None), key=lambda p: -p['rating'])
        result = dict(at=now(), plan_sha256=sha(OUT / 'plan.json'), taxonomy_version=fixed.TAXONOMY_VERSION,
                      totals=dict(total), unique_full_sequences=len(sequences), duplicate_extra_ids=sum(n - 1 for n in sequences.values()),
                      ep_fix_total_count_deltas={k: v for k, v in deltas.items() if v},
                      leaderboard_fetched_at=leader_record['fetch']['fetched_at'],
                      leaders_at_snapshot=[dict(team_id=p['id'], name=p['name'], active_version=p['activeVersion'], elo=p['rating']) for p in ranked[:6]],
                      selection_window=dict(newest=listing[0]['createdAt'], oldest=listing[-1]['createdAt']),
                      team_version_color=[export(groups[k], fixed.KEYS) for k in sorted(groups, key=repr)],
                      own_opponent_version_color=[dict(opponent_id=k[3], opponent_version=k[4], **export(pairs[k], fixed.KEYS)) for k in sorted(pairs, key=repr) if k[0] == OURS],
                      artifacts={str(p.relative_to(ROOT)): sha(p) for p in [STORE / 'games.jsonl', STORE / 'terminal.jsonl', STORE / 'source-hashes.json', STORE / 'opponent-cells.json']},
                      scope=plan['scope'], limitations=['Rates are observational and move-weighted, not causal skill rankings or independent-game confidence intervals.',
                      'Repeated complete trajectories remain in actual game counts; this is not a training split.',
                      'Many tags and all terminal attacker/material diagnoses use hindsight unavailable to the actor.',
                      'The four terminal mechanisms identify the final failure, not the earlier strategic cause or the availability of a one-ply escape.',
                      'The legacy king_capture tag is outside the 19 core metrics; its inferred terminal semantics are not corrected by this EP-only version.',
                      'This report neither repairs shared daily automation nor updates deployed models, history counts or guards.'])
        save(OUT / 'result.json', result)
        state.update(status='complete', completed=6000, result_sha256=sha(OUT / 'result.json'))
        print(json.dumps({k: result[k] for k in ('totals', 'unique_full_sequences', 'ep_fix_total_count_deltas')}, indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        atomic(OUT / 'execution.json', state)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.command]()
