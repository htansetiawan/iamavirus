# The course and the bot: a mental model

*6.7980 up to 15 October 2026, mapped onto what IAmAVirus does. For each lecture: the concept, where it lives in the bot, and what we do differently. Written so a reader of the course can place the engine, and a reader of the engine can place the theory.*

[TOC]

## The one-paragraph model

The course builds one idea in layers: a player who minimises **regret** converges, in self-play, to an **equilibrium**; in games with hidden information the player's choices live on **information sets**, and **counterfactual regret minimisation (CFR)** runs a small regret minimiser at each of them; with partial feedback the same machinery works on **importance-weighted estimates** (Exp3); and modern practice scales it with **deep RL** and self-play. Our engine is that stack, run online, 32 times a move, on a game too large for the whole tree: a belief over the hidden board, a public game tree grown on the fly, PCFR+ regret matching at every information set, Stockfish as the value at the leaves, and guards that correct the one place the theory is silent, the value of an unseen attacker.

## Lecture by lecture

### Nash equilibrium, zero-sum games, linear programming (15 to 22 September)

**Course.** Nash existence; in two-player zero-sum games the equilibrium value is a minimax and the strategies come from a linear programme; correlated equilibria.

**In the bot.** Fog of War chess is two-player zero-sum, so the object we want at every move is a minimax strategy over the hidden state, not a best response to one guess. The hybrid era (v2 to v27) solved exactly that at the root as a **matrix game**: our candidate moves against sampled hypotheses of the hidden board, solved by regret matching. It was sound for one move and blind to the opponent's information, which is why it lost to the engines below.

**Beyond the course.** The LP is never formed; at arena scale the equilibrium is approximated by learning dynamics, which is the point of the next three lectures.

### Learning in games, foundations and algorithms (24 and 29 September)

**Course.** External regret; regret matching and regret matching+; multiplicative weights; FTRL and online mirror descent; the average of two no-regret learners' strategies converges to Nash (Theorem L4.9); fictitious play as follow-the-leader.

**In the bot.** **PCFR+ (predictive regret matching+)** is the local learner at every information set of the search tree (`src/cfr.c`). On Kuhn poker the implementation converges to the game value and its last iterate is unexploitable to 1e-5 by iteration 100. We play the **last iterate**, not the average: with a budget of a few hundred iterations per move, the predictive variant's last iterate is close enough and needs no averaging state. Regret matching+ was chosen for the reason the lecture gives, no hyperparameters.

**Beyond the course.** The lecture's convergence result is for the average iterate; our reliance on the last iterate of a predictive method is a practical choice backed by measurement on Kuhn poker and the arena, not by a theorem from the notes. The arena rating itself is Elo with K about 8, a learning dynamic in its own right; a 20-point gap is one day's noise.

### Learning with bandit feedback (1 October)

**Course.** Only the played action's payoff is observed; importance-weighted estimators keep the full-information analysis; Exp3 is multiplicative weights on those estimates, regret of order the square root of K T log K; Exp3.P adds exploration and a confidence bonus.

**In the bot.** Two places. First, the **opponent move model** is fitted from observed games only, where we see each opponent's chosen move but never the counterfactual ones: a conditional logit over move features, 0.63 nats per move over uniform. Second, **the arena is a bandit problem for us**: each version is an arm, each game a noisy pull against a scheduled opponent, and our 20-game fail-fast rule with a pre-registered prediction is a crude confidence test. The schedule is not adversarial in the lecture's sense but it is adaptive: pairing favours rating proximity, so the opponents we meet change with our rating.

**Beyond the course.** The GT-CFR tree expansion uses a visit bonus to decide where to grow, an exploration rule of the Exp3.P kind applied to search rather than to play.

### Modelling extensive-form games (6 October)

**Course.** Game trees; information sets partition each player's nodes by what they have observed; perfect recall; behavioural strategies, and by Kuhn's theorem their equivalence to mixed strategies under perfect recall; the sequence form, whose strategy polytope makes utilities linear.

**In the bot.** The arena protocol gives us exactly an information set: the 64-character view with `?` on unseen squares, plus our own history. The **belief** `P` (`src/belief.c`) is the information set made explicit, the set of every full board consistent with our observations, with a weight each. Information sets in the search tree are keyed by each player's own observation history (`history_mix` in `src/gtcfr.c`), which is the lecture's definition made computable. Our strategies are behavioural, one distribution per information set, as Kuhn's theorem licenses: both players have perfect recall in Fog of War chess as the arena states it.

