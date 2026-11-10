# Native belief sort profile: close this kernel track

Eight forced historical prefixes completed in the original session 61155,
exit 0. The independent course audit validates **502 source frames**, every
actor input and forced action, all source/log hashes and aggregate arithmetic.
Only belief.c's qsort symbol redirects; its wrapper delegates to the same
libc implementation and comparator. No playing source body changed.

| Cost | CPU seconds | Share of engine CPU |
|---|---:|---:|
| Successor-board sorting | 3.2102 | 12.086% |
| Full rank sorting in paid thinning | 0.0841 | 0.317% |
| Kept-index sorting | 0.1080 | 0.406% |
| All sorting | 3.4023 | **12.809%** |
| Engine total | 26.5608 | 100% |

The largest successor array had 1,810,777 entries; the largest full rank
array had 186,355. The predeclared trigger required a large array **and**
at least 15% aggregate CPU in sorting. It fails. Do not reopen this as a
heap/radix rewrite on the strength track.

Eliminating every measured sort for free gives a 1.147× serial bound on
**these forced prefixes**. This excludes search and Stockfish, so it is not
a whole-decision bound or an Elo prediction. It also leaves observation
generation, move modelling and reconstruction untouched. The rank sort
alone, the proposed heap target, accounts for only 0.3% here.

Cases are six largest earlier control populations plus two closest to
1,000, chosen before these timings. The actor sees own observations,
clocks and forced own moves, including the final decision. No search or
evaluator process runs. Native clock-paid thinning remains enabled and
depends on measured wall time; one core runs two belief threads. This is
neither a population-equivalence test nor an arena speed test.

The profiler and plan were pushed on both mirrors at c0c0c653 before
collection. Core 6 is released. No GPU, model, release or arena changes.
See [audit.json](audit.json), [plan.json](plan.json) and the individual logs.
