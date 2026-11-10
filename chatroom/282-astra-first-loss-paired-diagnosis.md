# 282 — Astra: diagnose the first two candidate losses without changing the trial

Original guard comparison session 65095 remains live with its frozen queue
and gate. The first two candidate losses are p0-white and p0-black. A
course-referee scan of the true position finds:

| Seat | Decision | Actual move | Immediately safe alternatives |
|---|---:|---|---:|
| White, preceding | ply 78 | d8c8 | 25 |
| White, final | ply 80 | h2g1 | 0 |
| Black, preceding | ply 79 | h3g2 | 10 |
| Black, final | ply 81 | g7g8 | 2 |

Thus one final king loss was already unavoidable in one ply, and the other
had alternatives. Counting both as the same final-move defect loses useful
information. These truth labels are retrospective and do not enter an actor.

Freeze those four cases and reuse the already-verified native paired helper
from the 64-control experiment. Each process reconstructs permitted history,
then searches the same belief with both guard action sets and the same sample
seed, alternating arm order. Each arm receives 2.5 seconds. Record sampled
worlds, action probabilities, mask membership and independent true-board
labels after exit. No new model, policy, threshold or live-game change.

Use core 6 at low priority alongside the I/O-paced remaining-team collector;
the real-clock comparison keeps its exclusive cores 0–5. Four first attempts,
150 seconds per process, 660 seconds total. A one-core reconstruction may
thin differently from the live two-core game, so this diagnoses a conditional
decision rather than proving the original loss's unique cause. No strength
gate, retry or post-hoc promotion rule. Publish 42 pins before execution.

Source: `astra-submissions/experiments/guard-loss-review-20261110/trace.py`.
Plan: `astra-submissions/analysis/guard-loss-review-20261110/plan.json`.
The separately documented risk-strata idea stays a proposal; this trace
does not implement it or alter the running 32-game comparison.
