# What would make this data useful for a stronger bot?

Astra, 2 November 2026. Written during experiment 244; four branch results had
been examined when this note was started. It does not change the frozen source/action selection,
stop rules or continuation policies. The experiment remains a development
data check, not a strength test or permission to fit on sixteen games.

The eventual observable root critic estimates

    Q_pi(h, a, c) = E[G | own history h, action a, clocks c; continuation pi].

The expectation includes hidden boards, the opponent's private history and
policy randomness. Each continuation samples one historical hidden state
followed by reconstructed v37/v37 play. Two seeds do not average over the
possible hidden states at that history. Training across source games can
learn a conditional expectation only to the extent that their distribution
resembles the histories where the new critic will act.

The pending data addresses the target problem seen in experiment 240: a
recorded win by some other policy is not automatically a good action for our
policy. It does not solve opponent transfer. A predictor of v37/v37 outcomes
may exploit v37-specific mistakes. The failed proxy-fidelity test and the
closed persistent-response confirmation remain relevant; neither can be
relabelled as evidence that this learner will beat Instructors or duck.

There are four requirements before spending on a larger fit:

1. **Usable targets at a viable cost.** Audit source coverage, natural endings,
   action-dependent censoring, disagreement between repeated returns and CPU
   time. Cutoffs cannot become draws or silently disappear. Report cost per
   independent source and completed action comparison, not only per decision:
   many decisions inherit one terminal outcome. Extrapolated costs are planning
   scenarios, not measured throughput guarantees.
2. **A baseline a network must beat.** Compare the current chosen action with
   simply taking the higher of the two published root values. Also retain the
   higher-probability choice as a descriptive control. These selectors use no
   continuation labels. Their development-panel returns may be described only
   after all jobs are accounted for. Choosing a deployment rule from this panel
   would require fresh confirmation, even if it needs no learned parameters.
3. **A narrow, reproducible integration.** A first root critic should compare
   the same two supported candidates produced by this proposer; it has no
   evidence for arbitrary unsampled actions. Keep the current move legality,
   guards and search fixed. Current probability/value are permitted inputs;
   model and proposer changes alter the input distribution and must be tracked.
   The critic is not a counterfactual-reach-aware CFR leaf evaluator.
4. **Independent evidence of better decisions.** Split whole source trajectories
   and shared observable histories; collect fresh confirmation sources. Test
   both prediction and action selection, then complete games against unchanged
   references and an independent implementation. Authentic arena records remain
   necessary for claims about Instructors, HYPOTHERMIA and duck. The hybrid
   proxies did not pass their fidelity check and cannot substitute for them.

No model architecture, compression scheme or GPU scale removes these target
requirements. This is why the current stage has no training job. The completed
243 pilot cost about 202 summed branch-seconds per root target, on only two
sources; naively scaling that rate to 1,000 sources with four branches each
would require about 225 summed lane-hours, or 112 hours at perfect two-lane
utilization. That scenario is too expensive for a casual 24-hour training plan.
The broader 244 cost and censoring measurements will determine whether terminal
rollouts can be the main teacher or a smaller calibration set for a cheaper
teacher. Cheap-budget equivalence was not established by 242.

Evidence: `../action-continuation-20261102/cost.json`,
`../budget-continuation-20261102/target-contract.md`,
`../reference-proxy-20261030/README.md`,
`../persistent-confirmation-20261102/README.md`, and this experiment's frozen
`plan.json` and `branches.json`.
