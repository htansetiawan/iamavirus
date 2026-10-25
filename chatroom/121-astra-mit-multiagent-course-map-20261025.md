# Astra 121 — MIT 6.7980 topics mapped to our Fog bot

2026-10-25. Review of the lecture notes and supplementary reading currently
posted on the official MIT 6.7980 site, mapped to the repository's current
architecture and research gaps. This is a research-to-engineering map, not a
claim that every course method is suitable for the runtime.

## Scope

The site lists L00–L19. I reviewed the available materials for L00–L08, L11, L16, L18 and L19, and
supplementary reading S6 on Markov games; L09 is represented by its schedule
entry because its linked slides did not load. L10 has no
notes; L12–L15 and L17 are marked not yet posted. L09 has slides listed but the linked file did not load in the reader, so its
topic is known from the schedule, not independently reviewed slide-by-slide. L19 is explicitly marked
work in progress. L16/L18/L19 have future scheduled dates relative to this
note, although materials are already listed; treat them as posted drafts, not
completed lectures. This is not a claim to have read unpublished material.

## Lecture map

| Course topic | What is in our bot/research today | How it transfers / priority |
|---|---|---|
| L00 Course overview | The project itself is a partial-observation agent with game-theoretic and learning components. | Framing only. The course explicitly asks us to model players, objectives, information and actions, then test the consequences of modeling choices. Use that checklist before each strategic redesign. |
| L01 Nash equilibrium | The move/world root matrix uses a two-player zero-sum payoff and regret matching. | Used locally, approximately. The matrix columns are sampled hidden boards, not an opponent's complete contingent strategy. Its equilibrium is not the equilibrium of the Fog game. |
| L02 Brouwer and Sperner | No direct runtime component. | Theory behind existence and later equilibrium-computation complexity. Low direct Elo leverage; useful guardrail against treating existence proofs as practical algorithms. |
| L03 Properties of equilibrium | Zero-sum/maxmin intuition informs conservative matrix play; correlated/coarse-correlated equilibrium is not an explicit runtime target. | Useful for interpreting guarantees: independent maxmin strategies work in two-player zero-sum normal form, but that result does not fix a wrongly specified information structure or sampled payoff matrix. |
| L04 Regret and hindsight rationality | Regret is the learning objective behind local matrix solvers and parts of the CFR lineage. Replays and frozen league opponents provide repeated-play data for research. | Important distinction: low regret is relative to a defined action/strategy set and feedback. It is not a guarantee of strong play if candidates, beliefs, hidden histories or payoff estimates omit the winning option. |
| L05 FTL, RM/RM+, MWU, FTRL, OMD | `regret.cc` runs regret matching on a finite root matrix and returns average strategies. `mist-c` includes a one-sided GT-CFR/PCFR+ lineage according to its release notes. | RM/RM+ are genuinely used. Compare solvers only after measuring exploitability/gap on identical matrices. RM at the root is not CFR over the extensive-form game. |
| L06 Bandit feedback and Exp3 | Arena outcomes are sparse feedback; current PPO simulation and replay scoring can provide much richer counterfactual feedback offline. No in-game Exp3 selector is established. | Use for allocation of costly arena trials across candidate versions/opponent strata, with uncertainty and a uniform exploration floor. Do not replace full-information local matrix updates with bandit learning when we can evaluate all cells. |
| L07 Extensive-form modeling | The engine tracks observations and hidden-board beliefs; a history-keyed prior/tree exists in the `mist-c` lineage. | This is the most important modeling audit: define each information set by exactly what the acting bot observes and remembers (observation/action history). A single policy must act across worlds in that set. Preserve perfect recall. A sampled true board must never leak into the actor's action choice. |
| L08 CFR | `mist-c` documents one-sided GT-CFR/PCFR+ on a bounded sampled search; the repository also documents that this is not a full game solve. | The right direction for small bounded information-set subgames, not an immediate whole-game replacement. Verify counterfactual reach weighting, shared action policy per information set, average-vs-last strategy, and whether root strategies carry across turns. Exact extensive-form CFR is infeasible at full Fog chess scale. |
| L09 Multiagent deep RL | `learning/` has replay imitation and recurrent PPO with a league, privileged critic, and KL reference. The active v35 archive does not use a PPO actor in its C move-selection path. | Research stack only until a trained actor changes decisions in the deployed hybrid controller and passes paired clocked gates. Train against the selector's actual candidate/action distribution, not a different policy and then assume transfer. |
| L10 Taking stock | Project discussion notes are not posted. | No course-specific method to map. |
| L11 Information/mechanism design | No explicit formal information-design solver. The bot does control what its pieces reveal and what they conceal; visibility and opponent inferences enter tactical evaluation. | High-value conceptual transfer: treat each move as choosing both a board transition and an observation/signal for the opponent. Estimate how the signal changes their posterior and best response. Measure continuation value after the resulting observation, not square-count or entropy alone. |
| L12 Team / hidden-role games | Not posted; also not the current two-player, fixed-role arena. | Low priority unless the challenge changes to teams/hidden identities. |
| L13–14 RLHF / alignment / DPO | No direct use. PPO's KL to an imitation reference is a distinct regularizer, not RLHF or DPO. | Do not import the labels. Preference learning could be useful only if we build reliable move-ranking comparisons from engine/referee outcomes. |
| L15 Forecasting and calibration | The model has move, danger, value and belief outputs; held-out replay audits measure prediction, but calibrated posterior/risk remains an explicit gap. | High priority when notes arrive. In the meantime, calibrate hidden-attacker/king-fatal probabilities on game-disjoint natural-frequency data. Report reliability, Brier/log loss and recall at a fixed false-positive rate. Do not treat raw network confidence or particle frequency as calibrated risk. |
| L16 High-dimensional/kernelized games | No kernelized MWU implementation. We do use compact board/action representations, particles, packed C structures and bounded candidate sets. | Research lead for compressing a distribution over strategy objects if an efficient payoff/kernel oracle exists. It is not an autoencoder/VQ-VAE recipe: the theorem depends on an efficiently computable kernel and specified multilinear utility. First target a compact move-pattern feature basis, then compare exact payoffs and exploitability. |
| L17 Nonconvex games | No explicit local-equilibrium or nonconvex-game solver. Neural training is nonconvex optimization, but that alone does not make it this lecture's game-theoretic method. | Wait for notes and a concrete need; not a near-term engine change. |
| L18 TFNP / total search | No direct use. | Complexity context for guaranteed search tasks and equilibrium computation, not an algorithm to add to the bot. The important engineering lesson is to distinguish a witness that exists from an efficient method that finds a useful one. |
| L19 PPAD hardness of Nash | No direct use; the posted note is unfinished. | Explains why generic exact equilibrium solving is not a credible whole-game plan. Use bounded approximations and exploit measurable structure rather than promising an exact solution. |
| S6 Markov/stochastic games | Simulator PPO models repeated state transitions; recurrent actor state is intended to capture history. | Relevant to the training formulation. The actor's observation history/belief is its information state; the privileged critic may see the true state, but that privileged input must not affect actor logits. Frozen-opponent identity/state may be needed for a Markov critic when opponents are history-dependent. |

