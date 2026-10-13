# Methods and algorithms

*Each method we have used, in the order the problem forced it on us: what it is, why we tried it, what it measured, and whether it is still in the bot. "Kept" means it is in the active version; "withdrawn" means it was tried in the arena or the bench and taken out; "null" means it was measured and made no difference.*

[TOC]

## 1. Rules and observation

**Exact legal moves from one observation** (C++ engine, `observation.*`; mist-c `src/board.c`). A Fog of War move is legal if it is legal on *some* board consistent with the view, so the engine derives the legal set from the observation alone and an illegal move is structurally impossible. Verified by a differential test against the course referee (47,875 of 47,875 checks for the C++ engine; 13,467 positions with 0 mismatches for mist-c). **Kept** in both engines; it is also why we have had one illegal-move forfeit in 34 versions, from a castling-rights bug in v7.

**Pawn visibility deductions** (v12). A pawn's forward square is seen only when empty, so an unseen forward square proves a piece is there; the belief treats this as a hard constraint. **Kept** in the hybrid; in mist-c it is implied by the exact enumeration.

## 2. Belief: where the opponent's pieces are

**Particle filter** (v2 to v27). 2,048 full boards, 8,192 from v17, propagated by sampling the opponent's hidden move from a prior, resampled systematically, rebuilt from a census when the filter collapses, with capture evidence and our own pieces as hard constraints (v3). Cheap and always available, but the true board is often absent: with the hand-set prior it stayed in the population on 2 of 20 seeds of a hard opening, with a learned prior 17 of 20. **Withdrawn** with the hybrid.

**Exact enumeration with a cap** (Misty, mist-c). The belief *P* is the set of every position consistent with the observation history, updated incrementally; past a cap (200,000 in mist-c; 500,000 in our Misty settings) it is thinned by weighted sampling. On 40 recorded arena games the exact set overflowed a 100,000 cap in 24 games, so the weights decide what survives. **Kept.**

**Opponent move model** (mist-c v4). Every hidden opponent move is scored by a conditional-logit model over move features, fitted on 2,029 arena games; on 371 held-out games it gains 0.63 nats per move over uniform with 27.7% top-1 accuracy. A world's weight is the product of its moves' likelihoods, so plausible histories dominate the sample the search sees. The truth's weight share is 2.6 times what uniform gives it, and it is inside a 64-world sample 60% of the time instead of 50%. **Kept.** A flatter model (temperature 0.5 and 0.7) and the model turned off were both worse on the regression suite: **null** or negative.

**Empirical history prior** (mist-c v10). A table keyed by a hash of the mover's own view-and-move history, counting what real arena opponents did from that information state, mixed into the move model. It fixed a family of early queen-check losses (the a5 and a4 checks after 1.d4) that the fitted model under-weighted. Pseudo-counts from 1 to 16 made no difference: **kept**, with the pseudo-count a **null**.

**Temperature** (mist-c v11). The move model's log-likelihood multiplied by 2 before weighting. Sharpening concentrates the sampled worlds (3 to 6 distinct worlds in a search instead of 25 to 28) and cut hidden-check blunders on the suite from 73 to 59 of 399, with the material kind unchanged (centipawn loss 137 against 145). The whole of that gain turned out to be the king guard's risk estimate under the sharpened weights, and the same sharpening drops a 3% check world below the guard's margin, which lost two 7-to-9-ply bench games. **Kept only together with the two-weighting guard** below.

**Network belief head** (hybrid v5 onward) and **king-only belief fusion** (v23). The CNN-GRU predicts a 7-class content for every square from the observation history; from v23 its enemy-king prediction reweights the particles. The head missed 88% of real dangers in review and the fused version scored 11-2-14. **Withdrawn** with the hybrid; the idea returns as "learned belief weighting" in the open problems.

## 3. Deciding the move

**Alpha-beta per particle with a root matrix game** (C++ engine, v2 to v27). Candidate rows (the policy's top 8, the alpha-beta shortlist's top 6, and the 8 lowest-king-risk moves, at most 12 in all) are scored against 8, later 16, sampled hypotheses by a depth-10 alpha-beta search with quiescence and a transposition table, about 11M nodes a second; the row-by-hypothesis matrix is solved by regret matching (4,000 iterations) and the move is sampled from the mixed strategy. Sound against a single guess but blind to information: the opponent's reply is assumed to see our board. **Withdrawn** with the hybrid.

