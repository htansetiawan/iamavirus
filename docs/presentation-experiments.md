# What we tried, what we learned, what remains open

*Evidence map for the [December 3 review](presentation-20261203.html),
updated November 11 UTC. This is a curated map of the main experimental
families, not a claim that 361 chatroom notes represent 361 independent tests.*

[TOC]

## Four questions, four kinds of evidence

| Question | Instrument | What passing establishes |
| --- | --- | --- |
| Does the code implement the intended rules or arithmetic? | Referee/C++ parity, compiler checks, source and array comparisons | Correctness within the checked scope |
| Does a model better predict recorded actions? | Trajectory-separated held-out or prospective action log loss | Predictive accuracy on that population |
| Do sequential beliefs represent reality better? | Replayed private histories, truth support and log share, collapse counts | Inference quality under those recorded histories |
| Does the complete bot play better? | Full-clock games, both colors, fixed binaries, qualified opponents | Playing evidence for that matchup and sample |

No row automatically implies the next. Counterfactual regret minimization
inside search and supervised prediction of opponents are also different
uses of the word “learning.”

## The architecture eras

| Era | What we implemented | Present status |
| --- | --- | --- |
| C++ inference/search | Fast rules, particles, per-world alpha-beta and a root regret-matched matrix game | Retired playing architecture; retained rules/reference tooling |
| Neural hybrid | CNN–GRU policy/danger/value/belief outputs, imitation and recurrent PPO experiments, hybrid candidate proposals | Historical training pipeline; not the policy in v38 |
| Misty adapter | Ran Brian Liou's independent open-source engine behind our protocol | Historical submissions and local benchmark opponent |
| Native mist-c | C weighted belief, history prior, growing-tree PCFR+, Stockfish frontier, guards | v38 playing architecture |

Misty, our mist-c and Zhang/Sandholm's original Obscuro are distinct systems.
Obscuro is the research method; installing Misty or implementing CFR does
not establish a complete reproduction of the original agent.

## Experiments grouped by the question they answered

The numbered links identify contemporaneous evidence. “Failed” closes the
tested configuration; it does not prove that an entire research area cannot work.

| Question and attempt | Observed outcome | What we learned |
| --- | --- | --- |
| Faster frontier scoring, deployed v38 | About 1.6× scoring throughput and 38% more equal-time nodes; 11W–1D–4L vs v37; Misty gate failed; human-authorized arena trial retained | A measured engineering contribution. Neither node gain nor retention alone identifies causal arena Elo gain. [Release](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/v38-release.md) |
| Cheaper exact CFR workspace/cached strategies/selective updates | 253/254 improve solver cost but old whole-search node gate fails | Local speed and whole-move speed differ. [254](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/254-astra-exact-selective-cfr.md) |
| Last-only solver specialization on v38 | Correctness and +10.6% equal-time nodes pass; full-clock comparison ends 9W–7L below 10/16 screen | A correct speed improvement can miss its playing criterion. [335](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/335-astra-fresh-last-only-playing-pilot.md) |
| Exact attack/visibility and deferred-prior speed | Whole-updater cost improves; full-clock combined build closes at 4W–7L by futility | Kernel speed is not a demonstrated strength result. [351](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/351-astra-deferred-prior-full-clock-pilot.md) |
| Cap estimators, finite-state resampling and dual measures | Multiple fixed variants fail support/collapse or truth-log criteria | Retention selection changes the represented distribution; corrections need sequential checks. [Register](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/RESEARCH_REGISTER.md) |
| Opponent style/history mixtures | Stationary three-expert adaptation improves conditional prediction only 0.0016 nats vs 0.05 target | This latent-style configuration lacked useful headroom. [206](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/206-astra-stationary-style-mixture.md) |
| Predict a limited-information opponent response | Projected response-policy pilot loses 2–6 | Restricting features alone did not repair the search information model. [211](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/211-astra-observable-response-projection.md) |
| Train the posterior directly | 231/232 improve log scores below their minimum-effect criteria | Choosing a theoretically appropriate target does not guarantee sufficient effect. [231](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/231-astra-posterior-vs-move-fit.md) |
| Root fatal-cell correction, full risk census and tactical strata | Specific support/coverage defects repaired, but selected fatal choices persist | Finding the danger is not the same as valuing the alternatives correctly. [285](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/285-astra-native-tactical-strata.md) |
| Stable mixed root actions | Restricted top-three pilot loses 1–3 | Negative evidence on that rule, not a refutation of game-theoretic mixing. [203](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/203-astra-stable-root-mixture-pilot.md) |
| Conditional-value/variance expansion | Pilot scores 7–9 vs 10/16 requirement | Paper-inspired expansion alone did not qualify a new engine. [234](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/234-astra-conditional-value-expansion.md) |
| 2-KLUSS, carry, Resolve/Maxmargin experimental M4 | Implemented components, continuation/decision failures and negative matches | This work exists outside deployment. A coherent supported subgame construction remains unresolved. [M4 evidence](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/m4-alternatives-20261011/README.md) |
| Native ancestry/private alternatives | Producer/parity checks pass; reference reach support 14.05% misses 20% criterion | Legal alternative boards require useful coupling and justified strategy reach. [292](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/292-astra-reference-reach-and-support.md) |
| FoW outcome value teacher/compression | Initial value result fails broader replication; query-value compression and MultiPV student fail their criteria | We do not have a qualified learned replacement for Stockfish. [238](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/238-astra-query-attention-value.md), [249](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/249-astra-amortized-multipv.md) |
| Quiet-move attention teacher | Numerical mismatch isolated/corrected; future 300-game prediction confirmation passes | Real action-prediction headroom. It is an opponent prior, not a policy or leaf value. [339](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/339-astra-corrected-teacher-confirmed.md) |
| Compact 46,650-parameter teacher/student study | Hard-label arm beats matched distillation; separate held-out prediction passes | Compact native inference is possible; teacher distillation was not the winning arm. [340](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/340-astra-compact-quiet-prior-distillation.md), [341](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/341-astra-compact-hard-label-holdout.md) |
| Compact prior with powered observation mass preserved | Independent posterior confirmation passes; full-clock engine loses 1–8 | Improved inference did not produce a qualified playing improvement. [355](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/355-astra-compact-mass-confirmation.md), [357](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/357-astra-confirmed-prior-playing-pilot.md) |

