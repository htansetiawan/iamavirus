# 094 — Astra: v35 computes hidden-threat features that its fitted prior ignores

2026-10-25. Source-level finding from the exact v35 archive:
`src/movemodel.h` appends `MM_CHECK_UNSEEN` and `MM_THREAT_UNSEEN` after the
original feature set. `src/movemodel.c` computes both features, but the full
and cheap coefficient arrays end in `0.0000f, 0.0000f`. The previous archived
26-feature coefficients stop at `MM_XRAY_KING`; the hidden-threat features
were added after that fit and contribute exactly zero to the conditional
opponent prior in v35.

This is a concrete gap between feature plumbing and learning: arena analyses
show top players use unseen king threats substantially more than v35, but the
move model cannot learn that pattern from its current coefficients. It is not
proof that positive weights improve play. `MM_CHECK_UNSEEN` may be rare or
correlated with other tactics, and a prior that overweights it can distort
beliefs or discard the true board at the cap.

## Proposed data experiment

Use rules-validated public replays and the archived C `move_features()` as the
feature oracle. Refit the full conditional-logit prior with a game-disjoint
chronological split and report separate results for top opponents, unseen
check moves, unseen non-king threats, and ordinary moves. Compare the frozen
26-feature prior, the same prior plus the two refit coefficients, and a
regularized full refit. Evaluate held-out conditional NLL, calibration, and
the exact v35 sequential posterior (truth support/rank and king-risk choice),
then branch changed moves through the referee before considering a runtime
port. Keep top-level defaults and the submitted ZIP unchanged until this gate
passes.

The replay trace runner now also records the risk estimate of the move it
actually selected, distinct from the historical action's risk, to support the
next decision audit. No engine source, coefficient, or submission ZIP changed.
