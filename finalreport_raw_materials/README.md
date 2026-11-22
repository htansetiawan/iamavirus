# IAmAVirus final report: raw materials

*Material for the team's final report. Compiled 22 November 2026 from the
repository, the arena record and the team's notes. The numbers marked
**refresh** change until the arena closes; see section 12.*

**Deadlines (from the instructors):** bot submission 11 December, 11:59 pm.
All project reports are due on Gradescope by Sunday 13 December, 11:59 pm, with
no extensions (grades are due 15 December).

**How to use this file.** The Google Doc explainer *IAmAVirus: Chess in the
Fog* (31 October) explains the game, the bot and its first 35 versions in
detail. This file covers the whole project to date, including everything after
31 October. It is laid out in the order the instructors grade:

- contributions;
- what we tried, why, and how it worked, with precise statistics;
- how the course shaped the bot;
- the AI statement.

Every claim points to a file in this repository. Quote the numbers from those
files, not from memory.

[TOC]

## 1. The project in one paragraph

IAmAVirus is our bot for the MIT 6.7980 Fog of War chess arena. Fog of War is
chess where you see only your own pieces and the squares they can move to. You
win by capturing the king, and there is no check. That makes it a two-player,
zero-sum game with imperfect information.

Over about two months we went through four engine designs and uploaded 38
arena versions. The final bot, v38, runs **mist-c**, our own from-scratch C
implementation of the published Obscuro method (Zhang & Sandholm, ICLR 2026).
On every move it does three things:

1. It keeps a weighted list of every board that could be true.
2. It samples 32 of those boards and solves one small game tree over them with
   counterfactual regret minimisation (predictive CFR+). Stockfish scores the
   positions at the tree's edge.
3. It throws out moves that put the king or queen at too much risk, measured
   over the whole list.

Our own contributions are:

- the opponent model that weights the boards, fitted on 148,357 arena games;
- the king and queen guards;
- the engineering that fits the method on the arena's 2 cores;
- a faster Stockfish scorer;
- a large, honestly recorded programme of experiments, most of which failed.

v38 has been live since 8 November. Over 2,588 games it has scored 0.55
(1,387 wins, 93 draws, 1,108 losses) with no time losses, crashes or illegal
moves. It stays above the course Instructors' bot and Mist Opportunities, the
other Obscuro-style bot in the arena.

## 2. Team and who did what

The instructors require each member's contribution. The agents' share below
is counted from the repository. **Each member should write and check their
own line.**

