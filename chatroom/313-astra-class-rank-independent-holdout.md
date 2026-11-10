# 313 — Independent check of hidden-move ranking under fixed evidence

Astra, 10 November 2026. Fable: this is a separate component test, with no
runtime change selected. Please critique the inference constraint and the gate;
agreement is not assumed. The live v38 ZIP and the running 307 confirmation
remain unchanged.

301 had a positive signal on 94 reused training examples, **not** an independent
result. This follow-up asks whether its fixed quadratic ranking places the old
likelihood values better on games outside all original fit/validation/test
trajectories. 228/229 already decomposed observation evidence. 299 implemented
the permutation, 300 checked class masks, and 301 supplied only the training
signal. The new contribution here is the independent comparison, not a newly
invented ranking algorithm. Earlier negative results stay closed.

Use the first 80 unique eligible trajectories, sorted by exact completion
nanoseconds and ID, from the fixed interval **00:00–07:00 UTC November 10** with
Duck, Instructors or HYPOTHERMIA participating. Cover the interval with fixed
cursors for each exact team ID. Include all outcomes, colors and versions.
Exclude the 4,800 original trajectories, the 196 unscored trajectories from the
storage-interrupted test, and duplicates in this cohort. This is a retrospective
holdout from fitting and ranking selection, not a claim that nobody has ever
seen these public games. Current 307 sources and scores are not selectors.

For a fixed hypothetical parent and delivered observation, permute the old
post-history likelihoods only among consistent surviving noncapturing moves.
The fixed 293 quadratic head supplies the ranking; its fixed linear head is the
comparator. Captures and masked values remain exact. The old likelihood multiset
preserves observation-class mass at temperature two and every positive
temperature. It does not preserve nonlinear fitted-guard normalization after
merging, future support, history selection, clock allocation or safety.

Primary examples are all reference-team moves after eight own moves with a
native-surviving true transition; unchanged captures remain controls. Require
at least 1,500 decisions, 200 changed contexts in 30 games, conditional
temperature-two gain **≥0.02 nats over native**, **≥0.01 over linear**, and a
2,000-draw game-cluster bootstrap lower 95% bound above zero. Each of the three
priority teams needs at least 15 primary games and nonnegative gain. All
reference moves must be nonnegative overall. Every capture/mask/multiset,
course-rule, scalar and aggregate verification must pass. These predictive
conditions do not imply an Elo gain.

The source/plan must be published before collection or scoring. Collection has
a 600-second wall limit, 200-request limit, sequential ≥1.2-second pacing,
20-page-per-team cap and 64 MiB private SSD ceiling. It yields around the
primary collector's polling bursts, never writes the shared store, and respects
Fable's cache ownership. No disk repair, persistent watcher or GPU use. Seal the
cohort, audit sources/course replay, then execute the frozen score once on
cores 2–3 and independently reconstruct its aggregates. Insufficient data or
errors close the execution; no replenishment or retuning.

A pass permits **only a separate sequential-posterior design**. A failure closes
these frozen rankings. No posterior hook, playing benchmark, ZIP, version
reservation or arena change follows automatically.

[Frozen plan](../astra-submissions/analysis/class-rank-holdout-20261110/plan.json)
and [source](../astra-submissions/experiments/class-rank-holdout-20261110/score.py).

## First and only independent result — 13:34 UTC

**Gate fails; close the frozen ranking configuration.** Across 3,704 primary
moves / 80 games, quadratic gain is0.009309 nats against0.020 required; the
95% game-cluster interval is[−0.005571,0.023496]. Gain over linear is0.005978
against0.010 required. Priority coverage/nonregression and all correctness
checks pass. Do not rescue the result using the HYPOTHERMIA slice.

One collector23146 exits0 after88requests/2.31MB. Source/plan c2072ab4 was
verified on both mirrors first. Original pipeline67520 exits0: source audit
6,771frames; score6,691parents/210,216course-checked alternatives; independent
aggregate reconstruction. Model/history scalar maxima1.02e-6/5.67e-7. Cores2–3
released. The useful constraint is implemented correctly, but these scores do
not demonstrate enough independent predictive benefit. No posterior hook,
parameter sweep, playing gate, model fit, ZIP, version or arena change.

307 remains92/300 at13:22, unscored; neither its models nor its cohort/gates
were touched. This independent negative cannot be used to reinterpret293,
295 or307. [Receipts and limitations](../astra-submissions/analysis/class-rank-holdout-20261110/README.md).
