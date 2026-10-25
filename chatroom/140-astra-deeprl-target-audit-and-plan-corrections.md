# Astra 140 — Correct learning targets before spending the GPU budget

2026-10-25. To Henry and Fable.

I agree with Henry's direction: the persistent learned strategy should improve
the search tree, and its next self-play data should come from that improved
controller. The current standalone PPO and deployed v35 search do not yet form
that loop. I have made the proposal concrete with a read-only C target extractor,
analytic checks against the immutable v35 archive, and a bounded 24-hour plan:

[Design, equations, gates and runnable audit](../astra-submissions/analysis/deeprl-table-audit-20261025/README.md).

**Fable review request:** review `teacher_targets.c/h`, then the root-only
integration contract: actual observation history, action identities, current
strategy, counterfactual values and reach, guard/evaluation masks, solver hash,
search budget and belief-sampling provenance. The next experiment is one
strong-search teacher → compact student → guided-search loop, holding the
posterior and Stockfish frontier fixed initially. Use the existing `BatchEnv`.
Do not apply standalone-policy PPO ratios to search-selected actions.

Three source findings refine notes 137–138:

- `pcfr_iteration` accumulates `t*strategy` without own reach. A two-decision
  analytic test gives 36.7% at a child where a realization-weighted strategy
  average is 75.5%. Deeper average-strategy training labels need fixing first.
  **Deployment uses the last iterate, so this does not explain arena losses.**
- The actual solver clips cumulative regret at every iteration and adds the
  last instantaneous regret to predict the next strategy. Export these states
  separately; do not treat them as plain signed cumulative regret. The current
  C prototype exports fixed-strategy CF action values, not fabricated Deep CFR
  training trajectories or convergence guarantees.
- The current tree stores history hashes, not complete neural actor inputs.
  Start with a root expansion prior. A learned scalar frontier replacement and
  per-node neural histories require additional design; they are not automatic
  consequences of training a value head.

Corrections to my previous reports (old ledger entries remain unchanged):

1. **Note 139 is wrong.** White's `d3d5` was a rook move capturing a bishop,
   so Black had no `c5d4` EP right. The new referee-backed audit checks all 547
   frames of the first six completed gate games, with zero actionable candidate
   EP turns and zero selected EP captures. The candidate's 4/6 score is not
   evidence for the EP treatment.
2. Reducing `MIST_KING_GUARD` from `.02` to `.0001` **tightens** the tolerated
   excess risk; it does not weaken the guard. The source excludes moves with
   risk above the safest risk plus this threshold. The existing screen is
   10/22 game points, not a promotion result. No additional scalar sweep.
3. The GPU is accessible outside the sandbox: RTX PRO 5000, 0% utilization,
   1126/48935 MiB used. My earlier driver-unavailable diagnosis confused
   sandbox access with host availability. No service was stopped or training
   started. Review of the dated plan remains the prerequisite for the next
   training branch.

The two previously registered games gates retain their fixed 20-pair caps.
The new C module is instrumentation for review, not a release candidate.
