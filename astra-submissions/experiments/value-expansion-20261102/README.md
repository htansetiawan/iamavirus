# 234: conditional-value-guided tree expansion

Hypothesis: spending search on action value and uncertainty can discover useful
continuations faster than the current strategy-probability/visit heuristic.
The prior-fit family and representation audit did not earn further fitting.
This changes the allocation of search work while retaining v37's belief, guards,
solver, leaf evaluator, budget and final selector.

Source: [Obscuro Appendix C.4](https://arxiv.org/html/2506.01242v2#A3.SS4).
Its exploring player mixes uniform sampling over current support with the
maximizer of conditional action value plus a variance-scaled visit bonus.
The non-exploring player follows its current strategy. Here C=1, with variance
initialized by observations -1 and +1. The text says **variance**, not standard
deviation; the population-variance convention is explicit in our implementation.
This is one component of Obscuro, not a claim to reproduce the full agent or
inherit an asymptotic guarantee in our bounded, approximate tree.

For player i, infoset I, current profile x and action a:

```
mass(I) = sum_{h in I} chance(h) * reach_other(h)
Q(I,a) = sum_{h in I} chance(h) * reach_other(h) * value_i(h,a; x) / mass(I)
score(I,a) = Q(I,a) + variance(I,a) * sqrt(N(I)) / (1 + N(I,a))
```

An exact fixed-profile pass computes all Q values in O(tree edges + action
slots), without a search per candidate or clairvoyant choices within an infoset.
It runs when the existing cached exploration strategy refreshes, including
the asynchronous path. Values and strategy therefore come from the same
snapshot, then age together until refresh. Growth can make them stale in the
interim; newly added or zero-counterfactual-reach infosets retain the original
selection rule until values are available. A necessary own-reach consistency
check rejects invalid merges; this check alone is not a perfect-recall proof.

Moments update for all actions after each visit to a valued infoset, for either
player, and use the prior plus previous visits when choosing. Values retain
the existing doubled root-loss convention; we do not change utilities to make
the variance prior appear exact. New arrays are O(slots + infosets), reused
across refreshes. The extra whole-tree work may outweigh better ordering;
equal-clock measurements must report this cost.

`MIST_EXPANSION_Q=0` is the default and does not compute values or moments.
The production candidate modifies only `gtcfr.c` and adds `expansion_values.*`;
the CFR solver source is unchanged. Base extraction comes from the immutable
v37 archive. Its rebuilt binary matches our independently rebuilt v37 bytes.
No changes to Fable's source, deployed model, root masks or coefficients.

## Correctness and experiment sequence

1. Independent two-pass conditional-value calculations cover both players,
   hidden histories sharing an infoset, zero-probability actions, zero other
   reach, changing trees, invalid recall merges and 257 actions. Reading values
   must preserve solver state byte-for-byte. Actual `pick_once` fixtures must
   change only the intended exploration branch, preserving support sampling,
   the non-explorer and missing-value fallback. Sanitizers cover both modules.
2. Freeze and publish one replay comparison on the existing 51 development
   decisions from 25 games against Instructors, duck and HYPOTHERMIA. One process
   per case reconstructs a single belief/mask, then searches off/on for 2.5 s
   each with identical seeds and samples. Order alternates by case. Offline
   diagnostic export is separate from the playing binary. No true board or
   hidden opponent action enters the engine; truth labels join after exit.
   Cases with a forced sole front-end action are reported as unexercised.
3. Stop on any technical/integrity failure, illegal choice, inconsistent
   information-set reach, or fewer than 20 exercised pairs. The diagnostic
   permits at most one additional immediate king loss and two additional
   bounded two-point material events versus the paired control; these are
   fail-fast tolerances on reused data, not statistical improvement claims.
   The independent referee must verify labels and original handles must end.
   No coefficient sweep or retry of a failed call.
4. Only after that screen, 8 colour-swapped full-game pairs versus exact v37 at
   180+2, fixed bytes and seeds, at most two exclusive core-pair lanes and four
   hours. At least 10/16 points, no technical faults or forfeits, is required
   to justify a separate opponent gate (including Misty), not promotion or an
   Elo estimate. Do not demand better node throughput if game quality improves.

The paired replay controls search inputs, not Stockfish cache warmth; order
rotation mitigates that effect without pretending it vanishes. Truth labels
are bounded diagnostics, not replaying recorded replies after divergent moves.
All cohorts are reused development. No new release, GPU job or Fable agreement
is implied. Initial archive-directory and missing-stdio build failures are
preserved; neither launched a game or a policy comparison.
