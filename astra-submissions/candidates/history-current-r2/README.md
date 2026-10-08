# Integration with Fable's capture persistence

This supersedes the first `history-current` integration patch for root revision
`097eaecb56b31af1b26bab76587640e35859ac6b`. It includes Fable's `9c2c673`
capture-persistence implementation unchanged. The root checkout is not edited.
The earlier source and receipts remain available for reproducibility.

`port.patch` changes only `belief.h`, `belief.cc`, `engine.h` and `engine.cc`.
Its SHA-256 is
`d303d07b505a78b0e8527268d8b00830af7ea9ecd41510ce99c77d41fd6084f4`.
It passes `git apply --check` against the pinned revision. Recheck if root
changes again; do not overwrite Fable's implementation with these snapshots.

The single shared previous observation, deterministic capture evidence,
en passant capture ambiguity handling, and two-update probabilistic persistence
are retained. Strict filtering and history checkpoints require only the current
deterministic capture square. Recent capture locations remain a soft recovery
prior; they are not promoted to facts.

Modes retain the earlier meaning:

| `FOW_HISTORY_MODE` | Behavior |
| --- | --- |
| 0, default | Existing filter, with own-move particle/memory alignment and empty-successor fixes |
| 1 | Exact actor observation and previous-mover survival, plus recovery of inferred/known en passant metadata |
| 2 | Experimental bounded history recovery, still off |

Mode 2 is not recommended: the separate 634-seat gate improved average belief
metrics but missed more terminal threats. Mode 1 requires its own decision gate.
Mode 0 should preserve choices outside the repaired defects; universal identity
cannot hold when fixing a surviving particle's previously misaligned memory.

Build without mutating root:

```sh
taskset -c 2 python3 astra-submissions/tools/build_current_history_runtime.py \
  --source astra-submissions/candidates/history-current-r2 \
  --output astra-submissions/build/NEW_DIRECTORY
```

Add `--control` for the unchanged pinned root. The builder freezes root sources
from Git and records all source and binary hashes. Use the root-compatible
features-v2 neural export if running its hybrid benchmark; archived v1 weights
have a different input contract.

The isolated combined implementation passes **541 root belief checks, 622
engine checks, and 3,129 focused history checks: 4,292 total, zero failures**.
The root capture-persistence regression retains 227/256 capturers, matching
Fable's report. The focused tests also cover current capture evidence across
priors, seeds, strict/history modes, castling memory alignment, promotions, and
en passant recovery. See the
[correctness receipt](../../analysis/history-current-r2/correctness.json).
These are correctness checks, not playing-strength evidence or a release.
