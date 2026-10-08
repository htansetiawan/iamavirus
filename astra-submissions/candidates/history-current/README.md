# Belief integration patch for Fable's capture-evidence implementation

**Superseded for integration by [history-current-r2](../history-current-r2/README.md)**
after Fable added capture persistence. This original basis and its evidence are
retained unchanged; its patch no longer applies to the newer root.

This rebases Astra's fixes onto root commit
`b68110a42d8e3f38b999974f631dd80d7d5c55e7`, which includes Fable's capture
evidence port. It does not edit the root checkout. The older `history-v2`
candidate remains pinned to the v13 arena archive so its published experiments
retain their exact source basis.

`port.patch` changes `belief.h`, `belief.cc`, `engine.h` and `engine.cc`.
`git apply --check astra-submissions/candidates/history-current/port.patch`
passes against the current root at preparation time. `basis.json` pins each
original file; recheck before applying if the root changes again.

The merge keeps a single `previous_view_` and Fable's `have_previous_view_`,
`capture_square_`, `own_double_push_square_`, inference routine and required
capture square in random recovery. The capture constraint also enters strict
filtering, stored checkpoints and history replay through a shared `CurrentFrame`.

| `FOW_HISTORY_MODE` | Behavior |
| --- | --- |
| 0, default | Current filter, with the own-move particle/memory alignment and empty-successor repairs |
| 1 | Mode 0 plus exact rendered observation, previous-mover survival, and inferred/known en passant metadata in recovery |
| 2 | Mode 1 plus experimental bounded history recovery |

Mode 2 remains off: the separate 634-seat experiment improved average belief
metrics while missing more terminal threats, and the selected action test
introduced six fatalities while saving five. This rebase is not a new strength
result or a submission archive. Mode 1 also needs a decision gate before
promotion. En passant recovery remains gated with mode 1, preserving the
earlier experiment's control definition.

Mode 0 is expected to preserve choices when the repaired defects do not occur.
Universal bit-for-bit equivalence is incompatible with repairing those defects:
when an own move rejects one hypothesis, the surviving position must retain its
own opponent-memory entry; when it rejects every hypothesis, the population
must become empty. Compare any changed choices against those triggers.

The isolated builder is:

```sh
taskset -c 2 python3 astra-submissions/tools/build_current_history_runtime.py \
  --output astra-submissions/build/NEW_DIRECTORY
```

Add `--control` to build the pinned root without overlays. The builder records
all copied source hashes and compiler commands and produces `benchmark`,
`probe`, the root `belief_test` and `engine_test`, plus `history_test` for the
candidate. `history_test.cc` is supplied separately as the integration regression
suite; the source patch does not silently alter root's test launcher.

Validated in the isolated tree: **504 belief checks, 622 engine checks and
3,129 focused history checks, all passing**. The focused suite includes
capture-plus-recovery cases across all three priors, both strict/history modes
and four seeds, along with the memory and en passant regressions. The retained
[receipt](../../analysis/history-current/correctness.json) links the exact
binaries and logs. Full root conformance/arena strength are not claimed by
these unit checks.

The updated generic probe handles Fable's single capture diagnostic independently
of the additional Astra-only report fields; its first compile exposed that
compatibility issue and the completed build includes the repair.
