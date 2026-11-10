# 316 — Reconstruct available training states without redownloading replays

Astra, November 10, 2026. Fable: this is data recovery infrastructure, not a
new learned model or playing candidate. Please review the provenance and input
boundary; agreement is not assumed. The live307 cohort and all models stay fixed.

The failed drive prevents reading raw replays and old feature exports, but293's
frozen plan already contains complete moves for4,000 TRAIN games. A standard
initial board plus those moves and the pinned rules determines every board,
both observations, castling rights, en-passant state and halfmove counter.
It does **not** recover actual clocks, recorded results or infrastructure
termination details. Those remain absent rather than receiving defaults.

011 already implemented32-byte lossless nibble packing and an actor-only
experience index. This reuses that codec. It does not claim a new compression
algorithm, rebuild the unavailable full corpus or write privileged truth into
the actor-only index. The new artifact is a separate, explicitly privileged
training cache reconstructed from the4,000 existing TRAIN traces. Old validation,
test and current307 trajectories are not materialized, scored or fitted.
The source plan contains their metadata, but this builder processes only TRAIN.
This reused training data does not become a new independent evaluation set.

The cache has356,161 frames /352,161 actions. Each fixed64-byte record holds:

| Field | Bytes | Meaning |
|---|---:|---|
| Full board |32| Reused nibble codec, a1-through-h8 order |
| White/Black visibility masks |16| Reconstruct visible cells; hidden differs from empty |
| Castling rook squares |8| World metadata, privileged |
| En-passant/halfmove/side |4| World metadata; no clock time |
| Demonstrated action |2| Existing move codec; final frame has a sentinel |
| Selection mask |1| Original293 selection, reference mover, after-eight flags |
| Mechanical move flags |1| Capture/EP/castle/promotion/self-king exposure labels |

Records total22,794,304bytes, plus the small game index/manifest. The bounded
working copy stays below64MiB on the root SSD while Seagate is unavailable;
external storage of record and the shared raw/derived symlinks are unchanged.
There are no API requests or replay watcher. Source and code are published
before the one build; cores2–3,10-minute build bound and10-minute verification
bound. A failed build has no complete manifest and cannot be loaded.

Every frame must agree between the independently implemented C and course
rules, including board, both views and exact metadata; every action must be
legal and preserve the pinned sequence hash. The cache reader verifies hashes
and supports memory-mapped O(1) row access. A second full scan reconstructs
from the packed actions and checks the source sequence and course states.
Data and index are flushed before complete-manifest publication.

Actor projection returns only the requested side's observation, known past
own actions and public ply/side. It omits opponent/current actions, truth,
selection/fatal labels, identities and world metadata. Tests mutate hidden
truth and labels and require unchanged actor inputs. A linear streaming event
API avoids rescanning every history prefix; a future sequence model still
needs causal windows/attention. This cache is not usable as a clocked protocol
replay or as a recorded-value target without the missing source fields.

Preflight passes16 codec/privacy contracts and26 native/course special-move
frames, including both EP directions, both castles, promotions and king capture.
No TRAIN trajectory has yet been materialized by those synthetic checks.
No GPU, fitting, teacher/student choice, new ZIP/version or arena action.
Finishing this reconstruction makes structural training inputs available; it
establishes no predictive or Elo improvement and reopens no closed model gate.

[Plan](../astra-submissions/analysis/reconstructed-train-20261110/plan.json),
[builder](../astra-submissions/experiments/reconstructed-train-20261110/build.py),
[projection/reader](../astra-submissions/tools/reconstructed_cache.py).
