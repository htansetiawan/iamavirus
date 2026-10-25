# Astra 133 — EP gate first game was a null exposure

The first v35 vs EP-history full-clock game completed with candidate as White.
Candidate lost by king capture in 119 plies (547.26 seconds), with no bot
failure. The replay contained five double-pawn pushes, but none had an adjacent
pawn able to make a legal en-passant reply. Thus this game did not exercise the
EP action-generation treatment. Its outcome is a protocol/game observation,
not evidence for or against the change.

Track treatment-eligible EP opportunities in the remaining games. If the full
game gate rarely exposes the fix, retain it as a broad correctness repair and
use replay-position decision comparisons to measure whether it changes action
selection; do not over-interpret the paired score as a feature-specific effect.
