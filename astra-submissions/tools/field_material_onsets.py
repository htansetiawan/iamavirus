"""Extend the existing five-frame material-onset diagnostic to all v38 seats.

Retrospective, fixed-cohort curation only. No bot search, safe-reply analysis,
new match, training, network request or shared-report replacement.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
from statistics import median
import time

import chess

ROOT = Path(__file__).resolve().parents[2]
FIELD = ROOT / 'data/astra-spool/field-snapshot-20261111'
TAX = ROOT / 'data/astra-spool/field-taxonomy-20261111'
OUT = ROOT / 'astra-submissions/analysis/field-material-onsets-20261111'
STORE = ROOT / 'data/astra-spool/field-material-onsets-20261111'
OLD_ROWS = ROOT / 'data/astra-spool/duck-v11-matchup-20261110/matchup-rows.json'
OLD_SOURCE = ROOT / 'astra-submissions/experiments/duck-v11-matchup-20261110/measure.py'
PATCH = ROOT / 'astra-submissions/experiments/taxonomy-en-passant-20261111/move_taxonomy.py'
OURS = 'a2c35173659545c99752376a70418438'
VALUES = dict(p=1, n=3, b=3, r=5, q=9, k=0)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def material(text, white):
    return sum(VALUES[c.lower()] * (1 if c.isupper() == white else -1) for c in text if c != '-')


def first_run(values, predicate, start=1):
    length = 0
    for i in range(start, len(values)):
        length = length + 1 if predicate(values[i]) else 0
        if length == 5:
            return i - 4
    return None


def scan(meta, replay, labelled, fixed):
    side = 'white' if meta['whitePlayerId'] == OURS else 'black'
    other = 'black' if side == 'white' else 'white'
    assert meta[side + 'PlayerId'] == OURS and meta[other + 'PlayerId'] != OURS and meta[side + 'Version'] == 38
    white = side == 'white'
    score = .5 if meta['result'] == '1/2-1/2' else float(meta['result'] == ('1-0' if white else '0-1'))
    frames = replay['frames']
    assert len(frames) == meta['plies'] + 1 == len(labelled['moves']) + 1
    values = [material(f['board'], white) for f in frames]
    onset = first_run(values, lambda x: x <= -3)
    # The exact earlier 337 expression, independent of the streaming code.
    old_predicate = next((i for i in range(1, len(frames) - 4) if max(values[i:i + 5]) <= -3), None)
    assert onset == old_predicate
    crossing = next((i for i, value in enumerate(values) if value <= -3), None)
    tail = 0
    for value in reversed(values):
        if value > -3:
            break
        tail += 1
    event = None
    recovery = reaches_even = None
    if onset is not None:
        before, after = frames[onset - 1], frames[onset]
        move = after['move']
        src, dst = chess.parse_square(move[:2]), chess.parse_square(move[2:4])
        mover_white = onset % 2 == 1
        assert mover_white != white, (meta['id'], 'first deficit can only worsen on opponent turn')
        piece = before['board'][src].lower()
        capture = 'capture' in labelled['moves'][onset - 1]['tags']
        victim, victim_square = fixed.captured_piece(chess.Board(fixed.fen(before['board'])), chess.Board(fixed.fen(after['board'])), move)
        assert capture == (victim is not None)
        promotion_gain = VALUES[move[4]] - 1 if len(move) == 5 else 0
        assert capture or promotion_gain > 0
        assert values[onset] - values[onset - 1] == -(VALUES[victim.symbol().lower()] if victim else 0) - promotion_gain
        decision_available = onset >= 2
        previous_move = frames[onset - 1]['move'] if decision_available else None
        at_previous_destination = capture and previous_move is not None and chess.parse_square(previous_move[2:4]) == victim_square
        assert at_previous_destination == ('victim_walked_in' in labelled['moves'][onset - 1]['tags'])
        hidden = frames[onset - 2][side][src] == '?' if decision_available else None
        distance = chess.square_distance(src, dst)
        enemy_home_half = chess.square_rank(src) >= 4 if white else chess.square_rank(src) <= 3
        facets = ['opponent_capture' if capture else 'opponent_quiet_promotion']
        if hidden:
            facets.append('capturer_hidden_before_our_choice')
        if at_previous_destination:
            facets.append('victim_at_previous_uci_destination')
        if piece in 'brq':
            facets.append('slider')
        if enemy_home_half:
            facets.append('origin_in_opponent_home_half')
        if distance >= 3:
            facets.append('move_distance_at_least_three')
        event = dict(ply=onset, reply=move, piece=piece, capture=capture, victim=victim.symbol().lower() if victim else None,
                     victim_square=chess.square_name(victim_square) if victim_square is not None else None,
                     before=values[onset - 1], after=values[onset], promotion_gain=promotion_gain,
                     hidden_before_previous_own_move=hidden, victim_at_previous_uci_destination=at_previous_destination,
                     origin_in_opponent_home_half=enemy_home_half, distance=distance, facets=facets,
                     actor_input=dict(ply=onset - 2, observation=frames[onset - 2][side], own_move=previous_move) if decision_available else None,
                     preceding_own_move_tags=labelled['moves'][onset - 2]['tags'] if decision_available else None)
        recovery = first_run(values, lambda x: x > -3, start=onset + 5)
        naive_recovery = next((i for i in range(onset + 5, len(values) - 4) if min(values[i:i + 5]) > -3), None)
        assert recovery == naive_recovery
        reaches_even = next((i for i in range(onset + 5, len(values)) if values[i] >= 0), None)
    return dict(game=meta['id'], side=side, version=38, opponent_id=meta[other + 'PlayerId'], opponent=meta[other],
                opponent_version=meta[other + 'Version'], score=score, reason=meta['reason'], plies=meta['plies'],
                material_trajectory=values, first_crossing=crossing, onset=event, final_material=values[-1],
                five_frame_recovery_ply=recovery, first_later_even_ply=reaches_even,
                short_deficit_tail_without_five_frame_onset=onset is None and 0 < tail < 5,
                deficit_crossing_without_five_frame_onset=onset is None and crossing is not None)


def summarize(rows):
    onsets = [r for r in rows if r['onset'] is not None]
    hidden_captures = [r for r in onsets if r['onset']['capture'] and r['onset']['hidden_before_previous_own_move'] is True]
    return dict(games=len(rows), wins=sum(r['score'] == 1 for r in rows), draws=sum(r['score'] == .5 for r in rows), losses=sum(r['score'] == 0 for r in rows),
                moves=sum((r['plies'] + (r['side'] == 'white')) // 2 for r in rows),
                any_three_point_deficit=sum(r['first_crossing'] is not None for r in rows), five_frame_deficit=len(onsets),
                crossing_without_five_frame_onset=sum(r['deficit_crossing_without_five_frame_onset'] for r in rows),
                short_deficit_tail_without_five_frame_onset=sum(r['short_deficit_tail_without_five_frame_onset'] for r in rows),
                median_onset_ply=median(r['onset']['ply'] for r in onsets) if onsets else None,
                median_plies_from_onset_to_end=median(r['plies'] - r['onset']['ply'] for r in onsets) if onsets else None,
                onset_by_ply_20=sum(r['onset']['ply'] <= 20 for r in onsets),
                five_frame_recovery=sum(r['five_frame_recovery_ply'] is not None for r in onsets),
                later_reaches_even=sum(r['first_later_even_ply'] is not None for r in onsets),
                capture_onsets=sum(r['onset']['capture'] for r in onsets), hidden_capture_onsets=len(hidden_captures),
                hidden_capture_takes_previous_destination=sum(r['onset']['victim_at_previous_uci_destination'] for r in hidden_captures),
                hidden_capture_piece_types=dict(Counter(r['onset']['piece'] for r in hidden_captures)),
                hidden_capture_victim_types=dict(Counter(r['onset']['victim'] for r in hidden_captures)),
                hidden_far_home_half_slider_takes_previous_destination=sum(r['onset']['victim_at_previous_uci_destination'] and r['onset']['piece'] in 'brq' and r['onset']['origin_in_opponent_home_half'] for r in hidden_captures))


def main():
    def timeout(*_):
        raise TimeoutError('material-onset descriptive review exceeded 60 seconds')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(60)
    started = time.monotonic()
    listing = read(FIELD / 'listing.json')
    selected = [r for r in listing if OURS in (r['whitePlayerId'], r['blackPlayerId'])]
    assert len(selected) == 345
    selected_ids = {r['id'] for r in selected}
    dependencies = [Path(__file__), PATCH, OLD_SOURCE, OLD_ROWS, FIELD / 'listing.json', FIELD / 'validation.jsonl', TAX / 'games.jsonl',
                    ROOT / 'astra-submissions/analysis/field-taxonomy-20261111/result.json',
                    ROOT / 'astra-submissions/analysis/field-taxonomy-20261111/review.json']
    taxonomy_review = read(dependencies[-1])
    assert taxonomy_review['status'] == 'complete'
    assert sha(dependencies[-2]) == taxonomy_review['result_sha256']
    assert sha(TAX / 'games.jsonl') == read(dependencies[-2])['artifacts'][str((TAX / 'games.jsonl').relative_to(ROOT))]
    OUT.mkdir(exist_ok=False)
    STORE.mkdir(exist_ok=False)
    plan = dict(at=datetime.now(timezone.utc).isoformat(), game_ids=[r['id'] for r in selected], wall_seconds=60,
                selection='All 345 v38 game seats in the frozen 6000-game listing, all outcomes and lengths; no new or isolated held-out cohort.',
                definition='First frame i>=1 whose material balance is <=-3 in all five frames i..i+4, exactly as 337. Integer P/N/B/R/Q/K values 1/3/3/5/9/0.',
                recovery='First five-frame run above -3 after the deficit window; separately record any later return to at least even material.',
                diagnostics='First crossing, insufficient five-frame deficits, onset timing, exact captures/promotions, input-view visibility, preceding UCI destination, piece roles and source home half. No intention or safety claim.',
                dependencies={str(p): sha(p) for p in dependencies},
                scope='Local retrospective curation. No bot replay/search, safe-reply enumeration, new game, fit, GPU, train/test split, candidate, shared-report edit, commit, push or deployment.')
    save(OUT / 'plan.json', plan)
    state = dict(at=datetime.now(timezone.utc).isoformat(), status='running', completed=0, plan_sha256=sha(OUT / 'plan.json'))
    try:
        spec = importlib.util.spec_from_file_location('onset_fixed_capture_labels', PATCH)
        fixed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixed)
        labels = {}
        with (TAX / 'games.jsonl').open() as stream:
            for line in stream:
                row = json.loads(line)
                if row['id'] in selected_ids:
                    labels[row['id']] = row
        assert set(labels) == selected_ids
        valid = {r['id']: r for r in map(json.loads, (FIELD / 'validation.jsonl').read_text().splitlines())}
        old = {r['game']: r for r in read(OLD_ROWS)}
        rows, overlap = [], []
        for meta in selected:
            path = FIELD / 'raw/games' / meta['id'] / 'replay.json'
            digest = sha(path)
            assert digest == valid[meta['id']]['replay_sha256'] == labels[meta['id']]['replay_sha256']
            assert labels[meta['id']]['metadata'] == meta
            row = scan(meta, read(path), labels[meta['id']], fixed)
            row.update(replay_sha256=digest, sequence_sha256=labels[meta['id']]['sequence_sha256'])
            if meta['id'] in old:
                earlier = old[meta['id']]
                assert row['side'] == earlier['side'] and row['score'] == earlier['score'] and row['first_crossing'] == earlier['first_crossing'] and row['final_material'] == earlier['final_material']
                assert (row['onset']['ply'] if row['onset'] else None) == (earlier['onset']['ply'] if earlier['onset'] else None)
                if row['onset']:
                    for key in ('piece', 'capture', 'before', 'after', 'hidden_before_previous_own_move'):
                        assert row['onset'][key] == earlier['onset'][key]
                overlap.append(row['game'])
            rows.append(row)
            state['completed'] += 1
        for path, digest in plan['dependencies'].items():
            assert sha(Path(path)) == digest, path
        save(STORE / 'rows.json', rows)
        by_outcome = {name: summarize([r for r in rows if r['score'] == score]) for name, score in [('wins', 1), ('draws', .5), ('losses', 0)]}
        groups = defaultdict(list)
        for row in rows:
            groups[(row['opponent_id'], row['opponent_version'], row['side'])].append(row)
        result = dict(at=datetime.now(timezone.utc).isoformat(), plan_sha256=sha(OUT / 'plan.json'), games=len(rows), frames=sum(r['plies'] + 1 for r in rows),
                      full_sequence_count=len({r['sequence_sha256'] for r in rows}), by_outcome=by_outcome,
                      opponent_version_color=[dict(opponent_id=k[0], opponent_version=k[1], side=k[2], opponent=v[0]['opponent'], **summarize(v)) for k, v in sorted(groups.items(), key=lambda x: repr(x[0]))],
                      prior_337_game_id_overlap=overlap, rows_sha256=sha(STORE / 'rows.json'), scope=plan['scope'],
                      limitations=['Five frames is a retrospective horizon, not a guarantee a deficit lasts to the end or caused the result.',
                                   'A game ending before five recorded low-material frames can lack an onset despite a terminal deficit.',
                                   'Input-view visibility does not establish belief support, posterior weight or what alternatives the policy considered.',
                                   'Previous-destination facets use the UCI destination, so secondary rook movement in castling is not included.',
                                   'Opponent schedules, colors, versions and repeated/exposed trajectories prevent causal or pristine-holdout claims.',
                                   'No safe alternatives, intentional sacrifice, forced line or calibrated failure probability are established.'])
        assert (by_outcome['wins']['games'], by_outcome['draws']['games'], by_outcome['losses']['games']) == (184, 17, 144)
        save(OUT / 'result.json', result)
        state.update(status='complete', result_sha256=sha(OUT / 'result.json'))
        print(json.dumps(dict(games=len(rows), frames=result['frames'], prior_337_overlap=len(overlap), by_outcome=by_outcome), indent=2), flush=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=datetime.now(timezone.utc).isoformat(), seconds=time.monotonic() - started)
        save(OUT / 'execution.json', state)


if __name__ == '__main__':
    main()
