# Immediate king-loss calibration

1 November 2026. Astra diagnostic and supervised calibration experiment, based
on immutable v35. This is not reinforcement learning, a new arena submission,
or an automatic update to the deployed model.

The root-loss control-variate screen was level (note 194). It reduced sampled
risk on some moves that really were fatal. Before changing another search
weight, measure whether the larger belief scan estimates the exact terminal
event correctly on representative complete games.

## Data and event

140 v35 games, selected by a deterministic game-ID hash without using outcomes:
80 from 25–28 October for training, 20 from 29 October for validation, 40 from
30–31 October for testing. Opponents are Instructors, duck, HYPOTHERMIA and six
other leading teams; this is representative within those dates/opponents, not
the whole arena. Full-move-sequence duplicates are grouped before splitting.
The frozen plan records eligibility, excluded undated records, replay hashes
and split boundaries. A separate sidecar records actual opponent versions.

At every recorded own decision, collect each move permitted by v35's view
move generator, before selecting the recorded action. The event is immediate
own-king loss after that candidate move. The collector matches v35's root
legality and king-capture precedence; labels are independently joined from
the true replay state using the course-compatible rules after the engine exits.

The copied engine sees only its own observations, clocks and forced own moves.
It never receives a true board, the opponent's observation or an opponent move.
Forced own moves advance the historical belief; they are not predictions.
Missing played moves (for example a view move-set omission) are counted, not
silently replaced or supplied as extra candidate moves.

The scan uses the deployed 200,000-board belief cap and the guard's up-to-20,000
strided scan. It records sharp `exp(logw)`, flattened `exp(logw/temp)` and uniform
risks, invalid-action mass, world counts and cap status. Flattening is the
guard's transformation, not a claim to recover the exact untempered Bayesian
posterior after merges. Zero-support events are counted explicitly.

Move legality uses a direct 15-bit move-to-action lookup: each world's legal
move list is built once and mapped once, then all candidate moves are tested.
This avoids comparing every candidate with every generated move.

## Fit and decision rule

Train a monotone two-parameter logistic calibration of sharp risk:

    q = sigmoid(intercept + slope * logit(p)), slope >= 0.

Fit only on training games, with each decision contributing total weight one
across its candidate moves. A small penalty toward the identity map stabilizes
the fit. Select raw sharp, raw flattened, or calibrated sharp using validation
log loss. Evaluate the selected method once on the untouched test games.

Report log loss, Brier score, event counts and calibration bins for all candidate
moves and separately for moves actually played. Confidence intervals resample
whole games. The preregistered gate requires a non-identity validation winner,
held-out log-loss improvement with a game-bootstrap interval below zero, lower
held-out Brier, and no worsening of played-move log loss. Passing earns an
engine experiment only. Neither a better proper score nor calibration alone
establishes a playing-strength gain.

## Checks and limits

Native unit tests cover both colours, probability weightings, safe/fatal moves,
illegal-world fallback, empty belief and opposing-king capture precedence.
Python tests cover permitted replay input, recovery of a known calibration map,
and game-level bootstrap identity. The three-game pilot independently matched
the course referee on 330 frames and 4,813 candidate labels, with all 163 played
moves covered and no belief rebuilds in that pilot.

This is offline forced replay, not reconstruction of the arena process's exact
hidden memory. Wall-clock thinning still depends on measured update cost; the
collector consumes some clock while omitting search. Full collection logs
thinning and rebuilding. Above 20,000 boards the scan is approximate. Candidate
moves within a game are correlated. No static non-king attack multiplier is
borrowed from the earlier hazard calibration.

A calibrated king-event probability does not by itself define a coherent new
distribution over full boards, nor the value of surviving continuations. Any
subsequent engine integration must specify those semantics and avoid charging
the sampled terminal loss twice. Queen/material risk is outside this event.

## Reproduction

From the repository root, using an unused output directory for a fresh study:

```sh
taskset -c 0,1 python3 astra-submissions/experiments/king-event-calibration-20261101/build_collector.py
taskset -c 0,1 .venv/bin/python astra-submissions/experiments/king-event-calibration-20261101/collect.py freeze --out OUT
taskset -c 0,1 .venv/bin/python astra-submissions/experiments/king-event-calibration-20261101/collect.py collect --out OUT --limit 3
taskset -c 0,1 .venv/bin/python astra-submissions/experiments/king-event-calibration-20261101/collect.py collect --out OUT
taskset -c 0,1 .venv/bin/python astra-submissions/experiments/king-event-calibration-20261101/fit.py OUT
```

`audit_pilot.py` checks the current frozen study against the locally installed
course referee. It records the referee source hash. Collection and test reports
refuse an implicit overwrite/restart. The pilot is reused only when its game
and build provenance match. Data, receipts and results belong in
`astra-submissions/analysis/king-event-calibration-20261101/`.
