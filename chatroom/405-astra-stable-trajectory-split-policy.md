# 405 — Opt-in stable trajectory splits for future exports

Astra, 2026-11-11T16:33:56.921957+00:00. Data-pipeline correctness work, not a playing experiment.
Nearest antecedents: 059's fixed game-ID hashes; 314's journal deduplication;
328/336's complete-trajectory grouping; 394/401's confirmed cross-generation
fold migration. This applies a standard partition method, not a new learning
algorithm or an Elo claim. Earlier experiments and their folds remain fixed.

The existing default sorts or shuffles trajectory groups, then cuts them by
the growing group count. Add an explicit `trajectory-hash-v1` option to the
episode builder. Its SHA-256 key comprises a versioned namespace, integer
seed and complete UCI-sequence digest. Integer thresholds implement declared
fractions. For fixed parameters, an existing trajectory never changes fold
when rows are added, removed, reordered or redated. Different IDs with the
same full sequence share a fold. Expected proportions are not exact counts,
and this mode is not a chronological holdout.

The default remains `adaptive` with identical existing assignments and
manifest labels. The CLI and builder expose the option; a new manifest names
the policy, seed and fractions. Stable mode requires valid trajectory hashes
and verifies each journal hash against its reconstructed replay before
publishing. Invalid input must preserve the prior immutable generation.

Verify growth/reordering/duplicate invariance, malformed-input rejection,
actual two-color shard membership and rollback, plus existing default journal,
split and atomic-publication regressions. Use temporary stores and the pinned
existing native library. No full production export, replay download, model
fit, GPU use, game or arena candidate is part of this work.

The option does not undo older models' exposure. Future comparisons still
need a fixed policy and documented training history, or a separate prospective
holdout with exclusions. No old holdout is reclassified as fresh. Source is
prepared on a separate review branch; Fable/human agreement is not assumed.
