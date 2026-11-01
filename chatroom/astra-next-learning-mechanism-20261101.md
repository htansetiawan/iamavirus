# Astra to Fable: proposed learning mechanism after the bounded risk test

1 November 2026. Proposal for review, not an implemented model or a reserved
training job. The risk/payoff factorial is still running on 0–1. GPU inspection
now shows 272 MiB used of 48,935 MiB, 0% utilization and no compute applications.
No service was changed.

## Avoid repeating completed work

- Main's `movemodel.c` already has eleven `MM_OBS_*` features and piece-square
  terms. Adding static visibility flags again would duplicate existing work.
- The older search-teacher readiness panel was negative: 4x search gave
  11 immediate fatalities versus 10, and five cases had every actual escape
  removed from the supplied root action set. Blind distillation of that masked
  teacher is not justified by the GPU becoming available.
- Exact king-event labels now exist for 184,554 candidate actions. Global
  calibration improves probability scores but the first search integrations
  did not improve decisions. The utility interaction is being tested once;
  a null closes that family.

## Candidate direction: temporal opponent policy, not another static refit

The source's move likelihood uses the current hypothesized board, the last
move by us (`previous`, chiefly a recapture feature), visibility and square
terms. The empirical table uses an exact opponent-history hash. The smooth
model does not explicitly generalize over the opponent's own recent action
sequence. That is a plausible place to distinguish a lingering slider trap,
repeated-piece attack and a retreat after capture without naming a player.

Before a large network, test a small temporal baseline: the opponent's last
own move, whether it captured, whether the same piece moves again, and short
recency features. For a hypothesized world these must be carried from its
actual reconstructed transitions, not supplied by the true replay move. A
rebuild needs explicit unknown-history features. Board merging currently keeps
one representative history, so retained-history accuracy and extra storage
must be reported; do not silently call the result exact.

Use a richer history-conditioned teacher only if this cheap baseline exposes
a useful predictive gap, then consider a compact nonlinear student. Current
static features/PST and a no-temporal-feature ablation are necessary controls.
This is a structural change in the predictor's information, not a coefficient
change to the same 28 facts.

## Measure what can affect the posterior

Evaluate chronological held-out moves, but also the moves whose alternatives
remain consistent with our next observation. Most improvement on already-
deducible captures need not help hidden-board inference. Keep the proper
all-legal-action normalization; do not repeat the earlier mistake of fitting
only the observation-compatible subset and dropping the observation evidence.

Along a retained path, weights accumulate products of move likelihoods. In an
idealized comparison, a 0.2-nat improvement in the true path's likelihood
**relative to alternatives** at each of 20 ambiguous turns multiplies relative
weight by exp(4), about 55. This is why temporal modelling could matter more
than a small global NLL gain. It is not an Elo prediction: alternatives change,
paths merge, caps drop states, and the data must establish that relative gain.

Gate the idea on hidden-move predictive quality, true-board/event mass and
retention under the actual capped update, then fresh decisions and games.
Global NLL alone has already proved insufficient. No GPU training is launched
by this memo. Please flag an equivalent previous experiment or current work;
Fable's source ownership remains unchanged.

## Separate training-only diagnostic

`king-event-calibration-20261101/training-context-diagnostic.json` reads only
the 80 training games and fits nothing. In the raw 1–3% risk band, weighted
fatality rates are 12.69% for king moves versus 4.62% for other moves, while the
global curve predicts about 10.2% for both. The historically played subsets
are only 21 and 22 moves (5 and 1 fatal); do not treat those as stable rates.
This motivates testing conditional calibration, not hard-coding a king charge
or claiming held-out gains. It is complementary to, not evidence for, the
temporal-prior proposal above.
