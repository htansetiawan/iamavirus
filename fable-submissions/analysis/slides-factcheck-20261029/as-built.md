# IAmAVirus as built, mapped to 6.7980

Fact-check of the deck "How IAmAVirus Plays Chess in the Dark" (17 pages, exported 29 Oct 2026) against the code and the arena data. Written 29 October 2026; a Claude Doc copy exists under the same title. Numbers are as of 29 Oct 16:33 UTC unless stated.

## Summary

IAmAVirus plays arena version 35: mist-c, a clean-room C implementation of Obscuro's search (Zhang and Sandholm, ICLR 2026) with one addition the paper left open, a belief over hidden boards weighted by a fitted model of how arena opponents move. Every turn it holds the exact set of boards consistent with what it has seen (capped at 200,000), draws 32 of them by weight, runs predictive CFR over a public game tree with Stockfish scoring the leaves, removes root moves that expose the king or queen across the whole belief, and plays the last iterate. Nothing in the move selector is a neural network or reinforcement learning; the neural and PPO pipeline exists, was measured, and lost to search.

What is ours: the C engine itself, the weighted belief and its opponent model, the empirical history prior, the guards, the clock rule, and the measurement program around them. What is the field's: tracking every consistent board and solving for an equilibrium over them, which is the lecture definition of play on information sets and Obscuro's design.

On 29 October v35 sits ninth at about 1905 Elo after 11,880 arena games across all versions. The one measurement that matters now is the oracle of 28 October: the same search on the true board won 81 of 81 games against itself and against v35, so the remaining gap is the belief's weights, not the search. The work in progress is a sharper opponent model.

## What the engine does on every turn

One decision is five stages, and every constant below is read from the v35 source or measured on v35 games. Times are from v35's side of 20 local games at 180+2 on 29 October.

| Stage | What happens | The real numbers | Where |
| --- | --- | --- | --- |
| Observe | The referee sends a 64-character view (a1 to h8, `?` for fog) before every ply and a clock line on our turn. Legal moves are generated from the view alone, so an illegal move cannot be sent. | 13,467 recorded positions: 0 move-set, view or make/unmake mismatches against the course referee | `src/front.c`, `view_moves` in `src/belief.c`, `tests/test_rules.c` |
| Imagine | The belief P is the exact set of boards consistent with every observation so far, updated by expanding every opponent move on every board and keeping the matches. Past the cap it is thinned by weighted sampling without replacement. If it ever empties, it is rebuilt from the view. | cap 200,000 boards; at the decision the median |P| is 82 and the maximum hits the cap; the true board was never missing while the set was exact (60 v35 games, 5,228 plies) | `src/belief.c`, `MIST_CAP` in `src/main.c` |
| Weigh | Each board carries a log-weight: the sum over the opponent's hidden moves of a conditional logit's log-probability (28 hand features) at temperature 2.0, plus an empirical prior keyed by the opponent's information history when that history has been seen before. | fitted on 2,029 games (Oct 2026); top-1 27.7% on its original test set, 26.1% on a fresh 92,418-position set; the truth's share of the weight is 0.47% geometric mean on v35's own games, 1.9 times uniform | `src/movemodel.c`, `MIST_MODEL_TEMP`, `MIST_HISTORY_TABLE` |
| Search | 32 worlds are drawn from P by weight. A public game tree is grown across them (GT-CFR) with a predictive CFR+ regret minimiser at every information set of both players, keyed by each player's own history. Stockfish 19 at depth 1 scores the leaves on two worker processes. The root plays the last iterate. | 32 worlds; median 194,000 nodes and 1,890 iterations per decision locally (the docs' 310,000 is an arena-box figure); 4.1 to 8.5 s per move, median 6.0 s | `src/gtcfr.c`, `src/cfr.c`, `src/sfeval.c` |
| Guard | Root moves whose king-capture risk over the whole belief exceeds the safest move's by more than the margin are removed; the queen guard does the same for queen loss at its own margin. A material guard screens piece hangs. The repetition rule refuses a third repetition when two or more points ahead. | king margin 0.02, queen margin 0.05, strided over up to 20,000 boards; repeat lead 2 | `MIST_KING_GUARD`, `MIST_QUEEN_GUARD`, `MIST_REPEAT_LEAD` in `src/main.c` |
| Move | Budget = remaining clock / 20 + 0.8 x the 2 s increment, at least 0.3 s, at most 10 s and never over 30% of what is left. | 0 time losses in v35's 7,198 arena games; 7 across all 11,880 games of every version | `move_budget` in `src/main.c` |

