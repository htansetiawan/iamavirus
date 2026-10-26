"""Identical games cannot leak into a later chronological holdout."""
from learning.dataset import assign_splits


def test_duplicate_sequence_follows_latest_completion_into_holdout():
    rows = [{'id': str(i), 'moves_sha256': str(i), 'createdAt': f'2026-10-{10+i:02d}T00:00:00Z'}
            for i in range(10)]
    rows.append({'id': 'early-copy', 'moves_sha256': '9', 'createdAt': '2026-10-01T00:00:00Z'})
    assignments = assign_splits(rows)
    assert all(assignments[str(i)] == 'train' for i in range(8))
    assert assignments['8'] == 'validation'
    assert assignments['9'] == assignments['early-copy'] == 'test'
