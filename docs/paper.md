# Search without common knowledge on two cores: building, measuring and improving a Fog of War chess bot with two AI agents and a human

*Draft workshop paper for the 6.7980 project presentation (1 December 2026). Written on 16 October as a shadow of the final talk, to be revised as the numbers change. About four pages. Team IAmAVirus.*

[TOC]

## Abstract

We report on IAmAVirus, a Fog of War chess bot built over nine days of continuous arena play by two AI coding agents (Fable and Astra) and one human, through 35 arena versions and three engine families. The engine that plays today is **mist-c**, a 3,000-line clean-room C reimplementation of Obscuro's search without common knowledge, written from the paper for a sandbox of two cores and 4 GiB. Around it we built the parts a search engine does not come with: a daily pipeline that mirrors every arena game (119,000 so far) and rebuilds a move taxonomy, an opponent model and an empirical opponent prior fitted on that corpus, risk guards computed over the whole belief, a regression suite of 1,400 recorded decisions replayed through the exact bytes that lost them, a local arena, and a submission protocol with pre-registered predictions and a fail-fast revert rule. We present what moved the rating, what did not, and why; the arena's own dynamics (Elo with K of 8, proximity pairing, intransitive matchups); and the collaboration structure itself, a chat room of numbered notes and a core-reservation file through which two agents and a human shared one repository. Our conclusion is the course's thesis in reverse order: learning helped only inside a search that respects information sets, and the remaining gap is not in the learning dynamics but in the two inputs the theory takes as given, the weights on the information set and the value at the frontier.

## 1. The problem and the result

Fog of War chess is chess with hidden information: a player sees only the squares its pieces could move to, there is no check, and capturing the king wins. The course arena pairs bots continuously at 180 s + 2 s on two cores, offline, with a 15-second start-up limit. Between 7 and 16 October we uploaded 35 versions. The bot went from 1464 Elo (8th of 12) to a peak of 1922 (7th, above Instructors for one afternoon) and sits at about 1880, 8th, with the top six between 1930 and 2290. The rating moved in three steps, each a change of engine family (Table 1); within a family, changes measured as improvements on isolated decisions rarely moved the arena number, which is the central lesson of the paper.

**Table 1. Arena result by engine family.** Scores are schedule-adjusted against the v25 reference where available.

| family | versions | arena games | score | against the top six |
| --- | --- | --- | --- | --- |
| C++ belief and matrix-game engine | v1 to v4 | 262 | 0.41 | |
| neural hybrid (CNN-GRU imitation, regularised PPO) | v5 to v25, v27 | 556 at v25 | 0.48 | 0.26 |
| Misty (open-source Obscuro) | v28 to v30 | 464 | 0.47 | 0.22 |
| mist-c (ours), v9 | v33 | 663 | 0.49 | 0.26 |
| mist-c v12, with the sharpened belief and two-weighting king guard | v34 | 680 | 0.53 | 0.24 |
| mist-c v14, with the queen guard | v35 | 400+ | 0.54 | 0.27 |

## 2. mist-c: Obscuro in C for two cores

**Why a reimplementation.** Misty, the open implementation, is Python and Rust with Stockfish, and in the arena it forfeited three games on time and could not be changed where we needed it. We wrote mist-c from the Obscuro paper only, with Misty used solely as a local opponent, so that every part is ours to measure and modify, and so that the result is a small library others can build on.

**What it is.** Bitboard rules with Fog of War move generation verified against the course referee on 13,467 positions with no mismatch. An exact belief, the set of every full board consistent with our observations, updated incrementally with weights and kept under a cap of 200,000 by weighted sampling; on 40 recorded games the exact set overflowed a 100,000 cap in 24, so the weights decide what survives. A public game tree with each player's information sets keyed by their own observation history, solved by predictive regret matching+ with last-iterate play (unexploitable to 1e-5 on Kuhn poker by iteration 100), grown between solver rounds where the strategy and a visit bonus lead, about 310,000 nodes a move. Stockfish 19 at depth 1 scores the leaves on two worker processes in waves. A front end speaks the referee protocol, manages the clock, never sends a move the view forbids on some consistent board, rebuilds the belief from the view if the cap ever empties it, and avoids a third repetition when ahead.

**Costs, measured.** A Stockfish call is 0.3 to 1.8 ms; the belief update 0.27 s at the cap locally and about 0.5 s in the arena; the main thread once idled for 2.4 of every 2.5 s waiting on Stockfish, which pipelining and a second worker turned into search. The engine has not forfeited a game on time in 1,800 arena games. The code is at github.com/htansetiawan/mist-c.

## 3. Two agents and a human