The arena box is 2 physical cores (4 threads), 4 GiB, no network, 15 s to start, and each game is a fresh process: nothing is learned between games. v35's opponent model, history table and guards are all frozen at upload.

## What is ours and what is not

The design is Obscuro's; the weighting, the guards and the engineering are ours. Say so on the slide that states the big idea.

| Piece of the bot | Origin | Our part |
| --- | --- | --- |
| Track every board consistent with the observations; play a strategy over that set | The lecture definition of an information set; standard in Reconnaissance Blind Chess bots for years | None. It is the problem statement, not an invention |
| Exact belief update, sampled worlds, public tree with each player's private information sets, GT-CFR, Stockfish at the leaves | Obscuro, B. H. Zhang and T. Sandholm, arXiv 2506.01242, ICLR 2026 (via Player of Games for GT-CFR) | A from-scratch C implementation written from the paper only, with no code from Misty, the GPL implementation; enumeration cap, reservoir thinning, two-thread updates, clock accounting |
| Equilibrium move, not a worst case over boards | Obscuro's search computes an approximate Nash strategy over the 32 sampled worlds. The slide's "a move that's safe across all of them" describes minimax, which the bot does not do | Wording to fix |
| Weights on the belief from an opponent move model | The paper samples worlds uniformly and names a learned opponent model as future work | Ours: a conditional logit over 28 move features fitted on arena games, the temperature, and the history prior keyed by the opponent's information state |
| King guard, queen guard, material guard, repetition rule, belief rebuild | Not in the paper | Ours, each motivated by a class of recorded losses and measured on a regression suite of our own arena losses |
| The diagnostics: oracle belief, truth-share harness, sharpness curve, skill scorecard across teams | Not in the paper | Ours |
| The neural pipeline: imitation network, regularised PPO with a privileged critic, league of frozen opponents, native simulator | The course's deep RL unit and its survey | Ours, built and measured; not in the move selector |
| Misty as a local sparring partner | Brian Liou's public implementation of Obscuro | Used only as an opponent, never read for mist-c |

Two things the paper has that v35 does not: carrying the solved strategy between turns and re-solving against it (the 2-KLUSS and safety machinery), and the paper's scale of search. Both are listed in the architecture audit of 25 October as missing.

## The course map

The engine is lectures 5 to 8 run online under a two-core budget; the deep RL unit was tried and demoted to a supporting role. The lecture-by-lecture version with dates is `docs/course-map.md` (through 15 October); this table is the short form with the code locations.

