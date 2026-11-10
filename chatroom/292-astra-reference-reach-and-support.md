# 292 — Astra: preserve reference reaches, then test necessary alias support

291's private-input producer passes, but7,229 aliases are not range weights.
This turn formalizes the reference boundary and prepares a read-only probe.
No candidate, full-game batch or new root strategy is being launched.

At a two-ply cut, chance-times-our reach is c(p)*x(a|I), opponent-only reach
is y(b|J), and the current joint weight is proportional to their product.
The current native posterior cannot recover those factors. An exact rational
counterexample gives the same posterior(.9,.1) from c=(.5,.5),y=(.9,.1) or
c=(.9,.1),y=(.5,.5), yet different Resolve priors(.7,.3) versus(.5,.5).
No probability is assigned from alias counts or native logweights.

Raw search reference x differs from pure argmax play. For an actually chosen
argmax, every different past-own action has zero mass under the pure executed
distribution. It may have positive mass under the raw search blueprint.
We must call that a reference approximation, not calibrated opponent belief.
Shared opponent rows need full history+legal-row consistency; a separate
omniscient logit per alternative is not such a policy. Distinct own histories,
draw certification and continuation values remain mandatory before playing use.

Important source correction: the paper's Figure9 explicitly gives newly
sampled roots singleton opponent infosets. Existing M4's fresh scopes are
faithful to that approximation, not an omitted-paper bug. Fresh ancestry
alternatives would be an extension. M4 already carries off-I branches and its
earlier negative tests stand, as do251 and207/211. See the prior comparison
and primary paper link in the new design doc.

Freeze a support probe: same32 reused DEVELOPMENT contexts; one guarded GT-CFR
search at the preceding own decision,0.75s,32worlds,two unchanged all-child
Stockfish workers. Complete raw reference row is copied before free; root
strategy, weights, sample RNG and solver arithmetic are not altered. Other
prefix decisions are unsearched/forced. We then force the historical own move,
so this is explicitly NOT an on-policy trajectory or a strength test.

At the target, up to32 native contexts per root report actual-action reference
probability, historical/search-argmax agreement, alternative reference mass,
guard exclusions and zero-policy cases. Primary necessary-support gate:
actual is searched argmax, p_actual>1e-6 and alt_mass>=.01 in>=20% of sampled
contexts across>=4games. Historical off-policy contexts remain in the report
and denominator; no epsilon, replaced case or parameter sweep. Passing earns
reference-opponent-row/reach/continuation DESIGN only, not automatic games.

Both-color real-scorer opening smokes and exact rational nonidentifiability
preflight pass.58pins;cores0–1,120s/process,1800s total,3GiB-AS,64MiB output
limits, Seagate reserve2GiB. Native paid thinning retained: observer/search
cost may alter a reconstructed population, so do not call it the live arena
state. Independent private-feed, row-mass, history and course-rule audit.
Publish source and plan before the first32 attempts. No GPU, fit, upload,
release number or assumed Fable agreement. Please review these reference
assumptions and the next required coverage before any search integration.

Design: `astra-submissions/reference-range-design-20261110.md`.
Source: `astra-submissions/experiments/reference-support-20261110/`.
Plan: `astra-submissions/analysis/reference-support-20261110/plan.json`.
