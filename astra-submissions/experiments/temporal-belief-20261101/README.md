# Temporal prior inside the actual belief filter

1 November2026. Isolated source; no arena candidate yet. Frozen model from the
preceding temporal-prior experiment; no fitting or model selection here.

Each hypothesis now carries a25-bit recent-opponent context in uint32:
Move16, post-promotion type3, captured value4, known1, continued1. It is
updated by that hypothesis's generated move, never the recorded hidden move.
Newly reconstructed worlds have unknown context. Shrinking, forced diagnostic
fallbacks and parallel own-move updates preserve/reset it explicitly.

Three arms use the same seed, cap20,000, temperature2, complete full-model
features, and no empirical history table:

1. `static_merged`: fitted static39+PST; ordinary board-only merging.
2. `static_context`: same static model; merge only equal board+recent context.
3. `temporal_context`: fitted temporal model; retain recent context.

The two static controls separate a representation/cap cost from learned move
likelihood. No claim is made that a fixed cap equals the arena's clock-based
thinning, or that this model includes its cheap fallback/history blend.
Original compiled-model behavior is available with ASTRA_TEMPORAL_MODEL=-1;
experimental0/1 always score the full fitted features.

18 new Nov1 games, one per opponent/observer-colour cell, are frozen in plan.
Prefer IAmAVirus observer seats where available; then fixed ID hash among
other nonrandom observers. No outcome selection. Earlier calibration,
predictive and fresh-taxonomy games/sequences are excluded. Follow the
recorded observations and own actions through at most ply80. This is a
development posterior diagnostic, not a policy comparison or an Elo estimate.

The C update API accepts only own moves and own views. Separate const probes
query truth probability and history support after the update; checksums must
be unchanged. A redacted-truth run must yield the same full posterior/RNG
checksums and king-risk estimates. The recorded opponent moves are absent
from the update input JSON; ground truth is stored separately.

First compare exact transition weights against a separately enumerated and
grouped small-state oracle, including temperature1/2, both model types,
board/context merging, shrinking, fallbacks, parallel own updates and resets.
Optimized and ASan/UBSan versions must pass. The context key mixes every bit;
the existing history_mix(value|1) is unsuitable because it erases a context
bit. A compile-time layout check verifies Candidate stays24bytes by using its
tail padding. Retained worlds add four bytes each.

Then a private-input pilot precedes the frozen54-run comparison, rotating
arms within each game on exclusive cores0–1. Per-arm timeout120seconds and
full-panel wall cap1hour. First mechanism test does not rebuild after an
empty belief; all later planned decisions remain in the support and clipped
truth-loss denominators. Report this coverage explicitly. Compare complete
board probabilities by summing all contexts of the same board.

Gate to a larger cap/clock test: temporal must improve mean clipped truth-board
NLL by at least0.1nat against BOTH static controls, lose no more than2percentage
points of truth support, increase common-covered king-event Brier by no more
than0.002, and use no more than2x update time. Show sensitivity to clipping at
1e-9/1e-12/1e-15. These thresholds screen this development panel; they are not
population-strength guarantees. If it fails, preserve the predictive result
but do not promote the filter or tune it on these games.
