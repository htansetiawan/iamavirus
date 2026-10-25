import random

import pytest

from learning.rl_train import (Member, bound_snapshot_sampling,
                               sample_member_index, validate_group_weights)


def members():
    return [
        Member("duck", object(), 1.0, "targets"),
        Member("instructors", object(), 1.0, "targets"),
        Member("ta-p", object(), 1.0, "ta"),
        Member("leader", object(), 1.0, "leaders"),
        Member("snapshot-0", object(), 1.0, "self_play"),
        Member("snapshot-1", object(), 1.0, "self_play"),
    ]


def test_group_sampling_preserves_configured_quota_independent_of_member_count():
    league = members()
    weights = {"targets": 0.40, "ta": 0.25, "leaders": 0.20, "self_play": 0.15}
    validate_group_weights(league, weights)
    rng = random.Random(12345)
    counts = {group: 0 for group in weights}
    per_member = {member.name: 0 for member in league}
    for _ in range(100_000):
        member = league[sample_member_index(league, rng, weights)]
        counts[member.group] += 1
        per_member[member.name] += 1
    for group, expected in weights.items():
        assert counts[group] / 100_000 == pytest.approx(expected, abs=0.006)
    # Uniform sampling within the two-member groups remains explicit.
    assert per_member["duck"] / (per_member["duck"] + per_member["instructors"]) == pytest.approx(0.5, abs=0.01)
    assert per_member["snapshot-0"] / (per_member["snapshot-0"] + per_member["snapshot-1"]) == pytest.approx(0.5, abs=0.01)


def test_legacy_flat_member_weights_remain_unchanged_without_group_config():
    league = [Member("one", object(), 1.0), Member("three", object(), 3.0)]
    rng = random.Random(808)
    counts = [0, 0]
    for _ in range(40_000):
        counts[sample_member_index(league, rng)] += 1
    assert counts[0] / sum(counts) == pytest.approx(0.25, abs=0.01)


def test_unavailable_group_is_renormalized_without_invalidating_remaining_mix():
    league = [Member("a", object(), 1.0, "a"), Member("b", object(), 1.0, "a")]
    weights = {"a": 0.4, "empty": 0.6}
    rng = random.Random(1)
    assert {sample_member_index(league, rng, weights) for _ in range(100)} == {0, 1}


def test_snapshot_sampling_capacity_keeps_indices_stable_and_disables_old_members():
    league = [Member("anchor", object(), 1.0, "leaders")]
    league.extend(Member(f"snapshot-{i}", object(), 1.0, "self_play") for i in range(10))
    original_names = [m.name for m in league]
    bound_snapshot_sampling(league, 6)
    assert [m.name for m in league] == original_names
    assert [m.name for m in league if m.group == "self_play" and m.weight > 0] == [
        f"snapshot-{i}" for i in range(4, 10)
    ]
    weights = {"leaders": 0.85, "self_play": 0.15}
    rng = random.Random(99)
    sampled = {league[sample_member_index(league, rng, weights)].name for _ in range(1000)}
    assert not sampled.intersection({f"snapshot-{i}" for i in range(4)})


@pytest.mark.parametrize("weights", [
    {"a": 0.4, "b": 0.5},
    {"a": -0.1, "b": 1.1},
    {"a": float("nan"), "b": 0.0},
])
def test_invalid_group_weights_fail_before_rollout(weights):
    with pytest.raises(ValueError):
        validate_group_weights([Member("x", object(), 1.0, "a")], weights)
