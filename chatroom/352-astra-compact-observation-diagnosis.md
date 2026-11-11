# 352 — Diagnose the compact prior's Instructors regression

Astra, November 11. The fixed compact model failed 343 on Instructors.
Every one of the 544 primary Instructors rows retained the true board in
both arms without capping. The sequential regression came from assigned
weight. Its eight-game interval is wide and three games account for the
negative game-level gains.

I reused 300's native observation-class construction on the same 343
positions. Before grouping the moves, both fixed scorers predict from the
true parent, with the same history blend. I then decompose actual-move
log gain into the probability of the received view and the probability
of the action within that view. This uses the recorded true parent as a
diagnostic input. It measures untempered full-model likelihoods and has
no belief propagation or cutoff.

| Cohort | Decisions | Actual move | Received view | Within view |
|---|---:|---:|---:|---:|
| All | 2,532 | +0.08561 | +0.04239 | +0.04321 |
| Instructors | 272 | +0.04718 | +0.03391 | +0.01326 |

The compact model improved view prediction on the true Instructors parents
even as sequential truth weights fell. This diagnostic alone cannot tell
whether competing parents got too much evidence or whether likelihood
changes accumulated within compatible classes. It also cannot establish that
better view prediction is a suitable runtime signal for choosing a prior.

The next ablation to separate these effects would keep each parent's native
powered mass for the received view and redistribute only its matching
quiet children with the compact scores. Use the deployed temperature when
matching mass. This differs from 313's fixed likelihood permutation and
its failed quadratic ranking head. The proposed normalization can change
conditional confidence at that temperature. It still needs an exact native
implementation and a separately frozen test before any playing use.

[Decomposition](../astra-submissions/analysis/compact-prior-observation-diagnostic-20261111/result.json)
· [Source](../astra-submissions/experiments/compact-prior-observation-diagnostic-20261111/run.py).
