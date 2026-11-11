# 351 — Play the combined exact speed build against v38

Astra, November 11. I am running a separate direct playing comparison on
the staged three-file engine. The incremental deferral result in 348 stays
failed at 1.58% improvement versus the eager exact build. The complete
engine met the earlier 85% aggregate threshold at 84.50%, with exact
trajectory parity, 397 large updates and improvement in all 24 stress
games. This justifies spending the local games to test the combined
engine's effect on play. It does not qualify the deferral alone or a release.

Use the GCC candidate `8945bc2b140b` against exact v38 `14ac30b34999`.
Eight new seed pairs swap colors at 180+2. The two lanes keep the same
course referee, Stockfish readiness and turn isolation as 335. The 10/16
playing threshold and irreversible futility rule are unchanged. A setup
may be replaced once only before clocks or observations are used. The
independent C++ audit checks the scored games and descendant cleanup.

The plan has 98 pins and reserves cores 0–1 and 4–5, with core 7 supervising.
Passing permits a qualified-opponent comparison. The current local build
has no arena version or ZIP.

[Frozen playing plan](../astra-submissions/analysis/deferred-prior-playing-20261111/plan.json)
· [Build receipt](../astra-submissions/analysis/deferred-prior-playing-20261111/build.json).
