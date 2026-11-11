"""Reconcile the fixed onset scan and export explicitly separated case fields.

Original scan artifacts stay immutable. The event view replaces the overly
narrow 'capturer hidden' facet with 'source hidden', also valid for quiet
promotions, and separates the recorded candidate action from observations.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'astra-submissions/analysis/field-material-onsets-20261111'
STORE = ROOT / 'data/astra-spool/field-material-onsets-20261111'
FIELD = ROOT / 'data/astra-spool/field-snapshot-20261111'
VALUES = dict(P=1, N=3, B=3, R=5, Q=9, K=0)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    plan, result, execution = [read(OUT / name) for name in ('plan.json', 'result.json', 'execution.json')]
    assert execution['status'] == 'complete' and execution['completed'] == 345 and execution['ended_at']
    assert execution['seconds'] <= plan['wall_seconds'] == 60
    assert execution['result_sha256'] == sha(OUT / 'result.json')
    assert execution['plan_sha256'] == result['plan_sha256'] == sha(OUT / 'plan.json')
    assert result['rows_sha256'] == sha(STORE / 'rows.json')
    for path, digest in plan['dependencies'].items():
        assert sha(Path(path)) == digest, path
    rows = read(STORE / 'rows.json')
    assert [r['game'] for r in rows] == plan['game_ids'] and len(rows) == len({r['game'] for r in rows}) == 345
    events, controls = [], []
    quiet_promotions = 0
    renamed_hidden_facets = 0
    frames = 0
    for row in rows:
        path = FIELD / 'raw/games' / row['game'] / 'replay.json'
        assert sha(path) == row['replay_sha256']
        raw = read(path)
        sequence = ' '.join(f['move'] for f in raw['frames'][1:])
        assert hashlib.sha256(sequence.encode()).hexdigest() == row['sequence_sha256']
        trajectory = []
        for frame in raw['frames']:
            count = Counter(frame['board'])
            white = sum(v * (count[p] - count[p.lower()]) for p, v in VALUES.items())
            trajectory.append(white if row['side'] == 'white' else -white)
        assert trajectory == row['material_trajectory']
        onset = next((i for i in range(1, len(trajectory) - 4) if all(x <= -3 for x in trajectory[i:i + 5])), None)
        assert onset == (row['onset']['ply'] if row['onset'] else None)
        frames += len(trajectory)
        if onset is None:
            controls.append(dict(game=row['game'], side=row['side'], score=row['score'], first_crossing=row['first_crossing']))
            continue
        event = row['onset']
        assert event['before'] == trajectory[onset - 1] and event['after'] == trajectory[onset]
        assert event['reply'] == raw['frames'][onset]['move']
        source = event['reply'][:2]
        sq = ord(source[0]) - 97 + 8 * (int(source[1]) - 1)
        assert raw['frames'][onset - 1]['board'][sq].lower() == event['piece']
        decision = event['actor_input']
        assert decision and decision['ply'] == onset - 2
        assert decision['observation'] == raw['frames'][onset - 2][row['side']]
        assert decision['own_move'] == raw['frames'][onset - 1]['move']
        assert event['hidden_before_previous_own_move'] == (decision['observation'][sq] == '?')
        facets = ['source_hidden_before_our_choice' if f == 'capturer_hidden_before_our_choice' else f for f in event['facets']]
        renamed_hidden_facets += 'capturer_hidden_before_our_choice' in event['facets']
        if not event['capture']:
            quiet_promotions += 1
            assert event['piece'] == 'p' and len(event['reply']) == 5 and event['victim'] is None
        events.append(dict(schema='material-onset-event-v2', game=row['game'], side=row['side'],
                           metadata=dict(opponent=row['opponent'], opponent_id=row['opponent_id'], opponent_version=row['opponent_version'], result_score=row['score']),
                           decision_observation=dict(ply=decision['ply'], board_view=decision['observation']),
                           recorded_candidate_action=decision['own_move'],
                           hindsight=dict(onset_ply=onset, reply=event['reply'], source_piece=event['piece'], victim=event['victim'],
                                          capture=event['capture'], material_before=event['before'], material_after=event['after'],
                                          source_hidden_before_choice=event['hidden_before_previous_own_move'],
                                          five_frame_recovery_ply=row['five_frame_recovery_ply'], later_even_ply=row['first_later_even_ply'],
                                          preceding_own_move_tags=event['preceding_own_move_tags'], facets=facets),
                           replay_sha256=row['replay_sha256'], sequence_sha256=row['sequence_sha256']))
    assert frames == result['frames'] == 30945
    assert len(events) == 142 and len(controls) == 203 and quiet_promotions == 5
    for name, score in [('wins', 1), ('draws', .5), ('losses', 0)]:
        group = [r for r in rows if r['score'] == score]
        onsets = [r for r in group if r['onset']]
        hidden = [r for r in onsets if r['onset']['capture'] and r['onset']['hidden_before_previous_own_move'] is True]
        expected = result['by_outcome'][name]
        assert expected['games'] == len(group) and expected['five_frame_deficit'] == len(onsets)
        assert expected['hidden_capture_onsets'] == len(hidden)
        assert expected['hidden_capture_takes_previous_destination'] == sum(r['onset']['victim_at_previous_uci_destination'] for r in hidden)
        assert expected['five_frame_recovery'] == sum(r['five_frame_recovery_ply'] is not None for r in onsets)
        assert expected['later_reaches_even'] == sum(r['first_later_even_ply'] is not None for r in onsets)
        assert expected['median_onset_ply'] == (median(r['onset']['ply'] for r in onsets) if onsets else None)
        assert expected['median_plies_from_onset_to_end'] == (median(r['plies'] - r['onset']['ply'] for r in onsets) if onsets else None)
        assert expected['hidden_capture_piece_types'] == dict(Counter(r['onset']['piece'] for r in hidden))
        assert expected['hidden_capture_victim_types'] == dict(Counter(r['onset']['victim'] for r in hidden))
    save(STORE / 'event-view-v2.json', dict(schema='material-onset-event-v2', events=events, game_controls_without_onset=controls,
         input_contract='Only decision_observation is the directly recorded observation. recorded_candidate_action is an action being assessed or an imitation target, not a known pre-choice policy input. All hindsight fields are offline labels; metadata is for reporting. Controls are game-level, not matched negative decisions.'))
    review = dict(at=datetime.now(timezone.utc).isoformat(), status='complete', games=345, frames=frames,
                  event_rows=len(events), game_controls=len(controls), quiet_promotion_onsets=quiet_promotions,
                  generic_hidden_source_facets=renamed_hidden_facets, prior_337_overlap=len(result['prior_337_game_id_overlap']),
                  checks=['All source/result/journal hashes and original execution complete within original cap.',
                          'Every saved replay hash and complete move sequence checked.',
                          'Material trajectories rederived from symbol counts and every five-frame onset checked.',
                          'All event observations, candidate actions, source pieces and decision-time visibility checked against raw frames.',
                          'Outcome-group event counts, captures, victims, recoveries and medians independently reduced.'],
                  normalization='Original scan/metrics preserved. V2 replaces the capturer-specific hidden facet with generic source visibility, also correct for quiet promotions; candidate action is separated from observation.',
                  source_sha256=sha(Path(__file__)), original_result_sha256=sha(OUT / 'result.json'),
                  original_rows_sha256=sha(STORE / 'rows.json'), event_view_sha256=sha(STORE / 'event-view-v2.json'),
                  scope='Local data review/schema clarification only. No model, actor-feature promotion, matched-negative dataset, bot search, safe-reply enumeration, game, commit, push or deployment.')
    save(OUT / 'review.json', review)
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
