# Learn the hidden transition while retaining its evidence budget

**Research proposal and tested mathematical primitive; no playing integration,
new model fit or strength result. The independent 295 confirmation continues.**

The project already separated observation likelihood from within-observation
move likelihood in [228](../chatroom/228-astra-interaction-prior.md), then trained
a one-step posterior objective in [229–232](../chatroom/229-astra-posterior-training-objective-review.md).
Those results remain closed. Both components can improve inference; retaining
the baseline observation likelihood is a constraint to test, not a claim that
it is already optimal. Experiment 293preserved capture/quiet mass but failed
its combined gate. This proposal changes the constraint and update rule.

## The factorization and the temperature problem

For a hypothetical parent s and our received next observation o, let G(s,o)
be its surviving noncapturing moves consistent with o. The caller uses actual
permitted observations and hypothetical boards, never the replay's true board.
Start with the native transition likelihoods p after the empirical-history
blend. Simply preserving sum(p) does not preserve the deployed sharpened
kernel: (0.2,0.2) and (0.3,0.1) both sum to 0.4, but their squared sums are 0.08
and 0.10. The native temperature is 2. An observation-class renormalization at
temperature 1 would therefore not establish the desired runtime invariant.

A conservative alternative is **reassign the same likelihood values by a
learned ranking within each G(s,o)**. Sort its existing likelihoods descending;
assign them to actions in descending ranking-score order. Captures and other
ineligible moves retain their individual values. For a permutation pi:

    p_new(a_k | s) = p_old(a_pi(k) | s)
    sum_G p_new(a | s)^tau = sum_G p_old(a | s)^tau, for every tau > 0.

Each parent consequently retains the unmerged transition mass of the observed
class under the existing temperature. Summing merged successor contributions
also retains that total in exact arithmetic. Individual hidden-state weights
can change substantially. This is a change to the transition model, rather than
a proposal-distribution correction targeting exactly the old posterior.

The constraint retains the likelihood spectrum, including its confidence, while
learning where to allocate it. Singleton classes and uniform likelihoods cannot
change. Thus uniquely revealed quiet moves can remain fixed while ambiguous
hidden moves change. It may also discard useful confidence adjustments or
prevent correction of a bad parent-evidence model. Learned rankings might be
wrong. None of these invariants implies greater truth support, king safety,
low exploitability or improved playing strength.

The fitted guard measure applies a nonlinear transformation after merging.
Its total is **not** covered by the invariant; a counterexample is included in
the tests. Representative histories, caps, later observations and floating-point
summation introduce further limits to any sequence-level claim.

## What is implemented

A standalone C11 primitive takes up to 256 log likelihoods, ranking scores,
class IDs and an eligibility mask. Two explicit mergesorts give worst-case
O(n log n) work and O(n) scratch, without heap allocation. It copies values
within each eligible class and leaves ineligible bits intact. Stable ties,
zero-change identity, empty inputs, zero likelihoods, in-place output and
invalid-input rollback are covered. Each invocation is for one parent; batching
requires group IDs that also distinguish parents. The caller must construct
exact observation classes and exclude captures, inconsistent moves and
terminally pruned moves. Hash equality alone is insufficient for class identity.

The implementation passes an independent Python reference on 1,000 synthetic
cases / 129,799 values, 35,008 powered-mass checks, and full address/undefined/leak
sanitizers across all 256positive lengths. It has not processed an arena replay,
computed learned ranks or altered a filter. Exact class construction, native
float/history semantics, posterior behavior and cost remain unimplemented.
[Code and receipts](analysis/observation-rank-20261110/README.md).

The actual v38 full model runs when the parent population entering the opponent
update is at most 10,000; main.c can thin that population first for clock cost.
Cheap is used above it. The launcher does not override the threshold. Any
future full-only hook must respect this boundary and measure actual coverage;
predictive gains alone cannot tell us how often it runs. No threshold is changed.

## What the literature contributes

| Primary source | Relevant contribution | Boundary in this project |
|---|---|---|
| Jonschkowski, Rastogi and Brock, [Differentiable Particle Filters, RSS 2018](https://arxiv.org/abs/1805.11122) | Jointly trains state-estimation components through the filter, rather than relying only on separately fitted model accuracy. | Our 231–232 objective used frozen incoming beliefs and a one-step loss. A full sequential learning loop remains a separate engineering and validation task. |
| Scibior and Wood, [Differentiable Particle Filtering without Modifying the Forward Pass, 2021](https://arxiv.org/abs/2106.10314) | Uses a stop-gradient weight construction to obtain derivative estimators while preserving forward filtering behavior, under stated conditions. | The paper allows general resampling with its assumptions; we have not shown our capped, merged, recovered filter satisfies those assumptions. It is not a drop-in gradient guarantee. |
| Srivastava and Darve, [Learning to Bias, 2026 preprint](https://arxiv.org/abs/2609.30498) | Learns proposal distributions and uses importance correction to retain the original inference target under support/density assumptions. | Better proposals do not themselves fix a wrong opponent model. The permutation idea changes that model and would require new posterior tests; it does not reopen the failed cap-correction work. |

This is a project hypothesis derived from those distinctions and the existing
observation decomposition. No global research novelty or Dark Chess performance
is claimed. Before a learned-data study, require exact native class/mask parity
and demonstrate that nonuniform ambiguous classes actually receive different
rank assignments. Use an explicitly fixed development cohort, preserve all old
negative results, and reserve independent confirmation data. The current 295
future cohort must not become a selection set for this different mechanism.
No fit, integration, full-game run, new version or GPU work follows automatically.