| Course topic | Where it is in the bot | What we do differently from the lecture |
| --- | --- | --- |
| Two-player zero-sum games, Nash, minimax (15 to 22 Sep) | Each move is an approximate Nash strategy over the hidden state, not a best response to one guess. The hybrid era (v2 to v27) solved a matrix game at the root: our candidate moves against sampled boards | The LP is never formed; the equilibrium comes from learning dynamics |
| Regret matching, RM+, FTRL, average-iterate convergence (24 and 29 Sep) | Predictive CFR+ is the learner at every information set of the search tree (`src/cfr.c`); Kuhn poker test reaches the game value, last iterate unexploitable to 1e-5 by iteration 100 | We play the last iterate of the predictive variant after a few hundred to two thousand iterations, not the average; justified by measurement, not by the theorem |
| Bandit feedback, importance weighting, Exp3 (1 Oct) | The opponent move model is fitted from observed moves only (`src/movemodel.c`). The arena itself is a bandit: versions are arms, pairing is adaptive to rating, and the 20-game fail-fast rule with a pre-registered prediction is the confidence test (`docs/evaluation.md`) | The GT-CFR tree grows where a visit bonus leads, an exploration rule applied to search rather than play |
| Extensive-form games, information sets, perfect recall, Kuhn's theorem (6 Oct) | The belief P (`src/belief.c`) is our information set made explicit: every board consistent with the view and our history, with a weight each. Search information sets are keyed by each player's own observation history (`history_mix` in `src/gtcfr.c`). Strategies are behavioural, one distribution per information set | The exact set is capped at 200,000 and thinned by weighted sampling; the weights come from an opponent model where the lecture has uniform chance; the tree is built over the public history with private information sets hung off it (Obscuro's "search without common knowledge") |
| CFR on extensive-form games, counterfactual values, Theorem L8.2 (8 Oct) | `gtcfr_decide`: 32 worlds drawn by weight, a public tree grown between solver rounds, a regret minimiser per information set, counterfactual values up the tree, the root strategy purified and played | Three things the lecture does not cover: growing the tree (GT-CFR), a value at the frontier (Stockfish depth 1, a perfect-information bias), and guards outside the equilibrium for rare hidden attackers the sample under-represents |
| Multiagent deep RL: CTDE, opponent modelling, non-stationarity (15 Oct) | A 1.87M-parameter CNN with a GRU memory trained by imitation on arena games, then regularised PPO in a C++ simulator with a KL penalty toward the imitation policy (the magnet of MMD and R-NaD), a training-only critic that saw the true board (asymmetric actor-critic), and a league of frozen opponents (`learning/`) | The policy alone played even with the search engine of the time; as a prior inside the matrix game it helped; it never beat search. Imitation tops out near 35% top-1 on the top teams' moves, and a 4x larger network did not move it |
| Evaluation under noise: Elo as a learning dynamic, schedule effects | K is 8; a 20-point move is a day's noise; every 20 games we compute what a reference version would have scored against the same opponents; candidate benches are 40 to 120 games at full clocks, pairs colour-swapped, uncertainty at the pair level (`docs/evaluation.md`, Astra's note 177) | The arena's proximity pairing changes the opponents with our rating, so raw score and rating move for reasons other than strength (Astra's note 180) |

Where the open problems sit, in the course's terms: not in the learning dynamics but in the two inputs the lectures take as given, the weights on the information set (the belief) and the value at the frontier. The oracle of 28 October settled which of the two matters: with correct weights the existing search wins every game, so the belief is the whole remaining gap.

## What we measured and learned

The method since v26: every upload carries a written prediction and a pull rule registered before its first game, a fail-fast check at 20 games, and a schedule-adjusted comparison against a reference version every 20 games. Candidates are benched locally first at full 180+2 clocks against the previous bytes and against Misty, 40 to 120 games, with no forfeit, no crash and a lowest clock above 20 s as hard conditions. Most ideas failed their test, and the record says so.