The project was developed by two AI coding agents with different sessions and strengths, Fable (engine, evaluation, arena operations) and Astra (review, audits, the M4 subgame-solving branch, calibration studies), and a human lead who set direction, uploaded versions and arbitrated. The structure that made this work:

- **A chat room of numbered notes** in the repository (`chatroom/001` to `083`), each a dated, self-contained memo with its evidence and file paths, written by whichever agent did the work and read by the other at the start of its next session. Replies are notes too. A `ledger.jsonl` records every claim, and `INBOX.md` with a `msg_NNNN` channel lets the human write from a phone.
- **One version sequence.** Both agents' uploads share the arena's numbering; a zip is named for the version it will become, candidates are renamed at upload, and a number is never reused. `MUTATIONS.md` is the registry: parent, exact change, hash, prediction, fate.
- **A core-reservation file** (`chatroom/cores.json`): real-clock benches own a core pair exclusively, and an agent writes there before taking cores. Without it two agents' timing runs contaminated each other.
- **Predictions before games.** Every upload carries a prediction by opponent class written before the first arena game and a fail-fast rule for reverting. Broken predictions are recorded as broken, with the game that broke them.
- **Memory across sessions.** Each agent keeps a small file-based memory of facts not derivable from the repository (storage policy, the other agent's address, measurement pitfalls such as the belief's thinning being wall-clock dependent).

What we would share: the notes are the project's real record, better than the commit log; the hardest coordination failure was not disagreement but two agents editing the same engine source, solved by giving one agent the source and the other the review; and a human who reads every note and answers in a sentence was enough to steer.

## 4. Infrastructure: the logs and what we make of them

A systemd timer runs `tools/daily_refresh.sh` once a day, token-free: it pulls every arena game of every team (about 4,000 a day; 119,405 held), validates and quarantines, rebuilds the training manifests and the opponent-move export, regenerates the daily report, archives the day to an external disk, and commits the report. Nothing in the analysis pipeline runs through the agents on a schedule, after an early version woke an agent every 20 minutes.

**Representations we use.** (1) A **move taxonomy** of 19 tags per move computed from the true board and both views (capture from an unseen square, walk into an unseen attack, king threat from the fog, sacrifice, vision gain, king leaves home), reported per team per 100 moves. (2) **Event sequences** per game: the first queen event (lost outright, traded by whom), king-walk episodes, material swings. (3) **Decision-level traces**: for a replayed decision, the belief's size, the true board's weight and rank in it, each candidate's king and queen risk, the guard's verdict. (4) **Panels**: capability rates on a common opponent set, so teams are compared on the same schedule.

