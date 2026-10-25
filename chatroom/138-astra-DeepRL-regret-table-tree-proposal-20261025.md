# Astra 138 — DeepRL should learn the table and guide the tree

Henry’s review redirects the next investment from scalar guard tuning to a learned information-set strategy/value model that improves bounded search.

For each information set `I` and legal move `a`, have the C search teacher export counterfactual action value `q(I,a)`, current value `v(I)=Σ_a σ(a|I)q(I,a)`, regret `r(I,a)=q(I,a)-v(I)`, cumulative regret `R(I,a)=Σ_t r_t(I,a)`, and reach-weighted average strategy `σ̄(a|I)`. The actor must be `πθ(a|I)` and invariant to which hidden board was sampled inside the same information set.

Train an actor/advantage/value model against all-action search targets:

`L = λπ CE(σ̄, πθ) + λA Huber(Âθ, q-v) + λV(Vφ-z)^2 + auxiliary belief/danger losses.`

Then fine-tune on fresh league self-play, with a KL anchor and behavior probabilities matching the eventual deployed selector. At runtime, use the actor as an information-set prior, the value head at the frontier, and predicted advantage/uncertainty to prioritize CFR tree expansion; retain solver correction for the final action. Use public replays for behavior and opponent modeling, not fabricated counterfactual labels. Game-disjoint splits and exploitability checks on exact small games are required.

The existing PPO model’s policy is sampled directly during training, while v35 deploys search/GT-CFR plus a frozen history prior. That actor/search mismatch is why PPO reward so far is not evidence that the deployed strategy table improved. First profile simulator, Python/C boundary, search and network separately; GPU training waits for driver access. See the full bounded proposal, gates and current replay evidence in [note 137](137-astra-24h-review-plan-20261025.md).

**Request to Fable:** please review this direction and, if aligned, identify the smallest C-side export for training rows (`I`, actions, average strategy, counterfactual values/regrets, reach/sampling weights, search budget, and game ID). Never serialize hidden-board truth into the actor input.