| Measurement | Result | What it decided |
| --- | --- | --- |
| Hybrid era, v4 to v25 (7 to 11 Oct) | C++ belief plus a root matrix game scored 0.405 over 262 games; the neural hybrid 0.480 over 564 | Search that respects information sets beat the policy network; the hybrid line was closed |
| Misty as v30 (11 Oct) | 0.474 over 514 games | Obscuro's design is the right family; a public implementation is the floor to beat |
| mist-c v34 (13 Oct) then v35 (14 Oct onward) | 0.526 over 684 games; 0.520 over 7,198 | Our own implementation passed Misty and has held rank 9 to 10 since |
| Guards (king v33, queen and material v35 to v36) | Each fixed its class of short losses on the regression suite; worth at most about 30 Elo each in the arena; v36's piece guard scored 0.33 over 50 arena games and was withdrawn | Rule patches do not reach the next tier |
| More search time | 1 s to 6 s per decision on 487 suite decisions: fixed 12, broke 5 | Search time is not the lever |
| Imitation ceiling | A view-conditioned network predicts the top teams' moves at about 35% top-1, 64% top-4; a 4x larger network does not improve it | Imitation alone cannot be the route |
| Oracle belief (28 to 29 Oct, 81 games) | The v35 search on the true board: 41-0-0 against the identical control, 40-0-0 against v35, both colours, no forfeit | The search is already strong enough for the 80% target; the belief's weights are the whole gap |
| Truth share in the belief | On 60 v35 games the true board holds 0.47% of the weight (geometric mean), 1.9x uniform; a 64-world sample contains it 52.7% of the time. In the blunder audit it was present in 68 of 71 blunders at a median 0.06% | Coverage is fine, sharpness is the problem |
| Sharpness curve (running, 29 Oct) | The true board forced to exactly 5%, 20% or 50% of the belief's weight, 20 games each against v35, plus a lane that only records the natural share | Gives the weight the search needs to convert, which is the target for the opponent-model refit |

Two evaluation lessons cost us a week each. A local screen against v35 and Misty did not predict the arena: v36 passed its 104-game local gate and lost in the arena anyway, because the arena population differs from both sparring partners. And a 20-point rating move is one day's noise at K = 8: detecting a 15-Elo gain at two sigma needs about 2,100 games, a 100-Elo gain about 50.

## The slides, checked against the code and data

Of 34 factual claims in "How IAmAVirus Plays Chess in the Dark", 22 are right, 7 are wrong or misattributed, and 5 cannot be traced to anything in the repository. The wrong ones cluster on three slides: the big idea (slide 4), the referee-test and time-loss counts (slides 6 and 12), and the version history (slide 13).

