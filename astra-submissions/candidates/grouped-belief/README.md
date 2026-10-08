# Grouped opponent prediction

Research candidate, disabled by default. This removes duplicate-parent work and
the legacy 20,000-successor prefix cutoff while preserving the learned opponent
prior's move/capture memory. Root and Fable files are unchanged.

For parent identity `j`, let `c[j]` be its population multiplicity, `Z[j]` the
sum of priors over **all** legal moves, and `A[j]` the sum over successors
consistent with the observation. Resample parents with weight
`c[j] * A[j] / Z[j]`, then their accepted moves proportionally to their priors.
Normalizing only over accepted moves would incorrectly discard the evidence
likelihood of each parent.

Identity includes the complete board, rule metadata, last opponent destination
and capture flag. Hash collisions still require full equality. Compact
move/weight records replace stored successor boards; only selected successors
are materialized. The final shuffle moves boards and both memory arrays together.
Expected work is `O(N + U*M + N)` for `N` particles, `U` unique complete parent
identities and average `M` legal moves, rather than repeating expansion for each
duplicate. Hash lookup is expected constant time, not a worst-case guarantee.
The compact successor list has no prefix cap; worst-case storage is `O(U*M)`.

| `FOW_PREDICTION_MODE` | Behavior |
| --- | --- |
| 0, default | Legacy prediction, with diagnostic counters |
| 1 | Grouped prediction; existing strict post-filter remains independently selectable |
| 2 | Grouped prediction with exact evidence applied before resampling when history mode is nonzero |

`FOW_HISTORY_MODE` retains its existing default of 0. Mode 2 above does not enable
history rewind. Invalid history/prediction mode values log and fall back to 0,
matching Fable's current engine convention.

The analytic regressions check normalized posterior mass, learned-memory
separation, both parent storage orders, and the old prefix cutoff losing an
entire rook branch. The first build passed 3,831 focused, 541 root belief and
622 engine checks: **4,994 total, zero failures**. The final integration build
changes only invalid-environment handling in `engine.cc`; its 622 engine checks
also pass and its probe is byte-identical. See the
[correctness receipts](../../analysis/grouped-belief/correctness.json).

Build an isolated copy:

```sh
taskset -c 2 python3 astra-submissions/tools/build_current_history_runtime.py \
  --source astra-submissions/candidates/grouped-belief \
  --output astra-submissions/build/NEW_DIRECTORY
```

The source snapshot uses the historical basis in `basis.json`. For integration
with current root, use **`prediction.patch`**, based on
`c97f92c25a43a8af9d9f910ee6d0a004fba01c65`, after the history/capture repairs were
merged. Its SHA-256 is
`42b7f08b3c3bb6a5ffe33407503434477edf1b02eda9a5f3c48867ee3f352672`.
Recheck `git apply --check` as root changes. Do not copy the whole historical
engine over newer Fable work.

The [fresh replay pilot](../../analysis/grouped-belief/README.md) is encouraging
but small. This candidate has no arena release or demonstrated Elo gain.
