# The course and the bot: a mental model

*Current-state correction, November 11, 2026 UTC. Core course concepts mapped
to the shipped v38 source. The earlier October overview is preserved in the
local review evidence. Use the [presentation review](presentation-20261203.html)
for current deployment and experimental results.*

[TOC]

## The one-paragraph model

V38 maintains weighted possible boards, normally samples up to 32 root
worlds, and solves **one local extensive-form tree** with predictive CFR+.
Stockfish scores its frontier. Guards screen root king/queen risks. These
are implementations and approximations informed by the course; they are
not a full-game Nash certificate. Exp3 and deep RL are not additional layers
running in the deployed decision loop.

## Lecture by lecture

### Course overview (10 September)

The overview frames multiagent learning around incentives and interacting
policies, whose behavior can differ from isolated optimization. It lists
several approaches to FoW. Our deployed contribution combines inference,
local game solving, offline learned coefficients and engine engineering;
the historical neural-policy pipeline is a separate implementation.
[Lecture 0](https://www.mit.edu/~6.7980/slides/L00_course_intro.pdf).

### Nash equilibrium, zero-sum games, linear programming (15 to 22 September)

**Course.** L1 defines mixed equilibrium through unilateral deviations. L2
connects existence to Brouwer fixed points and Sperner's combinatorial
argument. L3 connects two-player zero-sum equilibrium to minimax and linear
programming, and distinguishes correlated equilibrium.
[Lecture 1](https://www.mit.edu/~6.7980/nfgs_nash.html),
[Lecture 2](https://www.mit.edu/~6.7980/brouwer.html).

**In the bot.** A zero-sum model motivates robustness to an adversary.
The earlier hybrid used a root matrix approximation; v38 uses a local game
tree. Solving either approximation does not establish optimal play in the
original FoW game. Earlier losses alone do not prove that one architectural
omission caused them. [Lecture 3](https://www.mit.edu/~6.7980/correlated.html).

**Limit.** The deployed engine forms no full-game LP or Sperner graph.
Existence of a mixed equilibrium does not prove that a particular finite
solver reaches it. The representation we solve is itself an approximation.

### Learning in games, foundations and algorithms (24 and 29 September)

**Course.** External regret; regret matching and regret matching+;
multiplicative weights; FTRL and online mirror descent; average-strategy
convergence in two-player zero-sum self-play; fictitious play as follow-the-leader.

**In the bot.** `cfr.c` clips accumulated regrets at zero and forms a strategy
from positive accumulated-plus-previous instantaneous regret. V38 uses the
last iterate and then takes its root argmax. The source still allocates and
updates averaging state even though that state does not select the move.
The [numerical walkthrough](presentation-move.html) checks actual updates;
the [experiment map](presentation-experiments.html) preserves the failed
playing gate for the faster last-only specialization.

For a fixed game, external regret compares the sequence of played strategies
with the best single strategy in hindsight. The zero-sum saddle gap of the
averaged realization plans is `(R1(T) + R2(T)) / T` in the lecture's canonical
setup. Here `T` counts solver iterations. In our runtime, those utilities
come from the constructed tree and its frontier values; they are not the
results of `T` arena games. Local regret updates do not refit the opponent
model.

**Limit.** The course's no-regret-to-Nash statement concerns average
strategies under its assumptions. It does not certify our finite last
iterate, growing frontier, root guards or argmax action. Arithmetic and
small-game checks are narrower evidence than full-game exploitability.
[Lecture 4](https://www.mit.edu/~6.7980/learning_intro.html),
[Lecture 5](https://www.mit.edu/~6.7980/learning1.html).

### Predictive learning and optimism (S4)

**Course.** Optimism uses the previous feedback as a prediction of the next.
S4 separates average, best-iterate and last-iterate results; their assumptions
and algorithms matter. The official source is now checked at
[commit f7c4d29](https://github.com/gabrfarina/MIT-6.7980-Topics-in-Multiagent-Learning/blob/f7c4d29fd95e5629c65e0d2c9d38f71867c8ed49/content/learning2.typ#L97).

**In the bot.** For local counterfactual utilities `u` and current strategy `x`:

```text
r(a) = u(a) − sum_b x(b)u(b)
R(a) = max(R(a) + r(a), 0)
last(a) = r(a)
next(a) is proportional to max(R(a) + last(a), 0)
```

`last` is a transient local regret vector. It is separate from the fitted
opponent-move predictor. With losses `ell = −u` and prediction equal to the
previous loss, the transformed prediction in Algorithm 5 of
[Farina, Kroer and Sandholm (2021)](https://www.mit.edu/~gfarina/2021/predictive-approachability-aaai21/predictive-approachability.aaai21.pdf#page=5)
equals this stored vector. An unchanged native-source fixture agrees with an
exact rational implementation on 39 scalar comparisons, including clipping.
Its final distribution is `(0, 12/31, 19/31)` on three invented actions.

**Limit.** This validates the local update, not a rate for the complete bot.
The paper's PCFR+ experiments use quadratic sequence-form averages. V38
keeps unused linear local sums and acts on its current root argmax. The known
whole-tree averaging issue is already recorded in note 140. Tree growth,
new-information-set initialization and approximate frontier values introduce
additional differences. No averaging switch or new playing gate follows.

Local evidence: `astra-submissions/analysis/course-optimism-source-20261111/`.

### Learning with bandit feedback (1 October)

**Course.** Bandit feedback reveals the played action's utility rather than
the full utility vector. Importance-weighted estimates support learning;
pseudoregret, expected regret and high-probability guarantees are distinct.
[Lecture 6](https://www.mit.edu/~6.7980/bandit.html).

**In the bot.** The fitted opponent model is supervised conditional-logit
learning from recorded actions. It is not Exp3 and uses no bandit
importance-weighted update. Arena trials involve partial counterfactual
feedback, but our fixed comparisons and fail-fast rules are experimental
designs, not an implementation of the lecture's algorithm.

**Limit.** GT-CFR's visit bonus is a search-allocation heuristic. A shared
exploration motivation does not make it Exp3.P or give it Exp3.P's bound.

### Modelling extensive-form games (6 October)

**Course.** Game trees; information sets partition each player's nodes by what they have observed; perfect recall; behavioural strategies, and by Kuhn's theorem their equivalence to mixed strategies under perfect recall; the sequence form, whose strategy polytope makes utilities linear.

**In the bot.** An information set groups indistinguishable histories, not
merely visible boards. V38 retains a capped projection onto complete current
positions with one representative opponent history per merged board. Its
search shares a strategy through history keys inside the constructed tree.
Those keys do not guarantee a lossless representation of the original
game's information sets or perfect recall after approximation.
[Lecture 7](https://www.mit.edu/~6.7980/efg_intro.html).

Perfect recall means remembering past observations and own actions. It does
not mean an enemy piece stays at its last seen square: hidden later moves
can increase current-board uncertainty despite that memory.

**Limit.** Our root range is our private retained belief, not a publicly
shared distribution. The course allows arbitrary fixed chance
probabilities; its uniform Kuhn-poker deal is an example, not a general
restriction. The [two-history illustration](presentation-knowledge.html)
shows why our unique board can coexist with an uncertain opponent. Its
legal alternative still needs justified policy reach before use in a solver.

### Learning in extensive-form games (8 October)

**Course.** CFR combines local regret minimizers using counterfactual
utilities. The lecture constructs the sequence-form strategy and recursive
utility feedback; its self-play construction targets a zero-sum equilibrium.

**In the bot.** `gtcfr_decide` alternates local regret updates with tree
expansion. Counterfactual traversal weights other-player/chance reach and
compares each action with the current mixture. This is a direct connection
to the lecture's decomposition into local regret minimizers. The
[real trace](presentation-move.html) and [worked toy](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/analysis/presentation-pcfr-20261111/README.md)
show the arithmetic. [Lecture 8](https://www.mit.edu/~6.7980/learning_efg.html).

**Limit.** Changing the frontier game and seeding new information sets on
their best child require separate analysis; the fixed-game regret theorem
does not automatically certify that process. Stockfish supplies
perfect-information heuristic utilities. Earlier hazard corrections did not
qualify as strength improvements and are not deployed corrections in v38.
Guards can cover some sampled-out danger but cannot guarantee survival.

### Multiagent deep RL (15 October)

**Course.** The posted slides distinguish neural best-response/regret
approximation, including NFSP, PSRO and Deep CFR, from policy-gradient
self-play. They discuss regularization and refining a policy with rollout
values at decision time. Their stated convergence result has tabular-policy
and exploration assumptions; it does not certify arbitrary neural PPO.
[Lecture 9, slides 4–8, 18–31](https://www.mit.edu/~6.7980/slides/L09_deep_rl.html?overview=1).

**In the bot.** The historical hybrid has CNN–GRU imitation/PPO code and a
batched C++ simulator. The retained trainer already contains a KL pull toward
the imitation reference, a training-only scalar true-board critic and GAE
over recorded trajectories (`learning/rl_train.py`, `learning/critic.py`).
A privileged critic or reference-policy penalty is therefore not a new
architecture for this project. These policy networks do not play in v38. The deployed
opponent model is a frozen conditional logit plus a count table; Stockfish's
borrowed NNUE is a different network. There is no deployed neural regret
approximator or self-play-trained FoW value replacing Stockfish.

**Limit.** “Learning” must name the process: offline parameter fitting,
within-game belief updating and within-decision regret updates are distinct.
The recent compact prior improved prediction and inference but lost its
playing pilot. That evidence does not support a universal conclusion about
when deep RL can work. See the [experiment map](presentation-experiments.html).

**Further reading.** Fan and Farina study action-sampling variance that can
remain even with an exact state-value critic. Their Q-boosting uses an
action-value critic and expected backups. That estimator is absent from our
retained GAE code; its relevance to our trainer is an unmeasured question.
[GAE Falls Short, v2, abstract and introduction](https://arxiv.org/html/2605.19235v2).

### Information and mechanism design (22 October)

**Course.** The lecture connects commitment, communication and incentive
constraints through strategies for a mediator. Its examples include
Stackelberg commitment, correlated recommendations and Bayesian persuasion.
[Lecture 11, slides 1–18 and 28–41](https://www.mit.edu/~6.7980/slides/L11_mechanism_design.pdf).

**In the bot.** A move changes the board and potentially the opponent's next
view. Concealed support can affect the opponent's choice. The arena's
visibility rules constrain this information; the bot cannot freely choose a
signaling scheme or enforce recommendations. The observed hidden-support
win illustrates visibility and tactics, not a solved persuasion mechanism.

**Limit.** V38 implements neither the lecture's mechanism-design LP nor its
mediator construction. The polynomial statement is relative to the supplied
game tree and model assumptions; it does not make a complete FoW tree small.

### Team games and hidden roles (27 October)

**Course.** Teammates' independent policies and privately correlated joint
strategies can define different optimization problems. The lecture uses
common-knowledge structure in a team-belief DAG and separately studies
unknown team membership.
[Lecture 12, slides 2–20 and 23–37](https://www.mit.edu/~6.7980/slides/L12_team_games.pdf).

**In the bot.** Each side's pieces have one controller, with fixed ownership.
There is no teammate-membership inference or team-belief DAG in v38.
Its retained board distribution is our private range. The representation's
history distinctions still matter: a memory approximation needs its own
justification before importing a perfect-recall result.

**Limit.** The lecture's team-specific construction and complexity bounds
are not measured costs or guarantees for our two-player GT-CFR search.
See the [two-history example](presentation-knowledge.html) for the actual
information-model limitation we can demonstrate in our bot.

### Human–AI agreement and delegated oversight (5 and 10 November)

**Course.** L13 studies prediction exchange, conversation calibration and
conditional benefits from competing information providers. L14 studies
unanimous authorization relative to a baseline under coalitional alignment.
These are different constructions with explicit incentive assumptions.
[L13 slides](https://www.mit.edu/~6.7980/slides/L13_alignment_I.pdf),
[L14 slides](https://www.mit.edu/~6.7980/slides/L14_alignment_II.pdf).

**In the bot.** Opponents supply moves and visibility, not cooperative
forecasts. V38 has neither conversation-calibrated prediction exchange nor
reviewers satisfying the oversight model. Our king/queen guards estimate
immediate risk over retained worlds; they do not compare exact baseline
continuation values under an alignment theorem.

**Limit.** Agreement between Fable and Astra is engineering review, not an
instance with the lecture's guarantees. Likewise, two guard conditions do
not establish baseline-policy improvement. These readings help specify what
a safety claim would require; they do not certify the current bot.

### Forecasting and calibration (3 November)

**Course.** Calibration compares outcomes within groups of similar forecasts.
The lecture develops multicalibration and a route to Φ-regret using additional
optimization primitives and private forecast sampling.
[Lecture 15, slides 2–10 and 16–24](https://www.mit.edu/~6.7980/slides/L15_calibration_gordon.html?overview=1).

**Implication for our measurements.** Truth log share and calibration answer
different questions. A risk check needs a stated event, prediction horizon,
decision-time inputs and sampling population. One unlikely event occurring
does not establish systematic miscalibration. The positive inference result
and rejected 1–8 playing pilot remain separate findings.

**Implementation boundary.** V38 does not implement this lecture's online
forecaster or forecasting-to-regret reduction. World sampling and the fitted
opponent prior do not supply those extra components or their guarantees.

### High-dimensional games and exact compact strategies (29 October)

**Course.** L16 represents distributions over combinatorial pure strategies
through their mean realization plans. Efficient kernels can reproduce vertex
multiplicative weights without enumerating every plan. For a finite
perfect-recall tree, shared backward/forward passes make the learner linear
in its sequence representation, beyond payoff-gradient cost.
[Lecture 16](https://www.mit.edu/~6.7980/kernelized.html).

**In the bot.** V38 uses local predictive regret matching. It does not
enumerate full contingent plans or implement the kernelized learner. For a
fixed represented tree, `pcfr_iteration` already makes two traversals plus
action-table passes: `O(N + E + A)` for nodes, edges and information-set
action slots, under ordinary scalar-operation accounting. Tree construction,
world filtering and frontier scoring are additional work.

**Limit.** The compact mean represents strategies, not the hidden-board
belief. Replacing the update would change the algorithm; this reading gives
no measured speed or strength gain. Earlier workspace and sparse-update
studies retain their failed promotion gates; the separate combined-speed
playing pilot also failed. Their evidence remains in the experiment register.

### Equilibrium existence and computational complexity (17 and 19 November)

**Course.** L18 separates polynomial verification from finding a guaranteed
solution, introducing total search and End-of-Line. L19 outlines circuit
gadgets behind general Nash hardness; its posted note explicitly remains
unfinished. Both notes were available ahead of their scheduled classes.
[Lecture 18](https://www.mit.edu/~6.7980/tfnp.html),
[Lecture 19](https://www.mit.edu/~6.7980/ppad_completeness.html).

**In the bot.** These are complexity explanations, not deployed algorithms.
General Nash hardness is not a lower bound on every two-player zero-sum
solver, nor an explanation of our particular arena losses. Finite-game
representation size, sampled information structure and frontier quality
still determine what our local calculation means.

**Limit.** Checking rules, regret arithmetic or a small-game best response
does not certify a full-game equilibrium. We have not reproduced the complete
hardness reductions, measured full-game exploitability, or proved that our
approximations preserve perfect recall.

## Where we stand, in the course's terms

| concept | course | bot | implementation limit |
| --- | --- | --- | --- |
| equilibrium notion | Nash, zero-sum minimax | approximate local-game optimization | no full-game exploitability certificate |
| learner | regret matching and variants | predictive CFR+; final last-iterate argmax | finite changing game and purification need qualification |
| information structure | histories, information sets, perfect recall | capped positions, representative histories, local history keys | opponent-compatible past alternatives and coupled re-solving absent |
| subtree values | counterfactual utilities in the represented game | Stockfish frontier and FoW terminal overrides | continuation quality is approximate; old hazard fixes did not qualify |
| partial feedback | bandit learning | supervised opponent fitting and experimental trials | no deployed Exp3/Exp3.P algorithm |
| deep RL | learned policies/values and multiagent training | historical PPO; borrowed NNUE; fitted inference prior | no deployed learned FoW search value or neural regret approximation |
| probability quality | calibration and multicalibration | posterior scores and model-weighted risk guards | calibration needs a stated event/population; no deployed forecasting-to-regret reduction |

## Later topics and possible connections

The [current course schedule](https://www.mit.edu/~6.7980/) also includes
information design, team/hidden-role games, alignment, calibration,
high-dimensional/nonconvex games and equilibrium complexity. These are not
all implemented bot modules. Calibration is relevant to judging inference
and risk estimates; information design motivates thinking about concealment.
Those conceptual connections do not make our agent a calibrated forecaster,
persuasion solver, kernel method or team-learning system.

The useful presentation claim is narrower: we implemented course-inspired
components, measured their behavior and found important limits in both the
represented game and its optimization. For the paper-specific missing
construction, read [Obscuro B.2/C.6](https://arxiv.org/html/2506.01242v2) and
our [two-history example](presentation-knowledge.html). It is not established
that all remaining losses lie outside the learner.

This correction checks the linked foundational notes and shipped source.
The follow-up reviews the textual content of L9 (48 slides), L11 (41 pages),
L12 (40 pages) and L15 (26 slides). A later pass adds L13 (67 pages), L14
(22 pages) and the complete posted HTML notes for L16, L18 and L19. Four
selected pages from L11/L12 and four from L13/L14 were also inspected as
images. Formal results and experiments were not independently reproduced.
The final foundational pass reads the overview's 51-page extracted text
and the full posted HTML main text for L01–L08. Two selected overview pages
were also inspected as images. Together, the dated reading records cover one
textual source for **all 18 currently posted lecture entries**. The official
schedule was checked again at 16:09 UTC on November 11: L10 (Taking stock)
and L17 (Nonconvex games) remain unposted. L19 labels its posted note unfinished.
The complexity notes are available ahead of their scheduled dates.

[Lecture-by-lecture coverage and source hashes](https://github.com/htansetiawan/iamavirus/blob/astra/presentation-review-20261111/astra-submissions/analysis/course-reading-followup-20261111/lecture-coverage.json)
distinguish reading from download and connect earlier dated records. This
is textual-source coverage, not a review of every graphic, lecture video,
supplementary reading, proof or future revision. The earlier incomplete
coverage statements remain dated historical records.
S4's HTML fetch failed in the earlier source audit; its full
official Typst source was checked at the pinned revision above. The PRM+
comparison uses the authors' original Algorithm 5 and unchanged `cfr.c`.
