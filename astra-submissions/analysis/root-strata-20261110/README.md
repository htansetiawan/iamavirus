# Tactical strata: exact immediate risks, unchanged decision

The native prototype and its first frozen diagnostic are complete. All
16 searches still choose g7g8, which is fatal on the recorded true board.
**No candidate, full-game experiment or promotion follows from this result.**

| Measurement | Result |
|---|---|
| Frozen population | 2,344 worlds, 15 legal actions, six terminal-risk signatures |
| Ordinary sampling, maximum action-risk error across four seeds | 0.13349 (13.35 percentage points) |
| Stratified sampling, maximum action-risk error | 1.56e-15 |
| Existing guard | Only g7g8 evaluated |
| Payoff-bound pruning | g7f6, g7h6 and g7g8 evaluated |
| Selected action | g7g8 in all four arms and all four seeds |
| Prototype census cost | 3.93 ms median in preflight, only this small population |
| Runtime | 43.37 s for all four processes /16 searches |

On stratified/bounded runs, f6's Q is about -1.107 to -1.115 and h6's
about -1.099 to -1.100. The capture is about -0.964 to -0.969. The current
belief assigns the escapes 11.65% and 10.00% immediate death probability,
versus 0.01390% for the capture. Allowing the escapes and preserving all
those probabilities does not make search prefer them. This refutes the
narrow explanation that the guard or missed sampled risk alone caused this
choice. It does not prove the posterior is wrong on the population, that
more search is useless, or that stratification has no value elsewhere.
The selected loss was already inspected; it is a diagnostic, not a test set.

## What was implemented

`strata.c` computes the full vector of root loss and direct king-capture
outcomes, using the solver's terminal precedence. Positive-mass groups each
get at least one draw; remaining draws follow mass, with largest-remainder
allocation. Each draw has chance P_g/K_g and duplicate **indices** add their
chance weights. Positions with different opponent histories stay distinct.
GT-CFR's one patched call site consumes these indices/chances; its tree,
information-set keys, regret algorithm and value function are unchanged.

The companion bound is p-kappa*r +/- (1-r-p), with immediate king-win mass
p, loss mass r, kappa2 and continuation bounds [-1,1]. It prunes only strict
interval dominance. This implements a queenless first scope. Own queens,
inconsistent information states, differing legal sets (including EP
ambiguity), excessive groups and unsupported numerical inputs retain the
original pruning/sampler. The frozen diagnostic supplies the original
recorded guard mask; this is not yet a protocol frontend or playing binary.

Census costs O(N*A) move/attack checks plus expected O(N) bounded hash grouping.
Grouping does not merge deeper information sets. Draw allocation costs
O(G log G), and within-group draws use binary search. The 3.93 ms number
cannot be extrapolated to 200,000-world beliefs without measurement. Census
cost was outside the equal **search-time** budgets here and must be charged
in any playing experiment. No generic speedup or Elo gain is claimed.

## Validation and provenance

- Four frozen seeds 2851100–2851103, four arms, 2.5 s/search, rotated order,
  fresh same scorer workers. Original35745 exits0; no retries or new games.
- Source/plan commit b75c7338cf775e7b6ef0a5291d47c5c9abc783ef published to both
  mirrors before collection. Thirty-six dependencies remain unchanged.
- Preflight verifies 32 other seeds, group mass, original risks and masks,
  overflow fallback, own-queen fallback, EP ambiguity and king-capture
  precedence. Address/undefined sanitizers pass. Known compiler warnings
  in inherited CFR and POSIX macro definitions are retained in preflight.
- Independent audit verifies all35,160 action/world pairs with course rules,
  exact chance risks, sampled boards, root masks, histories/input fields,
  target normalization and all16 outputs. Truth labels join after exit.
- Two setup failures remain recorded: Conda lacked python-chess; sandbox
  ptrace blocked LeakSanitizer. Existing .venv plus host-side sanitizer
  verification repaired the environment before any timed search.
- Host cleanup verifies no remaining actor/scorer. Cores0–1 released. No
  GPU, model fit, ZIP, version allocation or arena action.

See [audit.json](audit.json), [input-audit.json](input-audit.json),
[preflight.json](preflight.json), [plan.json](plan.json) and per-seed outputs.

The next prioritization should incorporate this negative result and the
closed posterior-learning screens231/232, feature audit233 and dual-measure
screen252. Repeating the same fits or changing a risk constant is not an
automatic next step. The remaining question is the provenance and quality
of the retained probability mass, including cap selection, rather than a
claim that these two safe true-board moves must be selected by this belief.
