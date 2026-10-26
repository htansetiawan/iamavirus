"""The rating lookup behind the daily point-flow table: pre-game ratings come from the latest
snapshot strictly before the game, never a later one (the defect found 26 October)."""
import datetime as dt
import json
import sys

import pytest

from learning.daily_insights import parse_utc, rating_before

U = dt.timezone.utc


def test_parse_utc_reads_snapshot_names_and_created_at():
    assert parse_utc("2026-10-25T101243.632817Z0000") == dt.datetime(2026, 10, 25, 10, 12, 43, 632817, tzinfo=U)
    assert parse_utc("2026-10-21T12:00:03.136818998+00:00") == dt.datetime(2026, 10, 21, 12, 0, 3, 136818, tzinfo=U)
    assert parse_utc("garbage") is None
    assert parse_utc(None) is None


def test_rating_before_uses_only_prior_snapshots():
    s = [(dt.datetime(2026, 10, 20, tzinfo=U), 1900.0), (dt.datetime(2026, 10, 22, tzinfo=U), 1950.0)]
    assert rating_before(s, dt.datetime(2026, 10, 19, tzinfo=U)) is None            # before the first snapshot
    assert rating_before(s, dt.datetime(2026, 10, 21, tzinfo=U))[1] == 1900.0       # between: the earlier one
    assert rating_before(s, dt.datetime(2026, 10, 22, tzinfo=U))[1] == 1900.0       # at a snapshot: strictly before
    assert rating_before(s, dt.datetime(2026, 10, 25, tzinfo=U))[1] == 1950.0       # after the last
    assert rating_before([], dt.datetime(2026, 10, 25, tzinfo=U)) is None


def test_offsets_and_subsecond_ordering():
    snapshot = parse_utc("2026-10-21T120003.100000Z0000")
    game = parse_utc("2026-10-21T08:00:03.900000-04:00")
    assert game == dt.datetime(2026, 10, 21, 12, 0, 3, 900000, tzinfo=U)
    assert rating_before([(snapshot, 1900)], game) == (snapshot, 1900)
    assert parse_utc("20261021T120003Z") == dt.datetime(2026, 10, 21, 12, 0, 3, tzinfo=U)


@pytest.mark.parametrize("text", [None, "garbage", "2026-02-30T12:00:00Z",
    "2026-10-21T12:00:00garbage", "2026-10-21T12:00:00", "2026-10-21", 123])
def test_invalid_instants_are_missing(text):
    assert parse_utc(text) is None
    assert rating_before([(dt.datetime(2026, 10, 21, tzinfo=U), 1900)], parse_utc(text)) is None


def test_empty_snapshot_report_and_invalid_listing(tmp_path, monkeypatch):
    from learning import daily_insights
    raw = tmp_path / "raw"
    game = raw / "games" / "bad-date"
    game.mkdir(parents=True)
    (game / "listing.json").write_text(json.dumps({"createdAt": "2026-02-30T12:00:00Z"}))
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["daily_insights", "--raw", str(raw), "--out", str(out)])
    daily_insights.main()
    report = (out / "insights-latest.md").read_text()
    assert "latest snapshot (none)" in report
    assert "0 games of all teams" in report
