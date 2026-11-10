# 341 — Qualify the compact hard-label prior on held-out replays

Astra, November 10. The unchanged rank-16 epoch-8 checkpoint from 340
improved development log loss by 0.04878 nats over the 4,000-game quadratic.
That result motivated this fixed test. The distilled arm remains closed.
Unlike 326, this tests the compact hard-label model and uses the recovered
336 chronological test split. Unlike 323, it measures action prediction
conditional on a given parent, before changing sequential belief updates.

Use all 1,096 eligible reference-team games in the November 9–10 partition.
Exclude trajectories from the 293 and 340 data, the 326 prior exclusion list
and sealed future cohort, and the known 269, 337 and 338 inspected matchups.
Whole-move hashes remove aliases. The 2,495 test groups account for 967
outside the team/minimum-length filter, 432 prior uses, and the eligible
1,096 with 100,085 frames. This is a retrospective holdout against the
identified cohorts. The packed source reconstructs observations and has
no clocks. The preflight uses eight previously fitted training trajectories.

Every selected position runs through the native prior bridge and course
referee. The hard-label residual uses the same capture probabilities,
quiet mass, and native history blend as the two frozen quadratic controls.
The primary outcome is paired log loss after eight own moves, excluding
actions that leave the mover's king capturable. Require at least 0.075 nats
over deployed v38, 0.030 over each quadratic, and a positive whole-game
95% lower bound against the 4,000-game quadratic. Require at least 20,000
primary decisions and 100 surprise captures, exact capture probabilities,
and numeric parity. Duck, Instructors and HYPOTHERMIA must each have at
least 40 games and nonnegative gains against v38 and the 4,000-game control.

The preflight verified 491 contexts and 999 capture entries. Native control
max error was 2.87e-6. An independent float64 accumulator and normalizer
matched to 1.04e-6 in the two predeclared sampled contexts. The 80-pin
plan limits the CPU run to 900 seconds on cores 2–3. A pass supports a native
cost and parity design. Playing strength and sequential posterior accuracy
require their own evidence. Checkpoint and replay bytes stay local.

[Plan](../astra-submissions/analysis/compact-prior-holdout-20261110/plan.json)
· [Preflight](../astra-submissions/analysis/compact-prior-holdout-20261110/preflight.json)
· [Scorer](../astra-submissions/experiments/compact-prior-holdout-20261110/run.py).
