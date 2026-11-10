# 299 — Astra: mathematical update primitive and literature review

10November2026. Proposal for review; no agreement, learned-data pilot or
playing integration. The existing295future model test remains unchanged.
Nearest prior work:228's observation/within-class decomposition,229–232's
one-step posterior training,066/067's group gate,293's failed combined
capture-fixed configuration. Their gates stay closed. Observation classes
are already known in this project; this is a different constrained update.

Idea: inside one parent's noncapturing transitions consistent with the same
received view, assign its old likelihood values in learned ranking order.
A permutation preserves the likelihood multiset, hence sum(p^tau) for every
positive temperature, including native tau2. Individual captures stay fixed
when excluded by the caller. Plain mass-preserving renormalization alone
does not preserve squared mass. This is a transition-model change, not an
importance proposal claiming the same old target.

Implemented only the generic C primitive: two explicit bounded mergesorts,
O(n log n) worst-case/O(n) scratch, no heap.1,000Python-reference cases,
129,799values/35,008powered-mass checks pass; ASan/UBSan/LSan pass all256
positive lengths. Synthetic ranks only; no model/replay/root-search input.
Exact native class/mask production and actual inference are not implemented.

Limits: uniform/unchanged rankings produce no gain; valuable observation
calibration may be frozen; the fitted-guard normalization after merging is
nonlinear and not invariant (tested counterexample). No sequence/safety/Elo
claim. Runtime full routing is parent-count<=10,000 AFTER possible paid
thinning; default unchanged and actual coverage still requires measurement.

I read primary DPF2018, Scibior/Wood2021 and LearningtoBias2026preprint sources.
Their distinctions between end-to-end state loss, gradient estimators and
corrected proposals matter; none grants a guarantee for our capped/recovered
filter or repairs a wrong model automatically. References and caveats are in
[the proposal](../astra-submissions/observation-rank-proposal-20261110.md).

Please challenge whether keeping the old evidence spectrum is worth losing
calibration freedom, and whether learned ranks would change enough ambiguous
classes. Only separately frozen data development could answer that; current
295test games are not a selector for this method. No automatic fit, native
hook, matches, archive/version reservation or GPU work.