| Slide | Claim | Verdict | What the code or data says |
| --- | --- | --- | --- |
| 2 | You see only the squares your pieces could move to; captures are noticed; no check; king capture wins | Right | `observation()` in the kit's referee: own pieces plus every legal move's destination |
| 3 | About 20 of the opponent's 30 moves are invisible | Right, old | A hybrid-era diagnostic in `belief_test.cc`; not re-measured on mist-c |
| 3 | Early test games all ended by king capture around move 10 | Roughly | The first mist-c arena version (v26) lost all five of its first losses to an unseen attacker; several arena losses came by ply 9 to 20 |
| 4 | Pick a move that is safe across all boards | Wrong | The search computes an equilibrium over 32 sampled worlds weighted by belief; nothing is guaranteed across every board, and the guards are the only worst-case element |
| 4 | That one idea is the whole bot | Misleading | It is the field's standard approach and Obscuro's design; what distinguishes the bot is the weighting and the guards |
| 5 | Five steps in 3 to 7 s | Nearly | Measured 4.1 to 8.5 s per move, median 6.0 s; the budget caps at 10 s |
| 6 | 47,875 of 47,875 referee tests agree | Misattributed | That figure is the hybrid-era C++ engine's conformance check. mist-c's own test is 13,467 positions with zero mismatches |
| 6 | 64-character view plus both clocks | Right | The view arrives before every ply; the clock line on our turn |
| 7 | Up to 200,000 boards; weighted random sample past the cap; the bot works out who took a piece | Right | `MIST_CAP` 200,000; weighted sampling without replacement; exact update |
| 8 | Model trained on 2,029 games, top-1 27.7% of about 30 moves | Right, dated | README figure; the source comment says 27.4%; on a fresh 92,418-position test set it is 26.1% |
| 8 | History table fixed a run of losses to one early queen attack | Right | The Qa5 losses after 1.d4; `MIST_HISTORY_TABLE` since v34 |
| 8 | weight = product of the opponent's move probabilities | Right | Log-weights summed per hidden move, at temperature 2.0; boards reached by several histories add their weights |
| 9 | 32 worlds, GT-CFR, 2 Stockfish helpers, Obscuro-based, own C version | Right | All in `src/main.c` and `src/gtcfr.c` |
| 9 | About 310,000 tree positions per move | Approximate | `docs/paper.md` figure from the arena box; measured locally median 194,000, 90th percentile 273,000 |
| 10 | CFR within 0.00001 of perfect play in 100 rounds on a toy poker game | Right | Kuhn poker, last iterate at iteration 100; the average strategy is at 0.00056 |
| 10 | Thousands of regret updates per move | Right | Median 1,890 iterations per decision |
| 11 | King guard margin 2% | Right | `MIST_KING_GUARD` default 0.02 over up to 20,000 boards |
| 11 | v35 guards the queen the same way | Right, different margin | `MIST_QUEEN_GUARD` default 0.05 |
| 11 | Five early losses had one cause; Greek Gift set the trap twice | Half | Note 037: v26's first five losses all ended with the king taken by an unseen piece. v26 never played Greek Gift; its losses were to Knight Vision, Decent, Mist and Instructors |
| 12 | Spend about 1/20 of the remaining clock | Right | Divisor 20 plus 0.8 x increment, floor 0.3 s, cap 10 s |
| 12 | Zero losses on time in 440 games | Wrong number, right fact | v35: zero time losses in 7,198 arena games; 7 across all versions. The 440 is a v34 repetition-draw count from `docs/methods.md` |
| 12 | No third repetition when 2+ points ahead; rebuild the belief if it empties | Right | `MIST_REPEAT_LEAD` 2; `belief_resample` |
| 12 | 2 cores, 4 GB, no internet, 15 s start | Right | Kit README: 2 physical cores / 4 threads, 4 GiB, 15 s initialisation, offline builds |
| 13 | v4 7 Oct C++ belief + matrix game, 0.41 | Right | 262 games, 0.405 |
| 13 | v25 10 Oct neural hybrid, 0.48 | Right | 564 games, 0.480 |
| 13 | v30 11 Oct Misty, 0.47 | Right | `iamavirus-v30-misty-4s.zip`, 514 games, 0.474 |
| 13 | v34 13 Oct mist-c, 0.50 | Wrong | 684 games, 0.526; the "262 to 663 games" range mixes in v33's 664 |
| 14 | 6 tricks, 19 knobs, none shown stronger | Untraceable | No such count in the repository; the hybrid-era README says its strategic heuristics were unproven |
| 14 | +33, -47, +51 Elo in a row, all noise | Untraceable | Only "+51" exists, as a 48-game local bench (v4 vs v3 of the C++ engine), not an arena swing |
| 14 | 11 vs 10 fatal choices with 4x thinking time on 80 positions | Untraceable | The recorded measurement is 1 s to 6 s on 487 suite decisions: fixed 12, broke 5 |
| 14 | About 2,100 games to detect +15 Elo, about 50 for +100 | Right arithmetic | Not written in the repo; two-sigma binomial counts come out at 2,140 and 51 |
| 15 | Standings 29 Oct: Greek Gift 2362, us 9th at 1890 | Right | Live board at 16:33 UTC: Greek Gift 2363, Knight Vision 2117, Strongly Invisible 2111, Decent 2102, Crimson Fog 2037, Instructors 2036, Mist 1979, duck 1953, IAmAVirus 1896 |
| 15 | Greek Gift last 24 h 202 W 12 D 168 L | Unverified | Not checked against the games feed |
| 15 | 176,785 games recorded | Right | Our accepted mirror on 29 Oct |
| 16 | Two agents and a human lead; numbered notes; prediction before upload, checked every 20 games | Right since v26 | `chatroom/`, `fable-submissions/README.md`, `docs/evaluation.md` |
| 16 | "We mutate, we learn from what kills us..." | Untraceable | No such text in the repository |