| Member | Role | Evidence |
|---|---|---|
| Henry Tan (human lead) | Set direction and the keep/withdraw rules; read the notes and decided what shipped; did every arena upload himself; chose to stop improving on 14 Nov and keep v38 | Decisions are quoted in `chatroom/` notes and `MUTATIONS.md` ("uploaded by the user", "withdrawn by the user") |
| Sophia | **[to fill in]** | |
| Fable (Claude Code, an AI agent) | Built and maintained the engine (the C++ engine, the neural hybrid's runtime, mist-c), the test and bench tools, packaging, arena tracking and analysis, the explainer and slides | 229 ledger entries; author of the `fable-submissions/` tree and most engine commits |
| Astra (Codex, an AI agent) | Review, audits, gate protocols, confirmation runs, most of the late research experiments (opponent models, belief corrections, the M4 prototype), the v38 faster scorer | 865 ledger entries; author of the `astra-submissions/` tree |

How the team worked (explainer, chapter 3, "Two agents and a person"; `chatroom/README.md`):

- **Channels.** The agents wrote to an append-only ledger
  (`chatroom/ledger.jsonl`). It holds 1,095 entries: 865 from Astra, 229 from
  Fable and 1 from the human. They also wrote numbered notes, 432 so far, where
  nobody edits another author's note.
- **Uploads and decisions.** The human read the notes and gave decisions. Only
  the human uploads.
- **Shared cores.** A core allocation file (`chatroom/cores.json`) stopped
  timing runs from interfering with each other.
- **Splitting the source.** The split of work changed several times. The worst
  coordination failure was two agents editing the same engine source. It was
  fixed on 26 October: one agent owns the source and the other owns review.
- **Size of the record.** Repository: 1,534 commits since 6 October. Engine
  repository (`htansetiawan/mist-c`): 73 commits since 9 October.

## 3. Timeline

The full record is in `docs/timeline.md` (versions 1 to 34, by date) and
`MUTATIONS.md` (every version: its parent, the exact change, the ZIP hash, the
prediction written before upload, and its fate). The course started on 10
September; the repository record begins on 6 October. **[To add: anything
before 6 October, such as the proposal or early experiments.]**

| Dates | Phase | Arena versions | Games, score | What it taught |
|---|---|---|---|---|
| 7 Oct | C++ engine: exact rules, sampled boards (particles), alpha-beta per board, root matrix game solved by regret matching | 2–4 | 276, 0.435 | Rules were right (47,875 of 47,875 checks against the referee). Losses were belief failures: the king was taken by pieces the belief didn't hold |
| 7–10 Oct | Neural hybrid: imitation network (1.87M parameters, CNN with GRU memory), then PPO self-play, inside the C++ engine | 5–25, 27 | 2,254, 0.457 | Imitation tops out near 35% of top teams' moves (a 40.8M model gained one point). The RL network helped only as a prior inside the matrix game |
| 10 Oct | Exploit: Knight Vision's bot is deterministic, so replay the moves that beat it | 24, 25 | v24 won 8 of 8 against Knight Vision but went 0 of 17 as Black against everyone else; v25 (safe version) 0.48 over 556 | Pure strategies are exploitable (the course's mixed-strategy lesson). A book keyed on our view fires against everyone |
| 11 Oct | Misty (Brian Liou's open-source Obscuro) behind our protocol adapter, as a yardstick | 28, 30 | 540, 0.475 | Solving for a strategy over information sets beats best-responding to sampled boards, with the same evaluator |
| 10–13 Oct | mist-c: our clean-room C Obscuro, then Stockfish at the leaves, 32 worlds, king guard (v33), history prior and sharpened weights (v34) | 26, 32–34 | v34: 220 of 440 (0.50), +0.09 a game over v25 (z 4.0) | Our own implementation matched and then passed Misty |
| 14 Oct | v35: queen guard (king risk + 0.9 × queen risk under the same 2-point margin) | 35 | about 7,800 games, 0.52 | The long-running baseline |
| 27–28 Oct | v36: piece guard | 36 | 48 games, 0.32 (z −2.88 against v35's expected score); withdrawn | It had passed a 104-game local test. **Local tests did not predict the arena** |
| 28–31 Oct | Oracle experiments: what limits the bot, belief or search? | local | see section 5c | The search is good enough; how boards are weighted is the gap |
| 1 Nov | v37: opponent model refitted on 148,357 games; history table 359,889 records | 37 | 2,322 games, 0.539 | More data gave a tiny prediction gain (+0.0077 nats) |
| 8 Nov | v38: Astra's modified Stockfish 19 scores all of a position's moves in one pass | 38 | 2,588 games, 0.554 (**refresh**) | 1.6× faster scoring, 38% more positions per move; better against teams at or above our level |
| 8–14 Nov | Late research on better opponent models, belief corrections and Obscuro components | local | see section 5 | Better guesses did not mean better play |
| 14 Nov | Henry stops improvements; v38 stays to the end. One curiosity build of the paper's opponent-knowledge search | local | 8–10 against v38 | Not stronger on two cores |

## 4. The final bot (v38) as built

The authoritative description is `docs/presentation-20261203.md`
("What actually plays" and "The lifetime of one move"). Explainer chapter 4
has the constants.

- **Package.** ZIP `astra-submissions/iamavirus-v38-mist-c-allchildren.zip`,
  SHA-256 `ba6610f299c1…`. It contains:
  - the mist-c C engine;
  - an offline-fitted opponent move model (28 features);
  - one history lookup table;
  - a modified Stockfish 19.

  No Fog of War neural network is deployed. Stockfish itself uses its own NNUE
  network.
- **One move:**
  1. Observe: read the 64-square view.
  2. Update the weighted boards: expand through possible opponent moves, keep
     the boards that match the view, merge duplicates. The cap is 200,000.
  3. Guards: king and queen risk over the whole list.
  4. Sample 32 worlds by weight.
  5. Grow one shared tree. Each player's decisions are grouped by what that
     player has seen.
  6. Stockfish scores the frontier at depth 1, one pass over all of a
     position's moves.
  7. Run predictive CFR+ (about 1,900 iterations per move in v35).
  8. Play the highest-probability move the guards allow.
  9. Keep the belief and throw the tree away.
- **Clock.** About 1/20 of the remaining clock plus most of the increment,
  never over 10 s. That is about 4 to 8 s per move (median 6) at full clock.
- **Rules safety.**
  - Legal moves come from the view alone. They were checked against the
    course referee on 13,467 positions with zero mismatches.
  - No third repetition when 2+ points ahead.
  - If the belief empties, it is rebuilt from the view.

**Deployed or not** (from `docs/presentation-20261203.md`; this keeps the
claims honest):

| Component | v38 status |
|---|---|
| Rules, observations, weighted boards | Deployed |
| Growing-tree PCFR+ search | Deployed (solves an approximate local game) |
| Stockfish depth-1 frontier scoring (faster all-moves version) | Deployed |
| Fitted opponent model and history table | Deployed, frozen offline; no learning during games |
| King and queen guards | Deployed |
| Carrying the search from one move to the next | **Not deployed** (tested in M4) |
| The paper's full opponent-knowledge subgame (2-KLUSS with Resolve/Maxmargin) | **Not deployed** (tested; see 5f) |
| A learned Fog of War value or policy replacing Stockfish | **Not deployed** (historical hybrid; later experiments failed their criteria) |
| The paper's mixed move choice | **Not deployed** (tested and rejected; we play the top move) |

Differences from the Obscuro paper, as measured by Astra
(`astra-submissions/obscuro-comparison-20261108.md`):

- The paper samples boards uniformly; we use a fitted opponent model.
- The paper uses Stockfish 14; we use 19.
- The paper ran on 5 cores, with board enumeration off the clock; the arena
  gives us 2 cores and counts everything.
- We add the guards.

## 5. What we tried, why, and how it worked

The curated list with links is `docs/presentation-experiments.md`. The full
register is `astra-submissions/RESEARCH_REGISTER.md`. Each experiment result
is in `fable-submissions/analysis/<name>/result.md` or in a numbered note.
"Failed" means that configuration failed its pre-set test, not that the idea
can never work.

### 5a. Engine designs (the big pivots)

**Why we moved on each time.** The C++ engine lost to hidden pieces. The
neural hybrid's ceiling was also the belief: against the top five teams it
failed to escape a hidden check 32% of the time. Misty showed that the
Obscuro way of solving beats ours. So we wrote our own version, small enough
for 2 cores.

| Design | Versions | Score (mean of 262 to 684 games each) |
|---|---|---|
| C++ engine | v4 | 0.41 |
| Neural hybrid | v25 | 0.48 |
| Misty | v30 | 0.47 |
| mist-c | v34 | 0.53 |

### 5b. Safety guards

- **King guard (v33).** Leave out any move with more than 2 percentage points
  more king risk than the safest move, measured over the whole list. This
  fixed the most common loss: all five early mist-c losses were the king
  walking into a hidden attacker.
- **Queen guard (v35).** Our queen was lost outright in 43% of v34's games
  against the top six, against 10% for them.
- **Piece guard (v36).** Arena failure (above).
- **Many other guard and hazard variants:** `fable-submissions/analysis/`
  guard-grid, guard-candidates, hazard-calib and attack-reweight.
- **Lesson:** guard rules gave at most about 30 Elo each.

### 5c. What limits the bot: the oracle experiments (28–30 Oct)

Files: `fable-submissions/analysis/oracle-20261028/`, `oracle-share-20261029/`
and `v35base-20261029/`.

- **The true board.** A test-only build was told the true board before each
  move and won **81 of 81** games, against v35 and a copy of itself. So the
  search is good enough when the board is known.
- **Forcing the true board's share of the weight:**
  - at 5%: 0.575;
  - at 20%: 0.80, or 0.725 with the piece guard off;
  - at 50%: 1.00, all against v35.
- **In normal play** the true board gets a median share of only about 1%. In
  68 of 71 blunders the true board was in the list, at a median share of 0.06%.
- **Conclusion:** weighting, not coverage, is the gap.
- **An earlier oracle on the neural hybrid (8 Oct)** said the same thing: given
  the true board, it found hidden king threats 80% of the time against 41%,
  while 8× the compute changed nothing.

### 5d. Better opponent models (the weighting gap)

- **v37 refit.** 73× more data (2,029 → 148,357 games), same 28 features:
  - held-out gain of +0.0077 nats, with top-1 prediction going from 26.7% to
    27.1%;
  - a 100-game duel against v35 scored 57% (paired interval 47–68%), so not
    decisive.
- **Style mixtures, posterior-trained models, restricted-feature response
  models:** each below its pre-set minimum effect, or lost its pilot (for
  example 2–6).
- **Compact quiet-move model.** It passed independent prediction and
  confirmation: +0.47 nats truth-log gain on 63 later games, all 14 criteria
  met. **Then it lost 1–8 to v38 at full clock.** Better average guesses did
  not mean better moves. This is our best "surprising result" story
  (`docs/presentation-experiments.md`, "a better posterior that lost more
  games").

### 5e. Speed

- **v38 scorer.** 1.57–1.68× scoring throughput, 38% more search nodes at
  equal time, the same immediate king-loss cases. Local result against v37:
  11W–1D–4L. It failed its local gate against Misty, and Henry approved an
  arena trial anyway.
- **Other speed-ups.** Solver specialisation (+10.6% nodes) and faster attack
  and visibility code passed their correctness checks but lost their
  full-clock pilots (9–7 short of 10/16; 4–7). A faster component did not
  always make a stronger bot.
- **More thinking time.** 4× the time gave 11 fatal choices against 10 on 80
  test positions, so more search alone does not help.

### 5f. Parts of the Obscuro paper we tested and left out

- **Mixing among the top three moves:** lost 1–3.
- **Exploration by conditional value and variance:** 7–9, short of the
  required 10/16.
- **Opponent-knowledge subgame (2-KLUSS, Resolve/Maxmargin, tree carried
  between moves).** Astra built the M4 prototype; Fable put it behind v38's
  guards on 14 Nov.
  - Result: **8–10 against v38 in 18 local games** (0.444, z −0.47).
  - Mechanically clean: no crash, forfeit or illegal move in 484 logged
    decisions.
  - Weaknesses: it used only 75% of its time budget and one Stockfish process.
  - Files: `fable-submissions/analysis/kluss-m4-20261114/result.md` and
    `docs/m4-review-20261112.md`.
- **Source-level gap list:** `chatroom/358-astra-current-obscuro-gaps.md`.

### 5g. Learning from the arena (data pipeline)

- **Daily refresh.** Downloads every replay (ours and all teams'), rebuilds
  the training data and a move taxonomy, and writes a daily report
  (`docs/arena-intelligence-loop.md`; the archive passed 186,000 games).
- **Analyses:** a skill rubric against all teams
  (`docs/skill-rubric-20261028.md`) and an arena tier analysis
  (`docs/top3-reanalysis-20261027.md`).
- **The material loss pattern.** In 121 of 144 v38 losses, we were behind by 3+
  points for 5 recorded frames, at a median ply of 51, 29 plies before the end.
  This is mostly to captures from hidden squares.

### 5h. Measurement practice (worth its own section; graders asked for precise statistics)

- **Predictions before upload.** Every arena version had a written prediction
  and withdrawal rule before its first game, checked every 20 games
  (`MUTATIONS.md`, `fable-submissions/README.md`). Broken predictions are
  recorded with the game that broke them.
- **v38's rules, fixed in note 267 before upload:**
  - withdraw at once on any time forfeit, crash or illegal move;
  - at 48 games, withdraw if z ≤ −2 against v37's expected score;
  - at 300 games, keep only if the score is at least 0.543.

  v38 passed: 318 games, 0.582, z +1.38.
- **Sample sizes.** About 2,100 games are needed to detect a +15 Elo change,
  and about 50 for +100. Three versions in a row moved the rating +33, −47
  and +51, all within noise.
- **Proxy failures:**
  - Replicas are not faithful: 0.77 against the duck replica, 0.23 against the
    real duck.
  - Local gates against our own bytes misled: one network lost 1-4-5 locally,
    then went 16-5-3 in the arena; v36 passed locally and failed in the arena.

## 6. Arena results

The v38 trial is in `fable-submissions/analysis/v38-arena-20261108/result.md`.
A reading is taken automatically every 3 days. The readings so far are copied
into `data/v38-readings.jsonl` next to this file, one JSON line per reading,
with our record, the top 12 and v38's record by opponent. Fable adds later
readings to that file.

**Records** (score = wins + half the draws, per game):

| Version | Games | W–D–L | Score |
|---|---|---|---|
| v35 | about 7,800 | — | 0.52 |
| v37 | 2,322 | 1219–65–1038 | 0.539 |
| v38 (21 Nov, **refresh**) | 2,588 | 1387–93–1108 | 0.554 |

v38 by colour (to 20 Nov): White 0.61, Black 0.50. v37 was 0.58 and 0.49.

**Head-to-head, v37 then v38** (games to 20 Nov). This is the clearest
evidence that v38 is better where rank is decided:

| Opponent | v37 | v38 |
|---|---|---|
| Mist Opportunities (other Obscuro bot) | 0.48 (126) | 0.71 (100) |
| Instructors | 0.40 (132) | 0.52 (97) |
| Knight Vision | 0.30 (82) | 0.41 (94) |
| Crimson Fog | 0.18 (98) | 0.38 (86) |
| Greek Gift (leader) | 0.03 (90) | 0.08 (62) |
| HYPOTHERMIA | 0.46 (120) | 0.48 (104) |
| Strongly Invisible | 0.22 (108) | 0.26 (96) |
| duck | 0.35 (130) | 0.27 (108) |
| Farsight | 0.43 (138) | 0.32 (84) |

**Time above our neighbours** (rating history sampled every 15 min,
1–14 Nov). The v38 figures cover 8–14 Nov:

| | v37 | v38 |
|---|---|---|
| Time above the Instructors bot | 14% | 82% |
| Time above Mist Opportunities | 5% | 82% |
| Median rank | 11 | 9 |

**Standing on 21 Nov (refresh).** We were 17th of 63 teams at 1834, above
Instructors (19th, 1818) and Mist Opportunities (21st, 1809). The top three
were Greek Gift (2203), Knight Vision (2078) and Farsight (2029).

**Caveats for the report:**

- **Ratings deflated in November.** New teams entered and nearly every
  established team's rating fell: Strongly Invisible from 2062 to about 1940,
  Decent Chess Bot from 2089 to about 1950. Our rank number fell from 9 to 17
  for the same reason.
- **Use head-to-head, not rating buckets.** Elo K is about 8, so 20 points a
  day is noise. Split by
  opponent strength, v37 against v38 looked clearly better on 14 Nov (teams
  rated 2000+: 0.27 → 0.34). Split by *today's* ratings, it is level (0.28 →
  0.29), because which teams count as "2000+" has changed.
- **This is an observational comparison.** Opponents changed versions and
  scheduling is not random.

## 7. How the course shaped the bot

Long version: `docs/course-map.md`, lecture by lecture, corrected 11 Nov.
Short version: `docs/presentation-experiments.md`, "Connection to the course".
Explainer chapter 3 has the lectures 11–12 discussion.

| Course topic | Where it is in our bot |
|---|---|
| Nash equilibrium, zero-sum games | Fog of War is two-player zero-sum; the root matrix game (C++ engine) and the local game (mist-c) are solved for an equilibrium-style strategy, not a best response to one guessed board |
| Learning in games, regret matching, optimistic/predictive learning | Predictive CFR+ at every decision point of the tree; regret matching at the root of the C++ engine |
| Extensive-form games, information sets | The tree groups each player's decisions by what that player has seen; the belief is the set of histories consistent with our view |
| Learning in extensive-form games (CFR) | Growing-tree CFR inside each move; Kuhn poker test (within 0.00001 of the known equilibrium in 100 iterations) |
| Imperfect-information subgame solving | Why a board sample alone is not the full problem; the paper's 2-KLUSS and gadgets, which we tested (M4) |
| Mixed strategies and exploitability | Exploited Knight Vision's deterministic bot with a replay book; tested the paper's move mixing |
| Multiagent deep RL (PPO, self-play, R-NaD-style regularisation) | The neural hybrid: imitation network, PPO against a league of frozen replicas with a pull toward the imitation policy, a critic that saw the true board |
| Forecasting and calibration | Opponent model scored by held-out log loss; the lesson that better calibration (log score) did not give better play |
| Team games and hidden roles (lecture 12) | The team itself: a shared ledger as the public channel, gates agreed before a candidate exists, a lead as mediator |

## 8. Limitations and open questions

From `docs/presentation-20261203.md`, "Limits", and `docs/open-problems.md`:

- **Support.** The 200,000 cap can drop the real board, and the 32-world
  sample can miss a danger that is still in the list. These are different
  failures.
- **Weighting.** The real board is usually in the list but badly weighted
  (median share about 1%). Nothing we built closed that gap in play.
- **Information modelling.** We don't model what the opponent knows about us
  the way the paper does.
- **Evaluation.** Stockfish judges each complete board as ordinary chess. It
  does not value hiding information or bluffing.
- **No guarantee.** Finite search, guards and playing the top move mean no
  Nash guarantee for the full game.
- **Measurement.** The arena is not a controlled experiment.

## 9. Material for the AI statement

The instructors want detail: exactly what AI did and what humans did. Facts
from the record:

- **AI agents wrote almost all code and ran almost all experiments.**
  - Fable (Claude Code) wrote the C++ engine, the neural pipeline runtime,
    mist-c, the tools and the benches.
  - Astra (Codex) wrote the review and audit tools, most of the late
    experiments and the v38 scorer.
  - Both wrote analysis notes.
  - Fable drafted the explainer, the slides and this file.
- **The human lead:**
  - chose the project's direction at each pivot (Misty as a yardstick, then
    our own engine);
  - set the evidence bar (for example, a next candidate had to score about 80%
    against v35 in direct games, with Instructors and HYPOTHERMIA as an
    external reference);
  - approved or rejected each upload and did every upload;
  - withdrew v36;
  - approved the v38 arena trial against a failed local gate;
  - stopped development on 14 Nov.
- **Other members:** **[to fill in]**.
- **How AI output was checked:**
  - the referee parity tests;
  - pre-registered predictions;
  - one agent reviewing the other's work;
  - arena results as the final test.

  Known AI errors that were caught and corrected are on record:
  - a double-counted game tally (31 duplicates);
  - an all-opponent average that undersold v38, which Henry caught from the
    leaderboard;
  - a misread queen-guard margin in the slides.
- **The instructors warn about writing nobody understands.** Write the report
  yourselves from this material, and keep only claims you can explain.

## 10. Suggested report outline (instructor guidance mapped)

1. Introduction: the game, why it is hard, our approach in one paragraph.
2. Team and contributions (section 2).
3. Background and course connections (section 7; Obscuro as the starting
   point).
4. System: the final bot (section 4).
5. What we tried, in order, with why and results (sections 3 and 5). Keep the
   negative results; the instructors asked for them.
6. Arena results with statistics and caveats (section 6).
7. Lessons and limitations (sections 5h and 8).
8. AI statement (section 9).
9. Appendix: version table (`MUTATIONS.md`), experiment register.

## 11. Where everything is

| What | Path |
|---|---|
| Every arena version, change, hash, prediction, fate | `MUTATIONS.md` |
| Timeline, v1–v34 | `docs/timeline.md` |
| Submission log with checkpoints | `fable-submissions/README.md` |
| Current system and claims audit (11 Nov) | `docs/presentation-20261203.md` |
| Experiment map and case studies | `docs/presentation-experiments.md` |
| Course mapping | `docs/course-map.md` |
| One real decision traced | `docs/presentation-move.md` |
| Two illustrated games | `docs/presentation-cases.md` |
| Tables and algorithms | `docs/presentation-tables.md` |
| Methods, evaluation, architecture | `docs/methods.md`, `docs/evaluation.md`, `docs/architecture.md` |
| Open problems | `docs/open-problems.md` |
| v38 arena trial and corrections | `fable-submissions/analysis/v38-arena-20261108/result.md` |
| Oracle experiments | `fable-submissions/analysis/oracle-*`, `v35base-20261029` |
| Opponent-knowledge search build | `fable-submissions/analysis/kluss-m4-20261114/result.md` |
| Obscuro comparison | `astra-submissions/obscuro-comparison-20261108.md`, `chatroom/358-astra-current-obscuro-gaps.md` |
| Research register (all late experiments) | `astra-submissions/RESEARCH_REGISTER.md` |
| Team notes and ledger | `chatroom/` (numbered notes, `ledger.jsonl`) |
| Engine source | github.com/htansetiawan/mist-c (v38 source: branch `allfit` plus the scorer in the ZIP; the M4 build is branch `fable/kluss`) |
| Published docs site | htansetiawan.github.io/iamavirus/docs/ |
| Explainer (31 Oct) | Google Doc *IAmAVirus: Chess in the Fog* (the team has the link) |
| Slides (updated 21 Nov) and their text | claude.ai slides deck; Google Doc *How IAmAVirus Plays Chess in the Dark (slides and speaker notes)* |

## 12. Before submitting: numbers to refresh

- **v38's final record, rating and rank.** The automatic readings run on 23,
  26 and 29 Nov and on 2 and 3 Dec. The arena may run until the 11 Dec bot
  deadline; take a final reading then.
- **Head-to-head table and time above Instructors/Mist,** recomputed over all
  of v38's games.
- **The final bot.** v38 is the final bot unless the team decides
  otherwise before 11 Dec.
- **Whether we presented on 3 Dec.** The instructors grade presenting teams
  more leniently.
