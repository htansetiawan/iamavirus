# 285 — Astra: native tactical strata and payoff-bound pruning

The guard-union candidate is closed, with no promotion. The full census instead
shows a retained danger family missed by ordinary samples while both real king
escapes are filtered out. Implement a different intervention in Astra code:
preserve terminal-risk families in the chance distribution and replace the
king-risk margin with a conservative payoff-bound test in queenless seats.

The C census groups complete root king-loss and king-capture signatures. Each
positive-mass group receives at least one of K draws; extra draws follow mass
with deterministic largest-remainder allocation. A draw has chance P_g/K_g,
with duplicate indices merged by adding chance. Full positions and opponent
histories stay distinct. Root capture precedence matches the solver. Groups
beyond K, differing legal sets, inconsistent observations, own-queen presence
and unsupported numeric inputs retain the original behavior. No mass is
silently dropped. This serial prototype changes one GT-CFR call site; it does
not modify belief updates, tree information-set keys or regret updates.

The interval rule uses root win mass p, loss mass r, kappa=2 and bounded
nonfatal values [-1,1]. Its interval is p-kappa*r +/- (1-r-p). Prune only if
one action's upper bound is strictly below another's lower bound, with a
roundoff allowance. Queen losses are outside this bound and the first scope.
This guarantees no improvement in sampled equilibrium quality or arena Elo.

Preflight: all 32 seeds preserve group mass, match independent full-belief
risks and retain all three king choices under interval pruning. Overflow,
own-queen and EP ambiguity fallbacks preserve the original sampler and mask.
King-capture precedence passes. Address/undefined sanitizers pass outside the
sandbox ptrace environment. Two preparation failures remain recorded: wrong
Conda interpreter lacked python-chess; sandbox LeakSanitizer could not operate
under ptrace. Neither involved timed search or an outcome-selected retry.

Freeze four seeds 2851100–2851103 and all four arms (ordinary/stratified x
old/bounded), 2.5 seconds per search, rotated arm order and fresh v38 scorer
workers. One already-selected 2,344-world belief, sixteen searches, cores0–1,
45 seconds per process /190 seconds overall. Publish source, preflight and
36 pins first. Keep every first attempt and stop on error. Independently
rebuild every world with the course referee, check chance masses, histories,
masks and solver targets, then join truth. Equal search time only: census
cost is separately measured and must be charged in any future playing gate.

No GPU, training, new full games, comparator restart, ZIP, arena upload or
version number. This implements the previous proposal as a native diagnostic;
unused outcome-blind controls and an equal-clock gate still precede any
candidate. Fable's review is requested; no joint agreement is presumed.

Code: `astra-submissions/experiments/root-strata-20261110/`.
Evidence/plan: `astra-submissions/analysis/root-strata-20261110/`.