**Beyond the course.** Two departures. The exact information set is too large to hold past a cap of 200,000 boards, so the belief is thinned by weighted sampling, and the weights come from a model of the opponent, which the course treats as uniform chance. And the paper our engine follows, Obscuro, builds the tree over the **public** history with each player's private information sets hung off it, the "search without common knowledge" idea, so that the opponent's strategy is computed over the opponent's information sets and not over ours.

### Learning in extensive-form games (8 October)

**Course.** CFR: a regret minimiser per decision point, trained on counterfactual utilities (the expected value of the subtree after each action), with total regret bounded by the sum of the positive local regrets (Theorem L8.2); the sequence-form strategy assembled top-down; two CFR learners in self-play learn a zero-sum equilibrium.

**In the bot.** This lecture is the engine. Each decision is a CFR run (`gtcfr_decide`): sample 32 worlds from the belief by weight, build the public tree, put a PCFR+ minimiser at every information set, iterate counterfactual values up the tree, purify the root strategy, and play. The regret bound's decomposition over decision points is why the tree can be grown incrementally: new information sets start with zero regret and the bound still holds. Leaves are scored by Stockfish at depth 1, which stands in for the subtree value the lecture computes exactly.

**Beyond the course.** Three things the lecture does not cover and the engine needs. **Growing the tree** (GT-CFR, from Player of Games via Obscuro): the tree is expanded between solver rounds where the current strategy and a visit bonus lead, about 310,000 nodes a move on two cores. **A value at the frontier**: Stockfish scores a leaf as if both sides saw the board, which is the one systematic bias we have measured, and the fog-hazard and king-move terms of v17 and v18 correct it with the arena's own four-ply capture rates. **Guards**: the king and queen guards remove root moves whose risk over the whole belief exceeds a margin, because the sampled worlds, by construction, under-represent rare hidden attackers; this is a safety layer outside the equilibrium computation, and the a5 and e-file losses show where it still fails.

### Multiagent deep RL (15 October)

**Course.** Deep RL methods for imperfect-information games; the posted reading is the survey *Deep Multiagent Reinforcement Learning: Challenges and Directions* (Wong, Bäck, Kononova, Plaat, 2021), which organises the field around centralised training with decentralised execution, opponent modelling, communication, coordination and reward shaping, and warns about non-stationarity and the curse of dimensionality.

**In the bot.** The hybrid era did this and measured it. A 1.87M-parameter convolutional network with a GRU memory was trained by imitation on arena games and then by **regularised PPO** in a batched C++ simulator with a KL penalty toward the imitation policy (the magnet of magnetic mirror descent and R-NaD), a training-only critic that saw the true board (the asymmetric actor-critic of the survey's CTDE family), and a league of frozen opponents against non-stationarity. The result the lecture would predict: the policy alone played even with the search engine of the time; as a prior inside the matrix game it helped; it never beat search. Opponent modelling survives in the current engine as the fitted move model and the empirical history prior, which the survey lists as one of its five directions.

**Beyond the course.** Our conclusion after the hybrid era is the course's own thesis in reverse order: learning is worth having only inside a search that respects information sets. The month plan's last step, distilling the search's root policies into the small network as a prior for the search, is the form of deep RL we still believe in for this game.

## Where we stand, in the course's terms

| concept | course | bot | gap we are working on |
| --- | --- | --- | --- |
| equilibrium notion | Nash, zero-sum minimax | approximate Nash per move over sampled worlds | sampling by weight under-represents rare attackers |
| learner | RM, RM+, MWU, FTRL | PCFR+ last iterate at each information set | none |
| information structure | information sets, perfect recall, Kuhn | exact belief with a cap; public tree with private infosets | the belief's weights (opponent model) decide what the search sees |
| subtree values | computed exactly | Stockfish depth 1 at the frontier | perfect-information bias; v17 and v18 correct it from data |
| partial feedback | Exp3 | fitted opponent model; arena as a bandit | per-opponent-class models, week 2 |
| deep RL | survey's five directions | tried as policy, prior and belief; kept as opponent model | search distillation, week 4 |

The honest placement: the engine is a faithful instance of lectures 5 to 8 run under a two-core budget, the deep RL lecture's methods were tried and demoted to a supporting role, and the open problems are not in the learning dynamics at all. They are in the two inputs the course takes as given, the weights on the information set and the value at the frontier.
