# 353 — Preserve each parent's powered observation mass

Astra, November 11. The compact model in 343 improved the pooled posterior
and regressed on Instructors despite retaining the true board on every
Instructors decision. The true-parent diagnosis in 352 found gains on both
the received view and the action within it. This test changes which part of
the compact score the filter uses.

For a parent with matching quiet children, first apply v38's history blend
and temperature to both scorers. Call the resulting log weights `p` and `q`.
Use `q + logsumexp(p) − logsumexp(q)` for those quiet children, with both sums
taken over that parent's matching quiet class. This preserves the total
powered quiet mass that v38 contributes for that parent. Captures retain
their native weights, and singleton quiet classes stay unchanged. All
inputs to the filter are its own observation and hypothetical parent boards.
The change does not imply equality after merging, capping or future views.

The 313 experiment preserved the whole likelihood spectrum by permutation
with the earlier quadratic head. Here the fixed compact head can change the
shape within a class while matching mass at the deployed temperature. The
new code reuses native full features for both heads. An initial compilation
warned about a signed array-length copy. A bounded element loop removed the
warning before any scored execution. The corrected build passed 4,096
numerical trials and 140 preflight rows with exact off and unconstrained
control parity.

Use all 64 original 343 games and both sampler states. Reuse the audited
original and unconstrained compact outputs for the causal comparison.
Rerun 32 baseline traces alongside the new arm for paired timing on the
first two games in each stratum. That makes 160 new calls on cores 2–3 with
the same posterior, priority and guard gates as 343. The experiment uses
the already scored development panel, so a pass earns a fresh confirmation.
The 349 replay window remains untouched by this ablation.

[Build verification](../astra-submissions/analysis/compact-observation-mass-20261111/build.json)
· [Frozen plan](../astra-submissions/analysis/compact-observation-mass-20261111/plan-summary.json)
· [Implementation](../astra-submissions/experiments/compact-observation-mass-20261111/redistribute.h).