**Representations we have not tried and want to.** Time-indexed belief entropy per game (how fast each side's uncertainty collapses); an embedding of positions after our move labelled by what happened within four plies, to find loss clusters without hand tags; and opponent "fingerprints" from the first ten plies, which the hybrid era's logistic classifier (AUC 0.94) suggests exist.

## 5. Layers of heuristics

The equilibrium computation is exact only on the worlds it samples; rare hidden attackers are under-sampled by construction. Around the search we keep a small set of rules, each introduced for a measured loss class and each measurable on its own:

| layer | what it does | evidence |
| --- | --- | --- |
| king guard | removes root moves whose chance of leaving the king capturable, over the whole belief under two weightings, exceeds the safest by 2% | hidden-check blunders on the suite 73 to 59 of 399 |
| queen guard | the same rule for losing the queen for 4+ pawns net, folded into one risk with the king's (0.9 weight) | outright queen losses vs the top six 43% to 23% of games |
| fog hazard | lowers a leaf's value by the measured four-ply capture rate for the king's open lines into unseen squares, and more for a king move | king moves in the endgame 32 to 22 per 100 in self-play; arena effect pending |
| repetition rule | no third repetition when two points ahead | three draws seven points up, before it |
| clock | remaining/20 plus the increment, first decisions longest | no forfeit in 1,800 games |

The pattern across the layers: each one fixes the loss it was built for and the losses move to the next weakest point. The queen guard turned outright queen losses into queen trades that we still lose on material; the exposure term lowered king walking without winning more games against our own bytes. We take this as evidence against patching one piece at a time and for the fitted corrections of Section 7.

## 6. Opponent analysis

**The top six on a common panel.** Against the TA baselines, our behavioural rates now match the leaders: king threats 4.8 per 100 moves against their 4.1 to 5.3, queen raids 4.3 against 4.1 to 5.8, leads converted 80 of 82. The gap shows only head to head: our queen was lost outright in 43% of top-six games at v34, theirs in 10%, in 99 of 100 cases to a piece on an unseen square, usually the defender of what the queen took.

**The arena's own dynamics.** From 523 leaderboard snapshots and our 200-game rating history: the rating is Elo with K of 8.0 (residual 0.4 points), pairing favours rating proximity (7,279 games within 100 points, 1,308 within 500 to 600), and two new entrants drained about 460 points from the pool in three days. A 20-point gap is one day's noise. Our point flow is intransitive: in v35's 1,094 games we lost 73 points to Instructors and 54 to duck while gaining 47 from Mist and 36 from Knight Vision, and Instructors beats us 0.67 while level with Mist, whom we are level with. The leverage on rating is matchup-specific.

**Where the top six differ from us.** Our king moves 16.6 times per 100 moves against their 11.6, and 13.2 in the endgame against Greek Gift's 1.8. After our own move, a king with 0, 1, 2 or 3+ open lines into unseen squares is captured within four plies 1.8, 7.3, 17.3 and 36.1% of the time in the middlegame, and a king move itself multiplies those rates two to four times.

## 7. Learning from the growing logs

The improvement loop is: a loss in the arena, a decision in the regression suite, a hypothesis tested on the suite, a bench, an upload with a prediction, and a daily report that feeds the next loss. Two instruments made it work.

**The regression suite.** 1,379 recorded decisions from our losses, each replayed with the engine's exact inputs so it faces precisely the arena position, labelled by kind (hidden check, fatal move, material loss), with the true board's weight and rank in the belief tracked. Runs are compared decision by decision as fixed and broken; the noise floor is about five flips each way. Out-of-sample sets are built from the next version's losses before the change is made, which is how the queen guard was shown to cut queen-sized losses on 114 unseen decisions from 51 to 21.

**Fitted, not tuned.** Calibration decisions moved from hand-set margins to measured rates: the queen guard's margin from a sweep of its veto rate on losses against its veto rate on a control set (39 of 55 against 1%); the fog hazard from four-ply capture rates; the opponent prior from counts keyed by the opponent's information history. The next step, in progress, is a logistic model of king and material loss within four plies on all teams' games, replacing the hand tables.

## 8. The local arena

`learning.arena_local` runs paired games on the course referee between two zips at the arena time control, pinned to core pairs, both colours, seeded openings, with a watcher for forfeits and illegal moves and a log of clocks and replays. Opponents include our own earlier bytes, Misty, and behaviour-cloned replicas of each arena bot from the hybrid era. The validation script unpacks the exact zip, builds it with gcc and both compiler fallbacks, checks that Stockfish and the history table load, and plays the course baseline as both colours.

Its limits are the paper's most useful negative result: a bench against our own bytes did not predict arena results (v32 scored 0.55 against Misty locally and 0.14 against the top six), self-play cannot judge a change aimed at how a specific opponent punishes us, and the bench's double load thins the belief harder than the arena does because thinning is paid from measured wall-clock time. We now bench against Misty for search-level changes and read opponent-specific changes only in the arena.

## 9. Distillation: cheaper approximations and where they come from

Three sources of a cheap policy are on the table. **From the parent**: the hybrid era's 1.87M-parameter CNN-GRU, trained by imitation on arena games and by regularised PPO with an asymmetric critic and a league, played even with the search of its day; as a prior at 100 centipawns per nat inside the matrix game it helped. **From the teacher**: distilling mist-c's root policies and belief-weighted values into the same network as a root prior and information-set initialiser for GT-CFR, which is week 4 of the current plan. **From a decision model**: TypeSafe's Jev, hosted, or its open 9B students, tested in the same two slots, as the opponent-move likelihood for the belief and as the root prior, then distilled for the offline arena. The measurement is the same suite for all three, which is the point.

## 10. Reflection

Three things we would tell a team starting today. First, the method matters more than the model: the one change of method, from a matrix game to search over information sets, was worth 0.07 a game, and no network, book or heuristic matched it. Second, measure where the theory is silent: the losses that remain are in the belief's weights and the frontier's values, and every hand rule we added there moved a symptom. Third, the arena is a learning dynamic too: a K-of-8 Elo with proximity pairing rewards beating the two or three bots nearest you, and the daily rating is a poor instrument; a schedule-adjusted score with a pre-registered prediction is a better one, and writing the prediction before the first game kept us honest about what each version bought.

## References

B. H. Zhang and T. Sandholm. General search techniques without common knowledge for imperfect-information games, and application to superhuman Fog of War chess. ICLR 2026, arXiv:2506.01242. · M. Schmid et al. Player of Games. 2021. · B. H. Liou. Misty: an open implementation of Obscuro. 2026. · A. Wong, T. Bäck, A. V. Kononova, A. Plaat. Deep multiagent reinforcement learning: challenges and directions. 2021. · 6.7980 lecture notes, lectures 4 to 8, 2026.
