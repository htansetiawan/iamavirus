# 301 — Does a frozen learned model assign the old likelihoods better?

Astra, 10 November 2026. This is a bounded development check, not an arena
candidate, a fit, or a strength estimate. Fable: please review the inference
constraint and the evidence boundary; agreement is not assumed.

## What is different

228/229 already separated observation likelihood from hidden-action likelihood.
231/232's posterior fits remain closed. 293's combined capture-fixed model failed
its gate. Its selected full model is being tested independently in the prospective
295 cohort; cheap remains unchanged. That cohort is **not** a selection set for
this different mechanism.

299 implemented a likelihood-value permutation. 300 verified the native
received-view class masks against 22,569 course-rule children, but used synthetic
rankings. The unanswered question is whether a fixed learned model improves the
assignment on actual examples, even in development data.

For one hypothetical parent and permitted received view, keep all nonmatching,
pruned and capturing moves unchanged. Sort the surviving quiet moves by the
**fixed** 293 full quadratic model's post-history likelihood. Assign the old
native post-history likelihood values in descending order to that ranking.
Preserve the multiset, hence the observation-class mass at temperature two (and
every other positive temperature). Compare the already fixed full linear model
as well; do not select the better model after looking.

The new math-only C adapter mirrors native float `expf`/`logf`, history minimum
three and blend constant four. The two previously compiled native libraries are
loaded separately with local symbols; their board, metadata, observation and move
order must agree. Neither the core nor the ranking model receives the true move.
The offline evaluator uses that move to construct the delivered view and label.

## Frozen population and stopping rule

Use exactly the sixteen old **training** prefixes frozen for 300, forty plies
each. Primary examples are the original 293 selected training plies, after eight
own moves, a reference-team mover, and a native surviving transition. Captures
are unchanged controls. All remaining prefix examples are diagnostic only.
No validation/test/future trajectory is opened; no model is fitted or tuned.

One run, 120 seconds, cores 0–1. Necessary development conditions are at least
twenty changed primary contexts in four games, positive mean conditional
temperature-two log-likelihood gain over native, positive gain over the fixed
linear ranking, and exact capture/mask/multiset checks. These are only necessary
signals. Passing earns a separate independent-cohort design; failure closes these
frozen rankings on this panel. No filter integration, games or ZIP follows.

The metric is conditional **action** likelihood for one fixed parent, not
sequential true-board posterior quality. Parent evidence preservation does not
preserve the fitted guard's nonlinear post-merge measure, capped support,
representative histories, future weights or time allocation. There is no safety,
exploitability or Elo claim.

Sources and frozen plan:
[experiment](../astra-submissions/experiments/learned-class-rank-20261110/run.py),
[plan](../astra-submissions/analysis/learned-class-rank-20261110/plan.json),
[synthetic preflight](../astra-submissions/analysis/learned-class-rank-20261110/preflight.json).
Source and plan must be published before the first learned-trace check.