**Risk charges** (v4 to v27). King-loss probability over all particles times 30,000; an exposure term; a two-ply material threat (weight 1.0) and a two-ply king threat (0.6, v13 and v14); a repetition charge (120); a "seen-gift" charge against taking bait (v17, times 3); a king-sighting bonus (300). Each one fixed a visible loss class and none moved the arena score outside noise. **Withdrawn** with the hybrid; their descendants are the king guard and the repetition rule.

**GT-CFR over information sets** (Misty; mist-c v3 onward). The Obscuro method: sample worlds from the belief, build a public game tree whose information sets are keyed by each player's own history, solve it with PCFR+ (predictive CFR+, last-iterate play), and grow the tree between solver rounds where the current strategy and a visit bonus lead. Because the opponent's strategy is computed over *its* information sets, the engine plays mixed strategies where it should and does not assume the opponent sees our board. The solver converges to the game value on Kuhn poker and its last iterate is unexploitable to 1e-5 by iteration 100. Local Misty beat our best hybrid 8-0. **Kept**; this is the core of v33 and v34.

**Stockfish leaves** (Misty; mist-c v7). Leaf positions are scored by Stockfish 19 at depth 1 with MultiPV, one call per expanded node, with our own material-and-shelter evaluator as the fallback. A call costs 0.3 to 1.8 ms. Capping MultiPV at 16 or 8 gave 2.1 to 2.65 times more expansions on an opening decision in tests and is an opt-in knob. **Kept.**

**Fewer worlds, better guarded** (mist-c v9). 32 sampled worlds instead of 128 to 256, so each world's subtree is deeper within the budget, and a **king guard**: root moves whose probability of leaving our king capturable, under the belief over all of *P* (strided to 20,000 boards), is more than 2% above the least-risk move are left out before the policy is purified. v33's 0.49 over 663 games against v32's 9 of 23. **Kept.**

**King guard under two weightings** (mist-c v12). The guard's risk is computed under both the sharpened weights the search uses and the fitted weights; a move excluded under either is excluded, and the sharper weighting is the fallback. Suite: fatal decisions 121 to 104 of 399 (hidden-check kind 73 to 59, 16 fixed and 2 broken); bench 23-1-16 against the v33 bytes and 16-1-3 against Misty. **Kept**; it is the one change that made the temperature safe.

**Stockfish on worker processes in waves, belief update on two threads** (mist-c v10). The main thread had been using 0.1 s of CPU in a 2.5 s search while waiting on the Stockfish pipe; two workers scored in waves and a two-thread belief update (2.3 s to 1.24 s at the cap) turned the second core into search. More search alone gave no fewer hidden-check blunders at 2.5 s, which is why calibration followed. **Kept.**

**Legality guard and belief rebuild** (mist-c v2, v3). No move is sent unless the view allows it on every consistent board; if the cap ever empties the belief, it is rebuilt from the view. Added after two illegal moves as Black when the capped belief had lost every position. **Kept.**

