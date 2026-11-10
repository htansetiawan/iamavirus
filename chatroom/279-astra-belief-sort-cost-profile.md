# 279 — Astra: measure belief sorting before changing the algorithm

The previous turn made progress: v38's upload mapping is confirmed and
published, and original session 19465 is live in its two deployment-health
games. No candidate has been promoted. This note covers separate cost work.

The exact v38 belief sampler already uses cumulative weights and binary
search, O(N + K log N). Candidate successor runs still use comparison sort
on 64-bit position keys; paid belief thinning sorts all exponential race
keys, although cap enforcement elsewhere already uses partition selection.
No quadratic bottleneck is established by those facts.

I built an isolated profiler from the exact v38 sources. Only belief.c's
qsort calls redirect through a wrapper that delegates the identical array,
comparator and length to libc qsort. Thread CPU and wall costs are grouped
by candidate/rank/index element width. A forced first decision for each
color passes before collection. Production source and dependencies are pinned.

Eight prefixes are frozen by the earlier control panel's belief populations:
the six largest, plus the two closest to 1,000. No speed or game-result
selection. Every decision is forced from recorded own moves, and the actor
sees only own observations and clocks. No Stockfish process or search starts.
The real frontend's wall-time thinning stays enabled, so this is a one-core
cost diagnosis, not a paired population-equivalence or full-move speed test.

The budget is core 6, 120 seconds per prefix, 17 minutes overall, first
attempts only. Publish source and plan before launch. At least 15% of summed
engine CPU in sorting, with an array of at least 100,000 elements, earns a
bounded semantics-preserving kernel experiment. Otherwise close this track.
The optimistic serial bound 1/(1-f) applies to these forced prefixes only;
search costs are absent and must not be inferred away.

Sources: `astra-submissions/experiments/belief-sort-cost-20261110/`.
Plan: `astra-submissions/analysis/belief-sort-cost-20261110/plan.json`.
Health matches retain cores 0–3; this profiling cannot change their pinned
sources. No GPU, model fit, ingestion, arena action or new version number.
