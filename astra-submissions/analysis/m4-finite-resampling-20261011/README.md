# Finite-state resampling: mathematically valid, fails the posterior gate

**Do not promote either new cap variant.** The inclusion-corrected sampler
loses true-state support across all three development seeds. Its whole-game
bootstrap interval is negative; risk-calibration changes are inconclusive.
No runtime default, model, ZIP or arena version changed. Stop cap-reweighting
variants as the immediate development direction.

## What changes, and what does not

The weighting distortion was already documented in chatroom 060. The earlier
061/062 experiment retained the original exponential-race winners and corrected
their weights using an additional threshold; it failed its sequential gate.
This experiment tests a different finite-state estimator with fixed total mass.

For positive weights `w_i` and cap K, solve
`sum(min(1, w_i / lambda)) = K`. Retain heavy states at their original weights.
Each smaller state is included with probability `w_i / lambda` and, if selected,
receives weight lambda. Systematic tail selection yields K distinct states.
Expected retained mass for each state is its input mass; total mass is constant
on each draw before floating-point storage. This property does not establish
an unbiased future nonlinear filter or a stronger bot with a misspecified prior.

The independent C implementation uses sorted log weights and separately scaled
tail accumulation, O(n log n) time and O(n) temporary memory. It has no access
to boards, truth, player names or move labels. Reference:
[Fearnhead & Clifford, 2003](https://doi.org/10.1111/1467-9868.00421).

As a small analytic illustration, weight-proportional sampling without
replacement from `[.6, .2, .1, .1]`, retaining two original weights and
renormalizing, represents approximately `[.70893, .17546, .05780, .05780]` in
expectation. The new method has lambda .4, keeps .6, and samples one tail state
with probabilities .5/.25/.25, assigning it .4. Its expected represented
distribution is the input distribution.

Seven native tests cover independent inclusion probabilities and expected mass,
fixed-size uniqueness, exact no-compression identity, invalid inputs, extreme
random offsets, large log-weight ranges, and **100,003 → 10,000** compression.

## Sequential experiment

The same immutable 26-feature opponent prior, historical moves and observations
are used in all arms. Fixed cap 10,000, seeds 41, 73, 109. The existing development
set has 42 primary games / 1,650 decisions, plus a separately retained diagnostic
game. Seeds are repeated measurements of those games, not additional games.

Three arms: original cap; new selection with corrected weights (`finite`);
new selection with original weights (`raw`). The raw arm separates selection
changes from reweighting. No parameters were changed between seeds. The
unchanged control at seed 41 reproduces **all 1,680 non-timing fields exactly**.
All 18 cohort runs exit successfully, preserve observation consistency and
match the historical rule labels. Only isolated copies of native source change.

| Seed | Control support / collapses | Corrected support / collapses | Raw support / collapses |
| --- | ---: | ---: | ---: |
| 41 | 1,386 / 13 | 1,310 / 18 | 1,349 / 14 |
| 73 | 1,361 / 12 | 1,357 / 9 | 1,358 / 17 |
| 109 | 1,355 / 16 | 1,297 / 20 | 1,340 / 14 |

Across **4,950 decision-seed observations**, corrected support falls
4,102→3,964, a **2.788 percentage-point decline**; game-bootstrap 95% interval
for the change is **[−4.904, −1.060] points**. Collapse counts across replicates
rise 41→47. Bootstrap samples whole game IDs, retaining their decisions and all
seed replicates together. Reused development games limit generalization.

| Mean metric across seeds | Control | Corrected | Raw |
| --- | ---: | ---: | ---: |
| Hidden-attack Brier | 0.0140209 | 0.0143212 | 0.0139368 |
| Historical fatal-move Brier | 0.0098078 | 0.0096725 | 0.0098136 |
| Update CPU seconds / seed | 42.369 | 43.791 | 43.857 |

All paired Brier intervals cross zero. Corrected fatal-Brier reduction is
0.0001354, interval [−0.0000989, 0.0004097]. Its hidden-attack Brier moves in the
wrong direction. Raw selection's support change is −1.111 points, interval
[−3.312, 0.977], with no established calibration gain. Neither arm earns the
fresh-data, live-cap or full-game promotion gate.

This result does **not** prove that biased weighting is generally superior.
It rejects this replacement under the tested prior, capacity and histories.
The live cap, adaptive clock behavior and arena v30 implementation differ.

## New data, separate from fitting and the gate

Public snapshot at **2026-10-11 17:39:42 UTC**: active arena v30 is
**1778.4629 Elo, 160W–25D–181L / 366 games**; duck is 1929.3721 Elo.
Ten newly cached games are **5W–1D–4L**, with all **881 frames** independently
checked against the referee for full boards, both views, moves and outcomes.
One Knight Vision loss has no immediately surviving final move; the other three
losses do. Do not label the unavoidable final move as an avoidable king blunder.

Combining these ten with the preceding six creates 16 rule-checked chronological
histories with zero overlap with the development set. Their tactical summaries
were inspected; they are not a blind holdout. They have not been used to fit a
model or run these cap variants. `next-temporal-cohort/` contains the prepared
input and source hashes for a later candidate.

## Next direction and artifacts

The protected-bait case documented in the preceding support-loss report already
fails with the true board present and all 59 retained states searched. Improve
or calibrate continuation evaluation under the opponent's information before
adding another cap weighting rule. A safe move's low frontier value is not a
proof of eventual loss; neither is one-ply survival proof of a win.

`inventory.json` links compact files to originals on Seagate at
`/media/henrytan/seagate/iamavirus/astra/m4-finite-resampling-20261011`.
It records original and compressed hashes. Executables and Python bytecode stay
on Seagate; source, all per-decision rows, reports, replays and reproducer scripts
are retained here. Unit-test validation records the observed successful run and
test-source hash. `gate/complete.json` hashes the completed native experiment.

Reproduce with `m4_finite_build.py` using the immutable native source from the
intent/prior experiment, then `m4_finite_gate.py` using the support-loss trace
directory. `M4_CAP_MODE` is only an isolated experiment option. The shared C
checkout is clean and no change is proposed for Fable to merge.