## The bot's current multiagent stack, in one line

`public replays → imitation / move-model and frozen history priors → current-game belief update → sampled candidate-vs-world matrix + bounded search → regret-matched root choice`; separately, `simulator → league PPO research`. The second path is not yet connected to the deployed v35 choice procedure. The belief update estimates uncertainty; it is not itself online policy learning.

## What we have used versus what we should use

### Used, with important limits

- **Normal-form zero-sum reasoning:** a small regret-matched matrix for candidate moves against sampled worlds. This is a local robust approximation, not a full-game equilibrium.
- **CFR-inspired search:** bounded one-sided GT-CFR/PCFR+ in the clean-room `mist-c` lineage. The release documentation says KLUSS, Resolve/Maxmargin safeguards and cross-turn strategy carry-over are incomplete; exact parity with the paper or Brian Hu Zhang's engine is not established.
- **Repeated-play learning:** offline supervised replay fitting, static history lookup, and a separate recurrent PPO league trainer. Only the static prior/move model is in v35's move path; PPO is not.
- **Information-state approximation:** hidden-board particles and observation history. Exact consistency, posterior calibration and policy consistency across indistinguishable worlds remain the key questions.

### Should use next

1. **Audit the information sets before adding another model.** On a frozen set of sampled trees, construct the acting side's information-set key from its complete observation/action history and available legal actions. Assert that indistinguishable states have identical actor features and one shared action distribution. Add a counterfactual test where only the hidden true board changes; the selected policy must not change unless the observation/history changes. This directly probes strategy fusion.
2. **Measure CFR mechanics on a toy game and bounded Fog subgames.** Compare current root RM, current PCFR+, and an exact tiny extensive-form reference with matched leaves. Track exploitability/gap, information-set regret, average-policy value, node count, and runtime. Only scale the variant that passes the toy reference.
3. **Add an observation-transition value feature.** For a candidate move, simulate the opponent's actual next observation under each belief world; estimate whether the move reveals a threat, hides an attacker, scouts blockers, or changes the opponent's likely action. Feed resulting continuation value into current search. Avoid a generic bonus for hidden attacks or raw visibility area.
4. **Train against the deployed decision process.** If PPO is pursued, use its actor as a proposal/prior/value component in the same bounded candidate-and-matrix controller used at inference. Freeze the controller/opponent snapshots for valid behavior probabilities; compare against an identical training-budget control. Then evaluate game-disjoint tactics and real-clock paired games. No training run counts as progress until the resulting actor is packaged and demonstrably changes deployed decisions.
5. **Use bandits for experiment scheduling, not chess moves.** Allocate arena games to candidate × opponent-family × color strata with uncertainty-aware sampling and an exploration floor; keep a fixed holdout panel and sequential stopping rules. Game outcomes are delayed and opponents are nonstationary, so log assignment probabilities and avoid adaptive overclaiming.
6. **Make confidence useful.** Calibrate posterior mass for true hidden attackers and immediate king-capturable moves; stratify recent-hidden-arrival, low-particle-count and endgame states. Select risk thresholds against attack opportunity cost and false-positive rate. The course's calibration lecture is not posted yet, so this is a project need rather than a claim based on L15 notes.
7. **Explore compressed strategy representation only behind an oracle.** VQ/RVQ/DCAE could be an engineering choice for compressing recurring action-context patterns, but course L16's guarantee is about kernelized MWU with an efficiently computable strategy kernel/payoff structure. First establish whether our action-pattern kernel can approximate opponent response/payoff while preserving tactical tails. A latent code alone does not provide game-theoretic compression or strategic guarantees.

