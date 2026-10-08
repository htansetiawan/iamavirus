# Why a better belief update did not reliably choose safer moves

The completed 453-game comparison gives no promotion result. Grouping reduces
duplicate transition work, but its hand-prior decision changes include both
36 saves and 29 new fatalities. The next question is whether those losses come
from the posterior, the candidate list, or the final utility comparison.

For all 65 changed-fatal cases, `audit_choice_risks.py` runs both selected moves
through both frozen beliefs. The optional `ASTRA_PROBE_CANDIDATES` input to
`probe_belief.cc` copies positions; it does not affect filtering or its RNG.
It reproduces the engine's en-passant override and normalization over legal
supporting particles. All **130 selected risks**, rounded to the engine's
permille trace, agree with the original decisions; all truth labels agree too.
The underlying particle counts retain precision beyond that rounded trace.
Without requests, old and new probes produce the same 116 observation rows
on the parity fixture, excluding elapsed time.

For the grouped belief, compare the two original moves in each changed case:

| Belief's immediate king-risk assessment | 36 saved positions | 29 newly fatal positions |
| --- | ---: | ---: |
| Fatal move has exactly zero predicted risk | 1 | 6 |
| Fatal move has positive, lower risk than the safe comparator | 11 | 12 |
| Safe comparator has lower predicted risk | 24 | 11 |

This separates two problems. In 18 of the 29 new fatalities, the posterior
either misses the fatal move's danger completely or favors it over the known
safe comparator. In the other 11, the engine selects a move with greater
immediate model risk. That is not by itself an implementation error: a search
may trade immediate risk against estimated future losses, material or other
objectives. Nor is the safe comparator necessarily the best action.

The exact true board is present in only 3 of the 29 newly fatal grouped
populations, and only 6 of the 36 saved populations. Complete-board inclusion
is a strict diagnostic; an approximate board can still identify the relevant
attack. One newly fatal case rebuilds the belief at that observation. This
selected set cannot estimate natural-frequency calibration or overall truth
coverage.

## The shortlist is not missing the escape in three inspected cases

Matrix traces reproduce the same choices for `0urlpzmw` White ply 32,
`wqlwbuoy` Black ply 83, and `ah9jp69c` Black ply 87. In all three, the safe
comparator is already in the final shortlist. The row selector therefore
deserves a controlled experiment independently of neural proposal recall.

For `0urlpzmw`, grouping chooses `f4f5`, with immediate model risk about 0.44%,
over `f2g4`, with zero model risk. Across the eight printed payoff columns,
`f2g4` has the better arithmetic mean, but a worse minimum. For `wqlwbuoy`,
`g7f6` has about 3.61% immediate risk and is chosen over zero-risk `g7h6`;
the latter is assigned future fatal outcomes in several hypothetical worlds.
Again its column mean is better while its minimum is worse. These observations
use rounded debug payoffs and do not prove what a different full engine would
choose.

The current solver treats the hidden-board columns as an adversarial player.
That is a robustness choice, not integration over posterior chance. Also,
`BeliefState::Sample` includes a hand-picked representative before its strided
samples. Simply averaging those columns would not be an unbiased posterior
expectation. `FOW_MATRIX_GAME=0` skips matrix search and returns the first ranked
move; it is not an expected-payoff control.

The next structural comparison should retain the existing full-population
safety costs, use the same posterior-distributed columns for both controls,
and compare adversarial versus posterior-weighted aggregation. Test sampling
separately against the existing representative-based control. It must retain
search/node budgets and compare complete games after replay diagnostics.
This would change root uncertainty handling; it would not solve deeper
information-set strategy fusion or implement CFR.

## Reproduction and limits

- `choice-risk-audit.json` pins all probe runs, input hashes and exact counts.
- `choice-probe-correctness.json` records the unchanged-observation check.
- Raw traces and matrix logs are under
  `/media/henrytan/seagate/iamavirus/astra/belief/grouped-choice-risk-65-20261008/`.
- `choice-matrix-three.json` preserves the three-case manifest and all six
  terminal matrices, verifying the original log hashes before extraction.
- This is an explanation of selected decision differences, not a fresh
  validation set, probability calibration result, game win rate or Elo claim.

Neither grouped prediction, the learned prior, a new risk tolerance nor a new
root selector is promoted by this analysis.
