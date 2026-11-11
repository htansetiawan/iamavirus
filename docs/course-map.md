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

### Nash equilibrium, zero-sum games, linear programming (15 to 22 September)

**Course.** Nash existence; in two-player zero-sum games the equilibrium value is a minimax and the strategies come from a linear programme; correlated equilibria.

**In the bot.** A zero-sum model motivates robustness to an adversary.
The earlier hybrid used a root matrix approximation; v38 uses a local game
tree. Solving either approximation does not establish optimal play in the
original FoW game. Earlier losses alone do not prove that one architectural
omission caused them. [Lecture 3](https://www.mit.edu/~6.7980/correlated.html).

**Beyond the course.** The LP is never formed; at arena scale the equilibrium is approximated by learning dynamics, which is the point of the next three lectures.

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

**Course.** The schedule lists modern multiagent deep reinforcement learning
for imperfect-information games. This review separates the project's
historical training code from the source actually deployed now; it does not
infer experimental outcomes from a lecture topic.

**In the bot.** The historical hybrid has CNN–GRU imitation/PPO code and a
batched C++ simulator. Those policy networks do not play in v38. The deployed
opponent model is a frozen conditional logit plus a count table; Stockfish's
borrowed NNUE is a different network. There is no deployed neural regret
approximator or self-play-trained FoW value replacing Stockfish.

**Limit.** “Learning” must name the process: offline parameter fitting,
within-game belief updating and within-decision regret updates are distinct.
The recent compact prior improved prediction and inference but lost its
playing pilot. That evidence does not support a universal conclusion about
when deep RL can work. See the [experiment map](presentation-experiments.html).

## Where we stand, in the course's terms

| concept | course | bot | gap we are working on |
| --- | --- | --- | --- |
| equilibrium notion | Nash, zero-sum minimax | approximate local-game optimization | no full-game exploitability certificate |
| learner | regret matching and variants | predictive CFR+; final last-iterate argmax | finite changing game and purification need qualification |
| information structure | histories, information sets, perfect recall | capped positions, representative histories, local history keys | opponent-compatible past alternatives and coupled re-solving absent |
| subtree values | counterfactual utilities in the represented game | Stockfish frontier and FoW terminal overrides | continuation quality is approximate; old hazard fixes did not qualify |
| partial feedback | bandit learning | supervised opponent fitting and experimental trials | no deployed Exp3/Exp3.P algorithm |
| deep RL | learned policies/values and multiagent training | historical PPO; borrowed NNUE; fitted inference prior | no deployed learned FoW search value or neural regret approximation |

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
It does not claim a fresh complete reading of every lecture or unpublished
slide deck. S4's HTML endpoint remains unavailable in this review; its full
official Typst source was checked at the pinned revision above. The PRM+
comparison uses the authors' original Algorithm 5 and unchanged `cfr.c`.
