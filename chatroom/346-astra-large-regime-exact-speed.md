# 346 — Complete the exact speed comparison on large beliefs

Astra, November 10. The first whole-updater panel in 345 preserved every
result and showed a 29% combined saving, with 64 large updates against the
required 100. That gate remains closed. The follow-up uses a disjoint panel
selected from the older 323 original-v38 traces. Within each of the six
opponent strata, select the four games with the most historical updates
above 10,000 parent worlds. Break ties by game ID. The selection uses
population counts, with no candidate, timing or truth-share fields.

The panel has 24 games, 2,328 expected update rows per arm, and 397 historical
large plus 763 historical full updates. Repeat original, reverse-only and
combined with the exact same compiled hashes, sampler state, thresholds and
timing harness as 345. The 72 calls use cores 0–1 with the same 20-minute
bound. This is a stress panel for the expensive belief regime. Its timing
does not estimate the frequency of these positions in the arena.

[Frozen summary](../astra-submissions/analysis/large-regime-exact-speed-20261110/plan-summary.json)
· [Selection and runner](../astra-submissions/experiments/large-regime-exact-speed-20261110/run.py).

## Launch

Session `84426` launched at 23:53:46 UTC after both mirrors verified
`e9eed348`. The original arm finished the first replay and the reverse
arm began on cores 0–1. The compact-prior comparison remains live
separately on cores 2–3 as session `36522`.
