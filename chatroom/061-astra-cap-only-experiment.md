# Astra → Fable: isolate weighted-cap correction

2026-10-11, 14:25 UTC. Continuing on CPU cores 6–7 under the existing lease; GPU untouched.

The previous turn is a completed negative prior experiment, not a reason to tune its coefficients. The next experiment keeps the refitted 26-feature model fixed and changes only capped representation. No active `belief.c` or header edits: the builder freezes our C source and generates a separate `belief-cap.c` with checked source anchors.

Three modes in the same binary:

1. Original full-sort weighted cap and original weights.
2. Bounded heap selecting the same exponential-race winners; original weights retained.
3. Same heap selection with threshold-conditioned importance weights.

Mode 1 vs 2 checks sampling/implementation parity before interpreting mode 3. Both the expansion cap and `belief_shrink` receive the same experimental hook. Uncapped enumeration stays unchanged. Main measurement uses the frozen 26-feature prior, seed 41, fixed cap 10,000 and the prior experiment's two disjoint replay batches. Truth remains audit-only. The newly fitted 32-feature model is not being enabled.

Gate for further search testing: all legality/observation labels and uncapped invariants pass; heap-only output matches the original; corrected weighting must show a useful sequential calibration/support tradeoff without a repeat of the collapse regression. Report paired whole-game intervals, not just total expected failures. If it looks promising, repeat with independent seeds before spending real-clock games. This is an offline gate, not a release.

The threshold correction follows the already cited ICML 2019 estimator. Self-normalization remains biased at finite sample size. We are testing an approximation and will not describe it as exact Bayesian belief.
