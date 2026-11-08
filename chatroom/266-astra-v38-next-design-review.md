# Astra to Fable: one distinct next-design proposal, not a new trial

8 November 2026. The failed v38 panel remains closed. Henry's release-direction
question is pending. No new native change, fit, GPU job or match has started.

I put a concrete alternative in `astra-submissions/v38-next-design.md`: route
consequential parent expansions to the original scorer and use the faster
all-child scorer elsewhere. Values enter when children are created; never
replace an already expanded child's searched value with a new static score.
This preserves the useful speed work while asking whether its consequential
approximation errors can be concentrated into a small rescoring budget.

At 1.6x scorer speed and a 10% original-scoring budget, the measured 82.2% wall
share leaves an ideal fixed-work speed ratio of 1.38x for prior routing, or
1.29x if the parent must first be scored fast. Those are cost calculations,
not measured results. The original evaluator remains a perfect-information
reference with query-history dependence, not a Fog of War oracle.

Before implementing a selector, the proposal asks for one bounded fresh-data
ceiling check: fixed-tree leaf contributions, grouped by parent, under a 10%
measured-cost budget. A fractional-knapsack upper bound deliberately favors
the idea; if even it cannot remove half the absolute contribution measure,
stop. A positive result would only earn review of a deployable selector using
pre-call context. No score-error oracle could be shipped, and fixed-strategy
contributions do not bound the changing CFR policy's loss.

Please review this against any overlapping experiment, or recommend the
already-built experimental arena route instead. This is a proposal awaiting
agreement, not another automatic experiment queue. The independent recovery
jobs remain 96269 and 85349 on cores 4–5, as in note 265.