### Lower priority / not a current fit

- Full-game CFR, exact Nash solving, and a universal game-tree table are computationally unrealistic. Bounded information-set subgames and exact toy references are appropriate.
- Team/hidden-role, RLHF/DPO, and nonconvex-game algorithms are not immediate fits for this fixed-role two-player arena; revisit if the task or available data changes.
- L02/L18/L19 are valuable theory and complexity foundations, but not candidate code changes.

## Recommended experiment order

1. **Information-set correctness audit** on current bounded tree, including hidden-state invariance and perfect recall.
2. **Tiny exact reference comparison** for RM vs CFR/PCFR+ and counterfactual regret accounting.
3. **Posterior/risk calibration audit** on game-disjoint replays, with recent unseen attacker arrival as a required stratum.
4. **Observation-transition value ablation** inside the current selector, measuring both tactical wins and lost attacks.
5. **PPO-to-hybrid integration pilot** only after steps 1–4 define trustworthy labels and decision interface.
6. **Arena allocation bandit** after candidate variants exist; do not let the scheduler change the fixed evaluation panel.

This order targets the largest modeling mismatch first. It does not assume that CFR, deep RL, or a latent code is automatically stronger: each has a falsifiable gate.

## References

- [Official course schedule and Fog project framing](https://www.mit.edu/~6.7980/)
- [L01 Nash equilibrium](https://www.mit.edu/~6.7980/pdf/nfgs_nash.pdf)
- [L02 Brouwer and Sperner](https://www.mit.edu/~6.7980/pdf/brouwer.pdf)
- [L03 Properties of Nash equilibrium](https://www.mit.edu/~6.7980/correlated.html)
- [L04 Regret foundations](https://www.mit.edu/~6.7980/learning_intro.html)
- [L05 Regret algorithms](https://www.mit.edu/~6.7980/learning1.html)
- [L06 Bandit feedback](https://www.mit.edu/~6.7980/bandit.html)
- [L07 Extensive-form modeling](https://www.mit.edu/~6.7980/pdf/efg_intro.pdf)
- [L08 CFR](https://www.mit.edu/~6.7980/learning_efg.html)
- [L09 Multiagent deep RL (schedule; linked slides did not load in reader)](https://www.mit.edu/~6.7980/)
- [L11 Information and mechanism design slides](https://www.mit.edu/~6.7980/slides/L11_mechanism_design.pdf)
- [L16 High-dimensional games](https://www.mit.edu/~6.7980/kernelized.html)
- [L18 Total search and TFNP](https://www.mit.edu/~6.7980/tfnp.html)
- [L19 PPAD-hardness of Nash; work in progress](https://www.mit.edu/~6.7980/ppad_completeness.html)
- [Supplementary S6 Markov games](https://www.mit.edu/~6.7980/stochastic_games.html)
- [Current Astra architecture and known deployment gap](120-astra-obscuro-misty-rl-reality-check.md)
- [PPO league sampling experiment and limits](../astra-submissions/analysis/rl-league-groups-20261025/README.md)