**Repetition rule** (mist-c v3; the hybrid's repetition charge). When ahead by two points or more, root moves that would place our pieces as they already have stood twice are left out. Three draws seven points up prompted it. **Kept**, but ten of v34's first 440 games were still repetition draws in long games, so the threshold is under review.

**Clock management.** The hybrid: budget = remaining over a divisor (30, then 20), capped at 4, then 7 s, a hard cap of 12 s (8 s in v27), a reserve of 6 to 10 s, and a node-capped fallback that scores each matrix cell with a one-ply search at the deadline. mist-c: remaining over 30 plus 1.6 s (v9), remaining over 20 (v11), and the belief update paid from the clock. The arena is about 1.9 times slower than our machines, which cost Misty three time forfeits; mist-c has none in 1,100 arena games. **Kept** (mist-c's); the divisor change alone was a **null** in games.

**Opening book and replay book** (v14, v15, v24, v25). A frequency-sampled book from the top six teams' first ten plies, gated by the king-safety filter after it carried a six-ply queen trap; then a replay book against Knight Vision, whose bot is a pure strategy (1,336 of 1,336 positions deterministic), which won 8 of 8 against it and 0 of 17 as Black against everyone else, and finally a safe replay that forces only the first move. **Withdrawn** with the hybrid; mist-c has no book.

## 4. Learning

**Observation encoding** (`learning/features.py`, mirrored in `neural_observation.cc` with a parity test). 32 planes of 8 by 8 plus 8 scalars in a canonical frame: the current one-hot observation, the last-seen content of every square, an ever-seen flag, the age of the information, our last move and en passant.

**Imitation (stage A)** (v5 to v17). `cnn64x4-gru256-heads-v1`: a convolutional stem, four residual blocks, a 256-unit GRU memory, and heads for value, per-square belief, and a candidate scorer giving policy and danger logits; 1.87M parameters, exported as two ONNX graphs (observe and score) and run in 0.14 ms per decision on the CPU. Trained on 1,500 to 4,700 games with per-team policy weights (the top teams at 4.0, ourselves at 0.5). A size sweep from 1.9M to 40.8M parameters on a 25,000-game dataset gave 34% top-1 at best. Behaviour-cloned replicas of each arena opponent (`releases/replica-*`) came from the same pipeline and are still used in the bench. **Withdrawn** as a player; **kept** as a tool.

**Regularised PPO in a batched C++ simulator (stage B)** (v18 to v22). A first recurrent PPO with GAE (gamma 1, lambda 0.95, clip 0.2) and a league of frozen checkpoints stalled at about 800 decisions a second in Python and never shipped. The second trainer runs in the batched C++ environment with PPO-clip plus a KL penalty toward the imitation policy (coefficient 0.05, the "magnet" of magnetic mirror descent and R-NaD), an entropy bonus, a training-only critic that sees the true board, and a league of the imitation reference, six opponent replicas and snapshots every five iterations. Checkpoints after 40, 120 and 240 iterations were uploaded. On its own the RL policy played even with v17; **as the matrix game's prior at 100 centipawns per nat** (v20) it scored 11-4-1 locally and raised the rating from 1586 to 1622. **Withdrawn** with the hybrid. The literature study behind it ("Keep the search, regularise the learner", in `reports/`) is the basis for the distillation direction.

**Opponent modelling.** A learned conditional-logit opponent prior (`opponent_model.*`) for the particle filter; a logistic opponent classifier over the first 20 plies (AUC 0.94 for TA bots against the rest, v24 era); "exploit cards" per top-six opponent from loss analysis; experimental SunTzu codes (vector-quantised windows of play). Only the classifier and the replay book reached the arena. **Withdrawn**; mist-c's history prior is the surviving form of opponent modelling.

## 5. Evaluation methods

The regression suite, the local bench and the schedule-adjusted arena checkpoint are described on [the measurement page](evaluation.html). Two methods there deserve a mention as methods in their own right:

- **Pre-registered predictions with fail-fast rules** for every arena version, written before the first game and checked at every 20-game checkpoint, which is how v11 was caught in the bench and how v24 was reverted within 44 games.
- **Decision-level diagnosis with the true board**: replaying a lost decision through the exact engine bytes while tracking the true board's weight share and rank in the belief, which is how the remaining hidden-check losses were traced to belief calibration rather than to search or the guard.

## 6. What each era bought

| step | evidence | kept? |
| --- | --- | --- |
| exact rules from the view | 0 illegal moves since v7 | yes |
| particle-filter belief + matrix game | 0.41 at v4 | no |
| imitation network as row proposer | 0.43 to 0.48 across v5 to v25 | no |
| RL policy as a prior, 100 cp/nat | 11-4-1 locally; +36 rating | no |
| replay book against a deterministic bot | 8 of 8 against it, 0 of 17 as Black elsewhere | no |
| Obscuro search (Misty) | 0.47; +0.12 a game over v25 | replaced by mist-c |
| mist-c with Stockfish leaves, 32 worlds, king guard | 0.49 over 663; no forfeits | yes |
| move model + history prior + temperature + two-weighting guard | 0.50; +0.025 over v33; Instructors 0.39, Mist 0.45 | yes |
