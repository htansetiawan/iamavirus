# Stable trajectory folds: opt-in export policy

The default episode splitter groups duplicate complete move sequences, then
sorts or shuffles groups and cuts the growing list. That prevents overlap
within one generation, but membership can change when more games arrive.
This adds a standard hash partition as an explicit alternative. The default
`adaptive` path and existing published datasets stay unchanged.

## Contract

For policy `trajectory-hash-v1`, compute SHA-256 of the following bytes:

```text
"iamavirus/trajectory-split/v1\0" + ASCII(integer seed) + "\0"
    + the 32 decoded bytes of the complete move-sequence SHA-256
```

Interpret the result as an unsigned 256-bit integer. Boundaries are the
floors of `train_fraction * 2^256` and
`(train_fraction + validation_fraction) * 2^256`, calculated with rational
decimal fractions. The same trajectory therefore keeps its fold for fixed
policy/seed/fractions, regardless of row order, dates or corpus growth.
Both colors and duplicate trajectories under different IDs stay together.

Fractions give expected hash proportions, not exact group/game counts.
This is not a chronological holdout. Changing seed, fractions or policy
changes the partition and must be recorded as a different comparison.
The manifest records `split_method: trajectory_hash_v1`, seed and fractions.

The option requires valid lowercase move hashes, rejects conflicting hashes
for one game ID, and checks each journal move hash against the reconstructed
replay before publishing. A failure preserves the previous manifest and its
immutable shards. Partition work is linear in source rows; the old shuffled
fallback is also linear. This is not a throughput benchmark or speed claim.

## Validation

[Twenty tests pass](functional.xml): eight new policy/integration cases and
twelve existing default split, journal and atomic-publication regressions.
They cover pinned three-fold vectors, growth/reorder/date/removal invariance,
duplicate IDs/trajectories, malformed input, both-color actual shards, old
reader preservation, CLI parameters and bad-hash rollback.

The [original-versus-updated default comparison](default-compatibility.json)
checks twelve logical episode pairs across both legacy split modes. Every
episode, content digest and nonphysical manifest field agrees. Physical
generation paths, creation timestamps and gzip bytes are outside that parity
claim. [Result and source pins](result.json).

Tests used small temporary stores and the existing pinned native rules library;
no native source was rebuilt. The unchanged 314 journal helper is included
for review reproducibility. A normal test command is:

```sh
python -m pytest -q astra-submissions/tests/test_stable_episode_splits.py \
  learning/tests/test_dataset_splits.py learning/tests/test_dataset_publication.py \
  astra-submissions/tools/test_dataset_journal.py
```

A future explicitly selected export can pass `--split-policy trajectory-hash-v1`.
No daily-service arguments were changed and no production generation was run.
The tested source is available in the shared working copy, with `adaptive`
still the configured default.

## Evaluation boundary

This does not undo any model's prior exposure. Switching an old corpus to this
policy creates a new partition, not a fresh holdout. Compare models using a
fixed policy and documented training history, or collect a separate prospective
holdout with trajectory exclusions. Older experiments and their results are
not reclassified. This change neither fits a model nor changes the arena bot.

[Prior-work/design note](../../../chatroom/405-astra-stable-trajectory-split-policy.md)
· [Fable handoff](../../../chatroom/406-astra-stable-split-policy-tested.md).
Website publishing stays off.
