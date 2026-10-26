"""The rating lookup behind the daily point-flow table: pre-game ratings come from the latest
snapshot strictly before the game, never a later one (the defect found 26 October)."""
import datetime as dt

from learning.daily_insights import parse_utc, rating_before

U = dt.timezone.utc


def test_parse_utc_reads_snapshot_names_and_created_at():
    assert parse_utc("2026-10-25T101243.632817Z0000") == dt.datetime(2026, 10, 25, 10, 12, 43, tzinfo=U)
    assert parse_utc("2026-10-21T12:00:03.136818998+00:00") == dt.datetime(2026, 10, 21, 12, 0, 3, tzinfo=U)
    assert parse_utc("garbage") is None
    assert parse_utc(None) is None


def test_rating_before_uses_only_prior_snapshots():
    s = [(dt.datetime(2026, 10, 20, tzinfo=U), 1900.0), (dt.datetime(2026, 10, 22, tzinfo=U), 1950.0)]
    assert rating_before(s, dt.datetime(2026, 10, 19, tzinfo=U)) is None            # before the first snapshot
    assert rating_before(s, dt.datetime(2026, 10, 21, tzinfo=U))[1] == 1900.0       # between: the earlier one
    assert rating_before(s, dt.datetime(2026, 10, 22, tzinfo=U))[1] == 1900.0       # at a snapshot: strictly before
    assert rating_before(s, dt.datetime(2026, 10, 25, tzinfo=U))[1] == 1950.0       # after the last
    assert rating_before([], dt.datetime(2026, 10, 25, tzinfo=U)) is None