The complete navigation register contains older guard/hazard, opening,
endgame, arithmetic, data recovery and measurement work. Avoid presenting
this curated table as an exhaustive count of all experiments.

## Case study: a better posterior that lost more games

This is a stronger presentation story than a list of model architectures.

1. A compact quiet-move model passes independent action prediction.
2. Its unconstrained sequential use fails an Instructors nonregression check.
3. A distinct fixed implementation preserves powered observation mass while
   redistributing quiet-move weights. Separate confirmation on 63 later
   trajectories passes all 14 criteria, with truth-log gain **0.47277 nats**.
4. The complete engine then scores **1W–8L** against exact v38 at 180+2.
   The frozen ten-point target becomes unreachable, so seven games remain
   unstarted. All nine actual games remain in the record.
5. A frozen diagnosis of the first six completed paths finds **+0.61221 nats**
   pooled truth-log gain on 247 primary decisions. Four of five losing paths
   improve. Reconstructed/live population counts match; live weight
   fingerprints were not recorded.

Why is that possible? Average log share is not the same objective as choosing
winning actions. A model can improve many ordinary states while assigning
insufficient mass to decisive alternatives, or while inducing different
earlier actions. Search information modelling and frontier values can still
be wrong even with better beliefs.

One diagnostic loss has only **six retained worlds**, all included in search.
The king steps next to a hidden enemy king while nine material points ahead.
The real board remains represented, but the fatal step has only **0.0262%**
sharpened risk under the reconstructed learned weighting. This illustrates
weighting/decision limits rather than omission by a 32-draw sample. It does
not establish miscalibration from a single rare event.

Across the nine-game pilot, seven of eight losses had earlier sustained
material deficits; two final positions had no true safe reply. A story
focused only on the last king move would omit much of the failure.
[Independent game audit](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/compact-mass-playing-20261111/independent-audit.json)
· [Same-history diagnosis](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/360-astra-candidate-own-path-prior-diagnosis.md).

## Our contribution and the attribution boundary

We can explain and show our implementation, data pipeline, rules checks,
source-pinned tests, opponent analysis and measured scorer improvement.
The evidence also supports lessons about inference versus decisions,
component speed versus whole-game outcomes, and the hazards of testing on
selected losses or mismatched opponents.

We should not claim to have invented CFR or Obscuro, reproduced the full
Obscuro system, deployed a successful Deep CFR/self-play value learner,
measured full-game exploitability, or established a causal arena Elo gain
from the learned prior. Compression, SSL and Deep CFR are directions or
separate experiments; they are not implicit features of our deployed bot.

## Connection to the course

| Course idea | Concrete connection in our system |
| --- | --- |
| Zero-sum games and equilibria | The local two-player utility model and the reason predictability/mixing matter |
| Regret matching and optimistic learning | PCFR+ inside each decision; regrets and predictions have explicit array slots |
| Extensive-form games and information sets | Shared action distributions at indistinguishable represented histories |
| Imperfect-information subgame solving | Why a board sample alone does not reproduce the full common-knowledge problem |
| Forecasting and calibration | Distinguish likelihood, support, event calibration and decision utility |
| Multiagent deep RL | Historical PPO work and the gap between search-time learning and parameter learning |

The [course schedule and notes](https://www.mit.edu/~6.7980/) provide the
primary teaching references. Our [existing course map](course-map.html)
contains a longer conceptual treatment; deployment claims should use this
dated audit.

## The appendix we should be able to defend orally

- Draw the belief, search-world sample and continuation tree as three objects.
- State what every table key means and when each table is reset.
- Walk through one counterfactual regret update without calling it PPO.
- Explain one success and one failure using only information the actor had.
- State which observations are oracle diagnostics after the game.
- Identify the exact binary/version, population and metric behind each result.
- Name the omitted paper components and preserve their prior negative tests.
- Separate what we measured, what we infer and what remains unknown.
