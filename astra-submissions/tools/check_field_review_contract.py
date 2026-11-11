"""Check the prepared data review on in-memory corruptions of one fixture.

No stored replay, source plan, collector or model is changed.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import verify_field_replays as review


def main():
    listing = review.read(review.STORE / 'listing.json')[0]
    path = review.STORE / 'raw/games' / listing['id'] / 'replay.json'
    original = review.read(path)
    ingest, referee = review.load_rules()
    checks = []
    base = review.verify_game(original, listing, ingest, referee)
    checks.append(dict(name='valid_source_accepted', pass_=True, frames=base['frames']))

    def reject(name, change):
        sample = deepcopy(original)
        change(sample)
        try:
            review.verify_game(sample, listing, ingest, referee)
        except AssertionError:
            checks.append(dict(name=name, pass_=True))
        else:
            raise AssertionError('corrupt fixture accepted: ' + name)

    reject('wrong_private_view_rejected', lambda r: r['frames'][1].__setitem__('white', '?' * 64))
    reject('wrong_true_board_rejected', lambda r: r['frames'][1].__setitem__('board', '-' * 64))
    reject('illegal_recorded_move_rejected', lambda r: r['frames'][1].__setitem__('move', 'a1a8'))
    reject('nonfinite_clock_rejected', lambda r: r['frames'][1]['clocks'].__setitem__(0, float('nan')))
    reject('wrong_played_version_rejected', lambda r: r.__setitem__('whiteVersion', r['whiteVersion'] + 1))
    cached = deepcopy(original)
    cached['whiteCurrentVersion'] = 999
    cached['blackCurrentVersion'] = 999
    assert review.verify_game(cached, listing, ingest, referee) == base
    checks.append(dict(name='mutable_current_versions_not_confused_with_played_versions', pass_=True))
    timing = deepcopy(original)
    timing['frames'][1]['clocks'][1] += 1
    flagged = review.verify_game(timing, listing, ingest, referee)
    assert flagged['clocks']['nonmoving_clock_changes'] > base['clocks']['nonmoving_clock_changes']
    checks.append(dict(name='finite_timing_anomaly_reported_without_repair', pass_=True))
    result = dict(at=datetime.now(timezone.utc).isoformat(), checks=checks, passed=len(checks),
                  source_sha256={str(p): review.sha(p) for p in [Path(__file__), Path(review.__file__), path]},
                  plan_sha256=review.sha(review.OUT / 'review-plan.json'),
                  scope='In-memory data-auditor contract checks. Source replays and frozen plan unchanged. No model, inference, game, collection restart, network or deployment.')
    review.save(review.OUT / 'review-contract-checks.json', result)
    print(json.dumps(dict(checks_passed=len(checks), source_game=listing['id'], frozen_plan_unchanged=True)))


if __name__ == '__main__':
    main()
