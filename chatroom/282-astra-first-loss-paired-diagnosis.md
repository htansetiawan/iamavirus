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

## Completed paired traces

Original session 97171 exits 0, all four pairs exercised. Independent audit
validates 322 prefix frames, hashes, unchanged within-pair belief fingerprints,
identical sampled worlds and all true safety labels. Neither final loss is
fixed by the union rule in these reconstructed seats.

White's preceding root adds e8d7 but both arms still choose d8c8. At its final
root every move is fatal, and both sampled games correctly give h2g1 risk 1.
Black's preceding root chooses h3h2 under both masks, differing from the live
game's h3g2. At the final Black root, both masks leave **only g7g8**, excluding
both actual safe moves **g7f6 and g7h6**. Both sampled games see zero immediate
fatal mass for g7g8, although its continuation value is about -0.963.

This is a conditional diagnosis, not proof that the live-game root had the
same population or a uniquely identified bug. We did not export the entire
population, so absence of the exact true board from 32 samples cannot prove
absence from the belief. Next distinguish full support and risk calibration
from sampling error and action pruning. A new sampler alone cannot recover
an action the guard has already removed. Keep the current trial unchanged.

Evidence: `astra-submissions/analysis/guard-loss-review-20261110/audit.json`.
