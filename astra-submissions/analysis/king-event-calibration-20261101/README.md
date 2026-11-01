# King-loss probabilities: a held-out gain, not yet a stronger bot

1 November 2026. **The fitted risk curve passes the preregistered probability
gate and earns an engine experiment. It is not deployed and has no playing-
strength result.** The data and a compact C inference primitive are ready.

## What was collected

140 complete v35 games against Instructors, duck, HYPOTHERMIA and six other
leading teams. Outcome-blind deterministic sampling, chronological game
splits: 80 training (25–28 October), 20 validation (29 October), 40 test
(30–31 October). Full-sequence duplicates were checked before splitting;
none occurred in the eligible set. Played versions are in `played-versions.json`.

The frozen v35 collector reconstructed 6,164 own decisions and measured
**184,554 candidate moves**. It received only own observations, clocks and
forced own moves. It recorded root immediate-king-loss probability under the
sharp, flattened and uniform belief weights. True labels were joined offline.
Collection took about 540 seconds summed over games on cores 0–1, with no GPU.

All candidate moves were legal on the true board. No true loss label had
exactly zero sharp probability. Four belief rebuilds and 32 clock-based
thinnings occurred; these estimates come from forced replay, not the arena
process's exact hidden memory. One historical move was absent from the view
candidate set: `rq0qgtlt:26`, en passant `e5f6` after `f7f5`. It is explicitly
excluded from played-move scoring, not inserted using knowledge of the answer.
The training set consequently contains 3,480 played choices from 3,481 decisions.

The three-game pilot independently matched the course referee on all 330 frames
and 4,813 candidate labels. Native event tests and three pipeline tests pass.

## Model and held-out result

Fit two coefficients on training games only, with equal weight per decision
distributed over its candidate moves:

    q(p) = sigmoid(-0.0136740746741455 + 0.5425673322952794 * logit(p))

The input is clipped to [1e-6, 1-1e-6], exactly as in the exported C primitive.
Raw sharp, raw flattened and fitted sharp were compared on validation log
loss. The fitted curve won. The untouched test set was then evaluated once.

| Test metric | Raw sharp | Raw flattened | Fitted curve |
|---|---:|---:|---:|
| All-candidate log loss, decision-weighted | 0.07212 | 0.06554 | **0.05887** |
| All-candidate Brier | 0.02079 | 0.01999 | **0.01889** |
| Played-move log loss | 0.03789 | 0.03299 | **0.02790** |
| Played-move Brier | 0.00952 | 0.00900 | **0.00841** |

Lower is better. Test: 40 games, 1,866 decisions, 52,796 candidate moves and
24 fatal played choices. The average sharp risk on played moves is 0.459%,
against an observed 1.286%; the fitted curve predicts 0.909%.

Resampling whole test games gives 95% intervals for fitted-minus-raw log loss
of [-0.02056, -0.00674] on all candidates and [-0.01732, -0.00419] on played
moves. Brier intervals also exclude zero. This passed the frozen gate; it is
not a guarantee outside these dates, opponents or reconstructed beliefs.

The learned correction is substantial in the low-risk range: a raw 1% becomes
7.54%; 2% becomes 10.67%; 10% becomes 23.04%. These are model outputs, not
assertions that every individual position has that risk. The mapping remains
monotone, so it **cannot repair a wrong ordering between two moves**.

## Runtime and reproducibility

`../../experiments/king-event-calibration-20261101/calibration.h` implements
the fitted curve using two double coefficients (16 bytes of parameters) and
scalar log/exp calls. C/Python outputs match on 6,000 endpoint/dense/log-spaced
inputs, max absolute difference 0 in the tested build. The primitive is not
wired into the policy. There is no new submission ZIP.

`collected-games.tar.gz` (2,309,379 bytes) preserves all probability rows,
labels, per-game provenance and raw collector logs. SHA-256 and all 420 member
hashes are in `dataset-archive.json`. Extract here to restore `games/` for
reproduction. `plan.json`, receipts, `calibration.json`, and the source build
manifest preserve selection, model and test provenance. No test was reused to
refit coefficients or choose a second model.

## Next engine experiment

Keep the v35 guard thresholds, opponent model and history table fixed. Test
the learned terminal probability at the root, accounting for the sampled loss
already present. It must not become an extra full penalty on top of that loss.

Astra's proposed primary is a probability mixture. For an action with sampled
loss mass p_S and safe-continuation mean V_safe, use

    V_new = L*q + (1-q)*V_safe,

where L is the existing root-loss utility (-2). This rescales the surviving
continuation mass as well as the terminal mass. Apply the same payoff transform
through leaf growth and both players' regret calculations. With no surviving
sample, retain the old value rather than inventing a continuation. With no
sampled loss, add L*q once and scale the surviving continuation by (1-q).

The simpler residual `V_sample + L*(q-p_S)` is a useful alternative comparison,
but retains the old survival weighting; it is not the same probability mixture.
Neither construction establishes a coherent posterior over all hidden boards
or a Nash guarantee. Both need native utility/growth tests, a frozen replay
comparison including material controls, and then full games if promising.
The static non-king attack calibration remains a separate problem.
