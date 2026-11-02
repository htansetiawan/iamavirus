# 254 — Exact selective PCFR+ updates

Build on experiment 253's exact workspace/cache change. Its eight actual tree
snapshots show a median 37% of action slots belong to visited infosets or have
a previous instantaneous regret to clear. The proposed update records those
sets during the existing traversal, without sampling or changing reach.

For an unvisited infoset, instantaneous counterfactual regret is zero. If its
previous prediction is already zero, its clipped regret and next strategy do
not change. If the previous prediction is nonzero, clear it and recompute the
strategy. Visited sets receive exactly the existing accumulation, clipping
and prediction update. Clear instantaneous scratch once on first visit, not
once per history in a shared infoset.

The average-strategy array still receives **every** original t*x addition in
every infoset, in the same floating-point order for each slot. This deliberately
retains that full scan; lazy multiplication of a sum of t values would not
preserve floating-point bits. The cache/worklists are rebuilt after growth or
external invalidation; a generation-counter wrap clears all marks. Best-response
diagnostics keep the original dense traversal path. This is an exact execution
optimization for the audited v37 callers, not a claim to implement Lazy-CFR.

Require bit-identical regrets, predictions, weighted averages and policies
against original v37 on the 253 synthetic/growing suite, plus explicit epoch
wraps and evidence that stale predictions were actually cleared. An injected
missing-clear defect must fail the same comparison. Native and host sanitizers
must pass before timing. These tests cover correctness, not strength.

Reuse the eight immutable real trees saved by 253, with their recorded hashes.
No new search/Stockfish capture is required. Six pairs of 200 iterations: discard
the first warmup pair, alternate timing order, compare all arrays before/after
each pair. Keep every first attempt. A 1.20x geometric-mean speedup over original
v37 and zero mismatches earns a separate equal-clock search comparison. Do not
reinterpret the older 253 measurements as a paired sparse-only effect.

Limit 120 seconds per tree, 20 minutes total, reserved cores 0–1. No GPU, model,
guard, utility, world-selection, expansion-policy or root-selector change.
No new release until separate decision and game checks justify it. Source stays
under Astra; other clients mutating solver arrays need a separate API audit.