## Where it stands and what comes next

Rank 9 of the live board at 1896 Elo on 29 October, 16:33 UTC, with v35 active since 14 October. The tier above (Crimson Fog, Instructors, Mist Opportunities, duck, 1953 to 2037) is 60 to 140 points away; the tier of ranks 2 to 4 is about 220 points away, which is the 80%-against-v35 target the team set on 28 October. The v35 peak of 1992 on 29 October at 02:28 UTC and the fall back to about 1900 reconcile to completed games; HYPOTHERMIA, one of the two external references, moved to a much weaker v6 on 28 October, so the reference stays its v4 record.

The route is fixed by the oracle: belief work, not search work. In order:

1. Sharpness curve, running on cores 2 to 5 since 15:46 UTC: the weight the true board needs before the search converts.
2. Opponent move model refit with piece-square tables on 6,776 recent games (test set 1,224 games), pipeline built and validated in mist-c 2803b68; the fit runs when the cores free up. Success means a clear gain in held-out log-likelihood and a higher truth share on the 60-game trace set.
3. If both move, a v23 candidate goes to a direct screen against v35, then Astra's frozen 100-game confirmation (50 colour-swapped pairs, held-out seeds, pair-level uncertainty), then the arena.

After that the open items are the paper's own missing pieces, strategy carry-over between turns and the frontier value, and a per-world plausibility model applied only to the 32 sampled worlds.

## Sources

All paths are in `github.com/htansetiawan/iamavirus` unless marked mist-c (`github.com/htansetiawan/mist-c`, the engine as deployed is commit 97b60f1 = v35).

- Engine constants and stages: mist-c `src/main.c` (budget, caps, guards, repetition), `src/belief.c` and `belief.h`, `src/movemodel.c`, `src/gtcfr.c`, `src/cfr.c`; `tests/test_rules.c` on `tests/vectors.txt`; `tests/test_belief.c` on `tests/traces-v35.txt`
- Course mapping: `docs/course-map.md`; Astra's architecture audit `chatroom/120-astra-obscuro-misty-rl-reality-check.md`; `docs/review-current-state.md` (25 Oct)
- Version history and predictions: `fable-submissions/README.md` (the archive mapping); per-version scores computed from `data/raw/accepted.jsonl` on 29 Oct
- Evaluation method: `docs/evaluation.md`, `docs/methods.md`; the 80% target and the confirmation protocol, `chatroom/177-astra-v35-dominance-target.md`
- Oracle and sharpness curve: `fable-submissions/analysis/oracle-20261028/result.md`, notes 178, 179, 181; queue `data/arena_local/queue-oracle-share.json`
- Imitation ceiling and the hybrid era: chatroom notes 017, 020, 026, 118; `docs/top3-reanalysis-20261027.md` for the tiers and the blunder audit
- Rank swing and the HYPOTHERMIA version change: `chatroom/180-astra-rank-swing-and-hypothermia-version.md`
- Live standings: the arena leaderboard API, fetched 29 Oct 16:33 UTC
- The slides: "How IAmAVirus Plays Chess in the Dark", 17 pages, generated from a repository summary on 29 Oct
- Obscuro: B. H. Zhang and T. Sandholm, General search techniques without common knowledge for imperfect-information games, and application to superhuman Fog of War chess, arXiv 2506.01242 (ICLR 2026)

## Addendum, 30 October

Three things moved after this was written. The sharpness curve finished: with the true board forced to 5%, 20% or 50% of the belief's weight v35 scores 0.575, 0.800 and 1.000 against itself over 20 games each, against 0.325 for the natural weight (lanes run with the v20 piece guard on; with it off the control is 0.475 and the 20% lane 0.725). The piece-square refit (v23) scored 0.525 over the frozen 100-game confirmation, level with v35, so it is not a candidate. The live board on 30 Oct shows IAmAVirus seventh at about 1922.
