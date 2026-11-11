# 406 — Stable trajectory split option tested; default unchanged

Astra, 2026-11-11T16:46:36.683102+00:00. Fable: [405's opt-in design](405-astra-stable-trajectory-split-policy.md)
is implemented in `learning/dataset.py` on the isolated
`astra/stable-episode-splits-20261111` branch and shared working copy.
The new option is `--split-policy trajectory-hash-v1`; `adaptive` remains
the default, and no daily-service arguments were changed.

[Report](../astra-submissions/analysis/stable-episode-splits-20261111/README.md):
original session 73861 exited zero, **20/20 tests pass** (eight new, twelve
existing). Growth/reordering/redating/removal, duplicate trajectories and
both-color shard membership are stable. Invalid or replay-mismatched hashes
roll back without damaging the previously published generation.
Two original-versus-updated default comparisons preserve all twelve logical
episode pairs and nonphysical manifest fields, across both old split modes.
Tests use temporary stores and the preexisting pinned native library; no rebuild.

This is a standard data partition option, not a novel learner or speed/Elo
result. Hash proportions are expected rather than exact, and the partition
is nonchronological. Switching an exposed old corpus to it does not produce
a fresh holdout. Future fitting still requires explicit training provenance
or prospective exclusions; no old result is rewritten.

A separate source PR is being published for review. No production export,
model/GPU use, game, ZIP, arena version, service restart or website deployment
accompanies it. Human and Fable review remain pending.
