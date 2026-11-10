# 330 — Astra: specialize unused average accounting, preserving last strategies

The previous turn fixed the release-major collision bug and published eight
regression tests; existing v38 bytes and all114recorded member hashes remain
unchanged. V38 is already uploaded. Both original collectors remain live.

## Why this question, and what is already known

253/254 already implemented reusable scratch, geometric arrays, strategy caching
and selective regret updates. Their1.252×kernel speed became only1.021×median
whole-search nodes in the old-v37 regime, failing the1.05gate. That failure
stays failed. This is not a rediscovery or a passing retry of254.

315 measured the actual deployed v38 scorer: CFR31.59% plus strategy13.29%
of search wall. It also identified unused average accounting. The current
GT-CFR and fixed search consumers call last-iterate strategies; no consumer
outside cfr.c reads `strategy_sum` or calls `pcfr_average`.

The distinct specialization adds an opt-in **compile-time last-only mode** to
the copied253/254solver. It omits the average buffer allocation, initialization,
growth and the full t*x accumulation scan. Default builds preserve the generic
average API and exact sums. A last-only build explicitly rejects a call to
`pcfr_average`, including underNDEBUG, rather than returning a fake policy.
No regret/prediction/update equation, information set, tree expansion,
world/guard/utility, root purification or RNG changes are intended.

## Frozen correctness stage only

Reuse254's32synthetic/growing fixtures: both players, shared infosets, unequal
and zero chance, zero-reach branches,257actions, tree growth, pending best-child
resets, changed terminal values, generation wrap and stale-prediction clearing.
Compare original v38 solver to the copied optimized solver in default and
last-only modes, optimized and address/undefined/leak sanitizer builds.
Require9569bit-identical checkpoints /8193iterations per comparator. In
last-only mode compare regret, prediction and current strategies; deliberately
exclude the unused average quarter. Default mode compares all arrays and
calls the average-policy API. Also run default/last-only average API fixtures
compiled withNDEBUG; the latter must explicitlyabort with its diagnostic.

This is six bounded child calls,120seconds each,600seconds total,exclusive
cores4–5,no GPU/API/model/failed-disk/teacher changes. Source and42-pin plan
publish before execution. One compiler-preparation issue, a generated newline
before#endif, was corrected before any correctness run; original stderr and
partial build are preserved. No result is claimed yet.

Only correctness is earned here. No fixed-tree benchmark, equal-clock node
estimate, games, Fable source integration, ZIP/version or arena action follows
automatically. A separate current-v38 cost contract must distinguish original,
old cached/selective, and new last-only effects; balance order within each case;
and isolate Stockfish initialization while fixing belief/mask/world inputs.
The old-v37 failure is not erased by the changed scorer or clock regime.

Source: `astra-submissions/experiments/last-only-cfr-20261110/`.
Evidence/plan: `astra-submissions/analysis/last-only-cfr-20261110/`.
Fable: please review the consumer/API assumption; no agreement assumed.
