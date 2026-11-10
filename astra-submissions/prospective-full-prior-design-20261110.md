# Confirm the full prior before changing the engine

The next useful question is whether the capture-preserving full model's signal
survives on games that did not exist when it was selected. Experiment 293 was
not a passing candidate: its combined gate failed. Its full model's gain of
0.05120 nats over baseline and 0.03495 over the matched linear model motivates
one new, explicitly post-selected hypothesis. Cheap remains unchanged.

For each hypothetical parent board let C be capturing moves and Q all other
moves. The frozen residual d changes quiet logits to

    z'(q) = z(q) + d(q) + logsumexp_Q(z) - logsumexp_Q(z+d).

Captures retain their logits and the original native global normalizer. Thus
all capture likelihoods and the total quiet mass are preserved for that parent;
only relative quiet choices change. The existing history mixture is unchanged.
This does not prove an unchanged posterior after a sequence of quiet moves,
a retained true board after caps, equal runtime, or safer play.

The nearest earlier implementations are 066/067's rejected group-mass gate
(which varied the opposite probabilities), 228's unconstrained interactions
(which harmed surprise captures), and 293's failed combined configuration.
231/232's posterior-objective results remain closed. This test does not rerun
those tests, relax their thresholds, reclassify the full subgroup as a combined
pass, or integrate the selected head. Its material difference is an entirely
future cohort and the expressly narrower full-only intervention, with no fit.

We will seal the first 300 eligible new trajectories after 07:15 UTC on
November 10, excluding all 4,800 trajectories in the prior study. The fixed
cohort and full predictive gates are in the [collection contract](analysis/prospective-full-prior-20261110/README.md).
No partial-cohort NLL is reported. All outcomes and opponent versions are
included; team IDs only identify evaluation movers and never enter the model.
The three minimum opponents receive explicit coverage and nonregression checks.

The collector preserves raw public data and page provenance on the external
disk. Fable's watcher remains the owner of our own games. Missing earlier owned
replays delay sealing. Rule/metadata mismatches stop the run; they are not
quietly dropped. Model weights and all code dependencies are pinned before any
eligible game exists. The GPU service is untouched.

After the cohort is sealed, one native scoring pass and an independent scalar
and course-rules verification determine the result. A predictive pass merely
allows designing the native cost and actual-filter tests. Those must check the
full/cheap switching condition, capture-turn skip semantics, truth support,
posterior weights, thinning under equal time and late-game cost before any
playing candidate. A predictive failure closes these frozen weights without
an automatic retune. The original combined gate remains failed either way.

This research confirmation proceeds within the user's improvement campaign.
Fable has been asked to review the model boundary and this protocol; no reply
or agreement is assumed. The optional human research-priority question has no
reply yet; this bounded confirmation is Astra's stated working choice, not an
inferred approval of an arena change.
