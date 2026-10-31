<!-- Exported from the Claude Doc 'IAmAVirus: Chess in the Fog' (https://claude.ai/artifact/6RDBmnFzu2uth64GbeaWhs) on 2026-10-31, after the review pass. The three drawings and the chart live in the doc; here they appear as placeholders. -->

# IAmAVirus: Chess in the Fog

Oct 31, 2026 · @Henry Tan

A technical account of the IAmAVirus Fog of War chess bot as built, written for the 3 December presentation in MIT 6.7980. Everything after this document is an improvement, extension or fix over the system it describes.

## Chapter 1. The game and the problem

Fog of War chess is chess played without seeing the opponent's side of the board. You see your own pieces and every square one of them could move to; everything else is hidden. The bot's whole job is to decide, in the few seconds the clock allows for each move, which move wins most often across all the boards that could be behind the fog.

### The rules in plain words

The pieces move as in ordinary chess, with three changes that matter.

- There is no check and no checkmate. You win by capturing the king. If your move leaves your king where it can be taken, the game ends at the start of the opponent's turn and you lose; the capture is never actually played.
- Moving into danger is legal. The king may step into attack, castle through attack, or ignore a threat. A player with no legal move loses. The two special pawn rules, promotion and en passant, are unchanged.
- The game is drawn when the same position occurs a third time, after 100 consecutive plies (a ply is one player's move) with no capture or pawn move, or at 1,000 plies. Two bare kings are not a draw.

What you see follows one rule: your own pieces, plus every square one of your legal moves could land on. So you see an enemy piece you could capture, and the squares your knights, bishops and rooks reach until they hit something. You do not see the piece blocking your pawn, or anything behind the first piece on a line. You always notice when one of your pieces is taken, because it disappears; you often do not see what took it. The opponent's move is never announced.

### How the game arrives at the bot

The arena talks to the bot in plain text lines. At the start:

```text
fow
w 180 2
```

The second line gives the colour, the starting clock in seconds and the seconds added back after every move. The bot answers `ready` within 15 seconds; that time is not on the clock. Then, before every ply of the game, both players receive a view of the board as 64 characters, one per square from a1 to h8: uppercase for White, lowercase for Black, a dash for a square seen to be empty and a question mark for a hidden square. White's first view is:

```text
RNBQKBNRPPPPPPPP----------------????????????????????????????????
```

On your turn, after the view, a line with your remaining seconds arrives, and the bot replies with one line:

```text
178.123456789
move e2e4
```

Anything else loses the game: a stray line on the output, a move sent at the wrong time, a move that is illegal on the true board, a crash, or a move that arrives after the clock runs out. The clock gives 180 seconds for the game plus 2 seconds back after every move. There is no limit per move: the bot divides its own clock as it sees fit, and over a typical game of 40 moves a side that averages about six seconds a move. The 15 seconds for the ready reply are separate and cover only start-up, loading the tables and launching the helper processes before the first view; once ready is sent the bot is frozen until a view arrives, and it is frozen again while the opponent thinks, so nothing can be computed off the clock during the game. In practice v35 spends 8 to 10 seconds on its opening moves, under 3 seconds late in the game, and finishes with 36 to 39 seconds unused.

Each game runs in a fresh process in a locked box: two processor cores shared with the opponent, 4 GB of memory, no network, and nothing kept from one game to the next. Every team plays rated games against other teams of similar rating, in both colours, and a single rating on the Elo scale used in chess, starting at 1500 and moving at most 8 points a game, follows the team across all its versions.

### One turn of the bot, from the outside

&#91;embedded content: one turn of the engine · 6 stages, from src/main.c\]

The top row keeps the picture of the board up to date; the bottom row chooses the move; the loop runs once a turn.

In words: the bot reads the views and works out every board that is consistent with everything it has seen in the game, keeping at most 200,000 of them. It gives each board a weight for how plausible it is, judged by a model of how arena opponents actually move, fitted on recorded games, with a memory of positions it has met before. It then draws 32 boards in proportion to those weights, grows a tree of moves and replies across them, with Stockfish, the standard open-source chess engine, scoring the positions at the ends, and settles on a plan that does well whichever of the 32 is real. Before playing, it strikes out any move that would leave its king or its queen exposed on too many of the boards. The time it spends is a twentieth of the remaining clock plus 1.6 seconds, never more than 10, and that rule has not lost a game on time in 7,907 arena games.

### Why this is hard

Three things make the problem difficult, and they come back in every later chapter.

- Hidden information. At a typical decision 82 boards fit what the bot has seen, but there are positions where 200,000 do, and the true one can carry a weight of one in a thousand. The bot cannot play well on boards it does not take seriously.
- Time. About six seconds a move on average, on two shared cores, with the whole set of boards to update, the opponent to model and a tree to search inside that window.
- The fog cuts both ways. We win by taking pieces the opponent could not see, and we lose to pieces we never saw. Both sides play the same rules; what differs is how well each one imagines the other side of the board.

## Chapter 2. Where we are going

We set out to learn which half of the problem decides games, seeing or deciding, and to build the fastest honest implementation of the best published method so that the answer could be measured rather than argued. Twenty-five days and 36 arena versions later the answer is: seeing. The search we have wins every game when it is told the truth; what it is told is the whole gap.

### What we wanted to test

Three questions were on the table from the first week.

1. Is Fog of War chess lost in the belief or in the search? Our first engine, a C++ program with a particle filter over 2,048 boards and alpha-beta on each, taught us on 7 October that the capturing piece was hidden in essentially every loss: the losses were belief failures, not search failures. Every engine since has been a test of that sentence.
2. How far can the arena's own record carry us? The arena keeps every game of every team, and we mirror it daily, 186,276 games by 31 October. Opponents can be modelled from how they actually move, openings can be read off our own results, and our losses can be replayed decision by decision.
3. Can a team of two AI agents and one person iterate at arena speed? That needs a local gym whose results predict the arena, proxies cheap enough to run in an hour, and a protocol that keeps two agents from undoing each other's work.

### Why a C engine

Efficiency is itself a strategy. The arena gives two shared cores and a clock that averages about six seconds a move; whatever the method, the implementation that does more per second imagines more boards and searches further. The Python prototype managed 44,000 nodes a second and was never submitted. The C++ engine reached 11 million. For training, a batched C++ simulator stepped 204,440 decisions a second against 800 in Python. mist-c, the current engine, is 4,227 lines of C that update an exact set of up to 200,000 boards inside the clock, with a bitboard update made 2.4 times faster this week at bit-identical output. C also gave us determinism: every random choice is seeded, so any recorded decision can be replayed exactly.

### Obscuro as the baseline

We chose Obscuro (Zhang and Sandholm, ICLR 2026, arXiv 2506.01242) because it is the latest published method for this game, it reports superhuman play, and its design matches the first lesson: it does not guess one board, it solves for a strategy over the whole set of boards it cannot tell apart. On 11 October we ran Misty, an open-source implementation of Obscuro, under our team name for 22 hours as a yardstick. It scored 0.474 over 514 games, 0.12 a game better than our best hybrid on the same schedule (those 540 rated games as Misty count in the team's lifetime rating), and locally it beat that hybrid 8-0 with the same evaluator and the same belief idea. The difference was the search: an equilibrium over information sets instead of a best response to sampled boards.

So we rebuilt it in C from the paper alone. Misty's code was never read; the engine was written in milestones (rules, exact belief, solver, front end) with tests against the course referee at each step. The first trial, arena version 26 on 10 October, lost 17 of 22, every loss to an unseen piece. Version 33 added 32 sampled worlds and a king guard and scored 0.489; version 34 added the history prior and the sharpened weighting and scored 0.526; version 35 added the queen guard and has sat between sixth and tenth place since 14 October; on 31 October it is eighth of 62 at a rating of 1918. Two parts of the paper are not in v35: carrying the solved strategy from one turn to the next, so each of our turns starts a fresh tree, and the purification of the final strategy.

### Sun Tzu as the frame

The lead's inspiration is Sun Tzu's Art of War, and three directions from the first week follow from it: learn the wisdom first and apply it, in a playbook whose first row was know the enemy; win by deception, in the lead's own words, to win games we need to employ deceptions; and a hierarchy of strategy codes learned from replays, under the working name SunTzu. Each became a line of work, and each was tested.

- Know the enemy became the opponent model and the history table: a model of how arena opponents move, fitted on their recorded games, and a memory of what they did after a given history, which fixed a run of losses to one early queen check that the model rated at 12% and the arena played 88% of the time. The grander version, identify the opponent from its first moves and switch to a counter, as the Reconnaissance Blind Chess winners do, reached 52% identification accuracy from early views and was withdrawn. The protocol tells the bot only its colour, so any such switch has to be read from play.
- Deception was built and shelved. A bait term that offers a piece next to the enemy king with a hidden rook behind it won 10-0 against a replica of Mist and 1-5-3 against our own previous version; it pays only against one style of opponent, and the bot cannot tell who it faces. In the current search, hiding and bluffing have no value by construction, because the opponent in the tree always faces our true position.
- The strategy codes were built, audited and withdrawn. Of that line only an opponent classifier and a replay book reached the arena, and the replay book won 8 of 8 on the recorded lines of the one opponent it was built on and 0 of 17 as Black against everyone else.

The frame that stuck is the epigraph of the mutation registry we keep for every candidate: like a virus, we mutate, we learn from what kills us, and the mutations that win survive. Every variant has a parent, a gene, a prediction and a fate.

### Learning from the arena

The arena record is the team's largest asset and it feeds four things. The opponent move model, a conditional logit over 28 move features fitted on 2,029 games, later refitted on 6,776. The history table, 151,316 records of what opponents did after a given information history. The regression suite, 1,379 of our own losing decisions replayed with the exact inputs the engine saw. And the daily taxonomy, which measures every team on back-rank exposure, king moves, sacrifices, fog captures and a dozen other habits, so that our weaknesses are ranked against the field rather than guessed. One further use was tried and closed: replay books against deterministic opponents, since no strong bot is deterministic as deployed. The opening-choice spreads in our own record suggest an opponent-adjusted book worth 10 to 20 Elo; it is not yet built.

### Layers over the base

Since version 33 the principle has been to keep Obscuro's search as the core and add layers the paper does not have. The belief is weighted by the opponent model and the history prior instead of being sampled uniformly. Guards remove a move that exposes the king or the queen on too many boards, the losses that 32 sampled worlds under-represent. A repetition rule handles won positions and a rebuild handles an empty belief. Each layer was motivated by a class of recorded losses and measured on the suite before it played.

Together they took the engine from 0.489 to 0.526; v35's rank has since swung between 10 and 6 on the same bytes. They also found their limit: a third guard, for rooks, bishops and knights, scored 0.33 in the arena as version 36 and was withdrawn, and tuning the margins of the existing guards moves nothing outside noise. The next tier will not come from another layer but from making the belief put its weight on the right boards, which is where Chapters 5 and 6 go.

## Chapter 3. How we built it

The bot that plays today is the fourth engine family in 25 days, chosen by measurement over the other three, and it was built by two AI agents and one person, with the split of work rewritten twice to keep the agents out of the same source file. This chapter is the story of the three that lost, the gym that judged them, the way the team worked, and what two of the course's lectures say about that way of working.

### Four engine families in 25 days

| Family | Arena versions | Dates | Games | Score | What it taught |
| --- | --- | --- | --- | --- | --- |
| C++ belief with a matrix game at the root | 2 to 4 | 7 Oct | 276 | 0.435 | The capturing piece was hidden in essentially every loss: losses are belief failures |
| Neural hybrid: imitation network, then PPO, inside the same engine | 5 to 25, 27 | 7 to 10 Oct | 2,254 | 0.457 | Imitation tops out near 35% of the top teams' moves; RL pays only as a prior; the hybrid failed to escape a hidden check 32% of the time |
| Misty, an open Obscuro, as a yardstick | 28, 30 | 11 Oct | 540 | 0.475 | A strategy over information sets beats a best response to sampled boards, with the same evaluator |
| mist-c, our C Obscuro with layers | 26, 32 to 36 | 10 Oct onward | 9,355 | 0.205 to 0.526 (0.489 to 0.526 for versions 33 to 35) | The layers reach rank 8; the belief's weights are the remaining gap |

### The neural era and the gym

The hybrid era tried the course's deep reinforcement learning unit in full. An imitation network of 1.87 million parameters, a convolutional stack with a recurrent memory over the observation history and heads for value, per-square belief and a move scorer, learned from arena games to predict the top teams' moves at 34.4% top-1. A size sweep to 40.8 million parameters gained one point, so the ceiling was the information in the observation, not the network. A second trainer ran PPO against a league of frozen replicas with a penalty pulling the policy toward the imitation network (the magnet idea from the course's R-NaD and mirror-descent material), and a critic that saw the true board during training. The policy alone played even with the engine of the day; used as a prior inside the root matrix game it moved the rating from 1586 to 1622, within the noise described in Chapter 5. The registry's summary is one line: RL pays only through the prior.

To iterate faster than the arena allows, the team built a gym: a batched C++ simulator stepping 204,440 decisions a second against 800 in Python, a local arena on the course referee, an opponent zoo of behaviour-cloned replicas of each arena team, decision exams cut from recorded games, and the requirement that the gym's ranking of candidates predict the arena's. The first oracle came out of this gym on 8 October: given the true board, the hybrid found hidden king threats 80% of the time against 41% deployed, while eight times the compute changed nothing. Information is the dominant ceiling. The same experiment on mist-c three weeks later gave the same answer, 81-0-0.

The gym also taught us where proxies fail, and every failure is on record. Replicas are not faithful: the same engine scored 0.77 against the duck replica and 0.23 against the real duck. Gates against our own bytes mislead: one network lost 1-4-5 to the previous version locally and went 16-5-3 in the arena, and version 36 passed a 104-game bench and scored 0.33 in the arena. The rule that came out of it is to bench against Misty for search-level changes and to read opponent-specific changes only in the arena. The proxies that survived are the regression suite of our own losing decisions, replayed with the exact inputs the engine saw, where a change must fix ten more decisions than it breaks; the full-clock bench, whose job is to catch forfeits, crashes and clock trouble; and the pre-registered arena prediction, checked every 20 games against what the previous version would have scored on the same opponents. Predictions that break are recorded as broken with the game that broke them: version 18 predicted 0.49 and scored 0.405; version 34 predicted no loss under 20 plies and lost in 19; version 35's prediction broke at 40 games with an 8-ply loss to a hidden check.

### Two agents and a person

&#91;embedded content: the team's working loop · chatroom/README.md, docs/evaluation.md\]

The two agents feed the ledger; the ledger feeds the gates; the arena answers; the mirror brings every game back.

Fable is a Claude Code session and owns the engine, the tools, the benches and the packaging; Astra is a Codex session and owns review, audits, the gate protocols and the confirmation runs; the lead sets direction, reads every note, answers in a sentence and performs every upload. The agents never upload. The division of work changed four times, and the hardest coordination failure was not disagreement but two agents editing the same engine source; it was solved on 10 October by splitting mist-c by file, and for good on 26 October by giving one agent the source and the other the review.

The channels are simple on purpose. An append-only ledger of JSON lines (553 by 31 October: 350 from Astra, 202 from Fable, 1 from the lead), each with a sender, a recipient, a type, a subject and the paths it rests on; corrections are new lines that name the line they correct. Numbered notes, 197 files from 001 to 187, where nobody edits another author's note. A file that allocates the machine's cores before any timing run, because two agents' runs had contaminated each other. And rules for candidates: one version sequence with no number reused, every candidate pinned by hash before its first gate, queues immutable once named, bench games never pooled across candidates, and a prediction written before every upload. A phone channel for the lead was built on 7 October and never used; the lead's words reached the agents through their own sessions.

### What lectures 11 and 12 say about this

Both lectures were given by Brian Hu Zhang, the first author of the Obscuro paper this engine implements. Lecture 11 (information and mechanism design) and lecture 12 (team games and hidden-role games) describe, in order, what cannot help the bot and what does describe the team.

Inside the game, nothing from lecture 11 applies, and the slides are clear about why. Every object in that lecture, the leader who commits, the mediator who recommends, the seller who persuades, is a third party with its own objective who commits and talks. Fog of War chess is a two-player zero-sum game with no such party and no message channel, and the lecture never treats a zero-sum game with a mediator; zero-sum games appear only as the solver, in the Lagrangian of slides 34 to 41, whose closing line is that if you can solve zero-sum games you can compute optimal mechanisms. Our search is the primitive those results consume, not a problem they improve. Two analogies are worth keeping. Our reading of the persuasion slides, not a claim they make, is that the receiver learns from the sender's policy rather than from the message; for us, opponents learn from our move policy, and a deterministic policy leaks more than a mixed one. And information in this game leaks through piece placement: what you can see is a function of where your pieces stand, which the opponent partly reconstructs from the pieces of yours it sees.

The team is close to lecture 12's team game, with one difference: the lecture's teammates act during the game, ours act before it by choosing one bot. The correspondence, slide by slide:

- The ledger is the public observation channel (slide 16).
- The notes and the gates agreed before a candidate exists are the pre-game correlation of slides 6 and 25, flipping coins before the game begins.
- The lead is the mediator who is always on the Good team (slide 37), and the gate protocol is the committed strategy.
- The agents' direct strategies, in the sense of lecture 11's revelation principle (slide 28), are to report honestly and obey recommendations.

Lecture 12 also gives the cost of secrecy a number: the size of the team's decision problem grows as (b+1)^k, where k is the information asymmetry, what one member knows that is not public to the team (slides 19 and 20). With everything on the ledger, k is 1 and the team is a single decision-maker with perfect recall; every result held in one session's memory raises k.

Measured against that, the process fell short in one stretch and improved in two. From 12 to 24 October the ledger has no lines at all while one agent built engine versions v9 to v16 (arena versions 33 to 35) alone; by the lecture's measure the team was two decision-makers with private information for twelve days. Slide 4's warning that a profile of mutual best responses can be a Nash equilibrium in which the team always loses describes the risk of two sessions each tuning against the other's current branch; the 26 October split into one source and one review replaced that with a jointly chosen plan. And the confirmation protocol of 28 October fixed the gate before any candidate existed, which is commitment in the lecture's sense. Three adjustments follow for the rest of the term: post every result before it is used in a decision; keep ledger entries in the form of reports and recommendations, which the revelation principle says loses nothing; and remember that more talk cannot beat a jointly chosen bot and cannot substitute for the arena measurement, since communication has no direct effect on the game.

The arena is not a hidden-role game. There are no in-game teammates, and the opponent's role is known; only its identity is hidden. The one useful line from the hidden-role half is that a type can be inferred only where behaviour differs by type: identifying arena opponents from their moves is worth exactly as much as their play differs, which on our reading is why a classifier over early views could not get far above 52%.

## Chapter 4. The architecture as built

The deployed bot is arena version 35: mist-c, a C program of ten source files, Stockfish 19 as the evaluator at the ends of the search tree, and a 2.4 MB table of opponent moves recorded in the arena. The uploaded ZIP sets two environment variables, the paths to Stockfish and to that table, and nothing else, so every number below is a default in the source. v35 is mist-c commit 97b60f1 of 13 October; the current source differs in two ways noted at the end.

### The pipeline with its constants

| Stage | What happens | Constants in v35 | Where |
| --- | --- | --- | --- |
| Observe | A 64-character line is a view, a number is our clock, anything else is ignored. Two views arrive on our turn (before the opponent's ply and before ours), each triggering one belief update. The legal moves are generated from the view alone, as the moves legal on every board the view allows, so an illegal move cannot be sent. | 13,467 recorded positions with zero mismatches against the course referee | `src/front.c`, `view_moves` in `src/belief.c`, `tests/test_rules.c` |
| Imagine | The belief is the exact set of boards consistent with every observation so far. After our move each board is advanced and kept if it still matches the view. After the opponent's move every board is expanded by every opponent move, the consistent successors are kept, boards where the opponent left its own king capturable are dropped (the referee would have ended the game), and boards reached by several histories are merged with their weights added. Past the cap the set is thinned by weighted sampling without replacement; before an update it is thinned to what half the move budget can afford. If it ever empties it is rebuilt from the view. | cap 200,000 boards; two threads above 4,000 boards; rebuild draws up to 2,000 boards from 60,000 tries; median 82 boards at a decision, maximum at the cap; the true board never missing while the set was exact (60 games, 5,228 plies) | `src/belief.c`, `MIST_CAP` in `src/main.c` |
| Weigh | Each board's log-weight is the sum, over the opponent's hidden moves, of a conditional logit's log-probability for that move among all legal moves, times a temperature. A cheap version of the model runs while the set is above 10,000 boards. Where the opponent's information history has been seen three or more times in the arena, an empirical prior replaces the model: (count + 4 x model) / (N + 4). | 28 hand features fitted on 2,029 games (top-1 27.4% held out); temperature 2.0, so the weights are the fitted posterior squared; history table 151,316 records | `src/movemodel.c`, `MIST_MODEL_TEMP`, `MIST_HISTORY_TABLE` |
| Search | 32 boards are drawn with replacement in proportion to weight. A game tree is grown across them (growing-tree CFR): information sets keyed by each player's own history, rounds of 10 predictive CFR+ iterations followed by 32 leaf expansions chosen by an explorer that alternates between uniform choice over its support and a PUCT rule, each leaf scored by Stockfish at depth 1 with every child's score read in one call. A root move that leaves our king capturable scores -2, a king capture +1, otherwise tanh(centipawns / 400). New information sets start on their best child. After 20 closing iterations the root plays the most probable move of the last iterate. | 32 worlds; two Stockfish processes, one thread and 16 MB hash each; at most 1.5 million nodes; stops at 85% of the budget; measured median 194,000 nodes and 1,890 iterations per decision, 4.1 to 8.5 s a move | `src/gtcfr.c`, `src/cfr.c`, `src/sfeval.c` |
| Guard | For every allowed move, over the belief strided to 20,000 boards: the share on which the move leaves our king capturable, plus 0.9 times the share on which the queen is then lost for four or more pawns. A move is removed when its risk exceeds the safest move's by more than the margin under the belief's own sharpened weighting or under the fitted weighting; if nothing survives, the sharpened weighting alone decides. The repetition rule refuses a third arrangement of our own pieces when two or more points ahead, and yields to the guards when both would leave no move. | king margin 0.02, queen margin 0.05, queen weight 0.9; no piece guard in v35 | `MIST_KING_GUARD`, `MIST_QUEEN_GUARD`, `MIST_REPEAT_LEAD` in `src/main.c` |
| Move | Budget = remaining clock / 20 + 0.8 x the 2 s increment, at least 0.3 s, at most 10 s and never over 30% of what is left; under 20 s left the search gets 0.3 s. The chosen move is checked against the view's legal set; if it fails, the best move by a static evaluation of the visible board is played instead. One log line goes to stderr, then `move e2e4` to stdout, flushed. | 0 losses on time in 7,907 arena games; 36 to 39 s left at the end of a typical game | `move_budget` in `src/main.c` |

### Surviving the protocol

The engine is built so that the referee's loss conditions cannot trigger. It writes to stdout exactly once a turn. It proves legality from the view rather than from the belief, so a wrong belief can cost a game on the board but never by an illegal move. If a Stockfish worker stops answering it is relaunched, at most three times a game, after which the search runs on the engine's own evaluator. If the belief empties, it is rebuilt; if the search returns nothing usable, a fallback move is chosen on the visible board. Startup loads the history table and starts the workers before printing `ready`, inside the 15 s allowance. Every random choice is seeded from a fixed seed plus the decision index, so a decision can be replayed exactly; only timing varies between runs. Since v35 went up, no game has been lost to a forfeit, a crash or an illegal move.

### What is ours and what is not

The design is Obscuro's (Zhang and Sandholm, ICLR 2026); the weighting, the guards, the engineering and the measurement are ours.

| Piece of the bot | Origin | Our part |
| --- | --- | --- |
| Track every board consistent with the observations; play a strategy over that set | The definition of play on an information set; standard in Reconnaissance Blind Chess bots for years | None; it is the problem statement |
| Exact belief update, sampled worlds, a public tree with each player's private information sets, growing-tree CFR, Stockfish at the leaves | Obscuro (arXiv 2506.01242); the growing tree follows Player of Games (Schmid et al., 2023) | A from-scratch C implementation written from the paper only; the cap, the weighted thinning, two-thread updates, the clock accounting |
| An equilibrium move over the sampled worlds, not a worst case over all boards | Obscuro's search | Argmax of the last iterate; the paper's purification is not implemented |
| Weights on the belief from an opponent move model | The paper samples worlds uniformly and names sampling by a model of opponent behaviour as the next step in its conclusion | Ours: the conditional logit over 28 move features fitted on arena games, the temperature, and the history prior keyed by the opponent's information state |
| King guard, queen guard, repetition rule, belief rebuild | Not in the paper | Ours, each motivated by a class of recorded losses and measured on a regression suite of our own arena losses |
| The diagnostics: oracle belief, truth-share harness, sharpness curve, hazard calibration, skill scorecard across teams | Not in the paper | Ours |
| The neural pipeline: imitation network, regularised PPO with a privileged critic, a league of frozen opponents, a native simulator | The course's deep RL unit | Ours, built and measured; not in the move selector |
| Misty, a public Obscuro implementation | Brian Liou | Used only as a sparring partner, never read for mist-c |

Two parts of the paper are not in v35: carrying the solved strategy between turns and re-solving against it (each of our turns starts a fresh tree), and the purification of the root strategy. Both are on the list in Chapter 6.

### The measurement and release program

Every change passes through the same instruments, in order of cost.

1. The regression suite: 1,379 recorded decisions from our own arena losses, each replayed with the engine's earlier moves forced and scored on the true board (did the move leave the king capturable, how much did it cost by Stockfish, did it repeat the game move). The noise floor is about five flips, so a change must fix at least ten more decisions than it breaks.
2. The local bench: full 180+2 games on two pinned cores against the previous bytes and against Misty, with no forfeit, no crash and a lowest clock above 20 s as hard conditions.
3. The 100-game confirmation, the standard since 30 October: 50 colour-swapped pairs against the frozen previous version, held-out seeds, uncertainty computed at the pair level. Twenty-game screens are used only to fail fast, never as evidence.
4. The arena: a written prediction and a withdrawal rule registered before the first game, a check every 20 games against what the previous version would have scored on the same opponents, and withdrawal on any forfeit, crash or a score more than 0.15 a game below expectation.

Candidate ZIPs and their queues are immutable once named, bench games are never pooled across candidates, and the human lead makes every upload. The diagnostics that feed the decisions are the oracle (the search handed the true board), the truth-share harness (the true board's weight and rank inside the belief), the sharpness curve (the truth forced to a fixed share), the hazard calibration (predicted against realised fog attacks), a replay tool that re-decides any recorded move, and a daily taxonomy of every arena game.

### Where the current source differs from v35

A binary built from the current source is not v35 in two ways. The piece guard, which vetoes moves that hang a rook, bishop or knight, is on by default (it was v36, scored 0.33 in the arena and was withdrawn; local runs set `MIST_PIECE_GUARD=-1` to play as v35). And the move model has 39 features plus piece-square tables fitted on 6,776 games; it scored 0.525 over 100 games against v35, level, and was not deployed. The arena record in this document is v35's; the code paths are the same.

## Chapter 5. Observations and limitations

v35 wins more arena games than it loses, 0.526 over 7,907 games since 14 October, and still sits eighth of 62 at a rating of 1918, because the points come from the field below us while the five teams at the top take two games in three or more. Nearly every loss has the same shape: material drains into the fog by ply 25, and the king falls some sixty plies later to a piece we never saw.

### Where the points go

&#91;embedded content: data/raw/accepted.jsonl · 7,907 v35 games, 14 to 31 October 2026\]

The pattern is a tier structure. Against the four teams rated 2050 to 2100 (Strongly Invisible, Decent, Knight Vision, Crimson Fog) v35 scores 0.22 to 0.32, against Greek Gift 0.08, against the two teams between them and us (duck, Mist) 0.34 and 0.49, against Instructors, just below us, 0.41, and against everyone else below us 0.57 or better. Rank 3 means scoring about 0.5 against those four and 0.2 against Greek Gift. The distance is about 175 Elo, an expected score of 0.26 at that gap.

Colour matters. As White v35 scores 0.568, as Black 0.483, and against the teams above us the Black score runs from 0.05 to 0.43. No loss is a forfeit, a crash or an illegal move: all 3,646 end with our king capturable on the true board, and our losses run ten plies longer than our wins (median 86 against 76). We are ground down, not trapped.

### How a loss happens

The final capture is a formality. When the king falls we are already five or more points of material behind in 81% of losses, and 97% were three or more down earlier, at a median ply of 25 in games that last 86. The capturer is a rook or a queen in 85% of cases and was unseen at our last decision in 93%.

The bleed is ours. Within the first thirty plies we move a piece worth three or more onto a square attacked by an enemy piece we cannot see 1.95 times a game, against 1.3 to 1.6 for the top bots. The punishment rate is the same for everyone, about two thirds, so the opponents are not sharper; we walk in more often. Counting only entries that are still uncompensated two plies later, ours are 0.15 a game against 0.03 to 0.05, three to five times theirs. The result is that we are three or more points down by ply 30 in 14 to 17% of games against 3 to 10% for the teams above us, and our score from that position is 0.25.

Two things this is not. It is not a conversion problem: on a lead held for three consecutive plies, Black converts 0.78 and White 0.83, and an earlier reading that Black converted only 0.45 was an artifact of measuring in the middle of an exchange. And it is not a search problem: in the blunder audit the true board was inside the belief in 68 of 71 blunders, but at a median weight of 0.06%, and when the search is handed the true board it wins every game. The belief holds the right world and does not weight it.

### What the bot does worse than its neighbours

The move taxonomy over 10,843 arena games of 25 to 28 October, ranked among 15 teams, puts v35 last for leaving the back rank bare (6.9 per 100 moves against a tier-two median of 4.45), 13th for king moves (15.9 against 13.2), 12th for sacrifices, meaning three or more points given over two plies (2.5 against 1.35), and 12th for king threats. In the middlegame it moves its king 13.0 times per 100 moves against 7.6 for the top six, and when three or more fog lines reach the king it is captured within four plies 32% of the time. It ranks 4th or 5th for the things fog rewards: the share of its captures the victim could not see (0.46), vision gained per move and long strikes. The engine exploits the fog well when it attacks and does not defend against it. We lose the queen outright in 17% of games against the top six and score 0.02 in those games.

### What this week's experiments established

| Question | Result | What it decided |
| --- | --- | --- |
| Is the search good enough? | v35's search with the true board in place of its belief: 41-0-0 against itself, 40-0-0 against v35 | The belief is the whole gap; the search needs no work |
| How much weight does the truth need? | Truth forced to 5, 20 and 50% of the belief, measured on the v36 configuration (piece guard on): 0.575, 0.800 and 1.000 against v35; on v35's own configuration the natural lane scores 0.475 and the 20% lane 0.725 | Target share 0.2 as the floor; the natural median is 0.003 to 0.010, a gap of 20 to 60 times |
| Do more worlds help? | Belief cap 200K to 1M: coverage rises, the truth's weight stays 1.8 to 2.0 times uniform | Coverage is not the gap, weight is |
| Can guard margins be tuned? | King and queen margins swept on 487 suite decisions: changes inside the five-flip noise | Margins are not a lever |
| Can an opponent be exploited? | No strong bot is deterministic as deployed; 0 forced lines against current versions | The exploit route is closed |
| Does a better opponent model help? | Fitted piece-square model (v23): 14-0-6 on a 20-game screen, 52-1-47 over 100 | Level with v35; 20-game screens mislead |
| Is the belief miscalibrated? | Fog-attack probability under-confident 2 to 7 times in the 1 to 30% range; support failure absent; losses and trades inseparable on the static estimate | No veto can work; the correction must reach the worlds the search sees |
| Can world re-weighting fix it? | Boosting fog-attack worlds: truth share on 166 loss decisions +6% at best; by destination squares +20% | A calibration rather than a cure: on loss decisions the share (0.001) needs to rise about 200-fold, against 20 to 60-fold at the median decision |

### Lessons about measuring

The arena is noisy at the scale that matters. The rating moves eight points a game at most, and a 20-point swing is a day's noise: v35's last 200 games span 61 rating points on unchanged bytes. Detecting a 15-Elo gain at two sigma takes about 2,100 games, a 100-Elo gain about 50. Opponents change with our rating, because pairing favours proximity, so a version can score better for reasons outside its control: the same v35 bytes scored 0.517 before v36 went up and 0.573 after it came down, while the rating fell.

Three mistakes are on record. A 20-game screen is the high end of noise as often as a signal: v23 screened 14-0-6 and confirmed 52-1-47. A 104-game bench against v35 and Misty passed the piece guard that then scored 0.33 in the arena, because the arena population differs from both sparring partners. And a lead measured at a single ply can be an exchange in progress. The standard since 30 October is a 100-game confirmation: 50 colour-swapped pairs at full clocks, frozen bytes, held-out seeds, uncertainty computed at the pair level, then a fail-fast rule of 20 games in the arena.

## Chapter 6. The road to December

Everything above is the system. What follows is the list of changes it can take between now and 3 December, in the order the evidence ranks them, each with the test it has to pass. Nothing on this list changes the architecture; each is an improvement, an extension or a fix over the scaffold of Chapters 1 to 4, and the results land in Chapter 5's table as they come.

### The bar and the test

Rank 3 is about 175 Elo away, an expected score of 0.73 against v35; the lead's bar, a candidate that beats v35 about 80% of the time, is stricter (about +240 Elo) and is the one the test below serves. The test for any strength claim is fixed: the regression suite first (fix at least ten more decisions than it breaks), then 100 unforced games against the frozen v35 as 50 colour-swapped pairs with held-out seeds and uncertainty at the pair level, then the arena with a written prediction and a 20-game withdrawal rule. A 20-game screen is a fail-fast device, never evidence. Belief changes carry one more offline test before any game: the true board's share of the sampling weight on recorded decisions, where the floor that converts is 0.2 and the natural median is 0.003 to 0.010.

### Improvements to the belief

The oracle fixed the route: the search wins every game on the truth, so the weight the belief gives the truth is the lever.

1. An opponent model that conditions on what the opponent could see and on its own history. The linear model refit (v23) raised the truth's share eightfold on our own games and was level in play; the per-world neural discriminator's first gain was a leakage and the corrected version a null. What is untried is a model of the opponent's decision as the opponent experiences it, not as we see it. Test: truth share median above 0.05 on the 60-game trace set before a 100-game lane.
2. The destination-coverage term at strength 0.2, measured this week: it calibrates the fitted fog-attack estimates and lifts the truth in 112 of 120 losses where the true board is above expectation. Too small alone; free as an ingredient of the next candidate's base. Test: it must not lower the overall truth share, which it does not at 0.2.
3. A per-move correction inside the search: re-weight each root move's value across the 32 worlds by the measured under-confidence for its own destination square, from the calibration tables. This reaches the place a state-level re-weighting could not. Test: the suite's fatal and material decisions, then the replay tool on the 166 unseen-capturer losses, then games.
4. More sampled worlds, re-tested. Version 33 cut the draw from 128 to 256 worlds down to 32 because more worlds spread the search too thin; with the belief update now 2.4 times faster and a weight fix in hand, a larger draw is worth one more test. Alone it is not a lever.

### Extensions from the paper

5. Carrying the solved strategy between turns (the paper's 2-KLUSS re-solving). Astra's branch holds the gadgets and is unmerged; the paper's ablation reports that removing this alone drops Obscuro to 58% against itself. Test: suite, then the 100-game lane; the clock cost must leave the lowest end clock above 20 s.
6. Purification of the root strategy, which the paper does and we do not. Cheap to add. Test: suite only, unless it changes more than noise.
7. The frontier value. Stockfish at depth 1 scores the leaves as if the position were fully seen; more search time was close to neutral on the suite (fixed 12, broke 5 of 487 decisions), so this stays last unless a belief fix changes which leaves matter.

### Cheap levers

8. An opening book adjusted to our own record: the spreads inside our lines are worth an estimated 10 to 20 Elo. The local lane cannot see an opponent-specific gain, so this is read only in the arena, with a prediction per line and the 20-game check.
9. The clock. Games end with 36 to 39 s unused; spending it is free, but more time per move fixed 12 and broke 5 of 487 suite decisions, so expect little. Test: no forfeit over the 100-game lane.
10. The habits the taxonomy ranks us worst on, leaving the back rank bare and moving the king in the middlegame, have no guard-shaped fix left: the king-move hazard terms were withdrawn and the margins are not a lever. They improve only through items 1 to 5.

### Fixes

- The slide fact-check of 29 October marks the registry's epigraph (like a virus: we mutate, we learn from what kills us, and the mutations that win survive) as untraceable; it is the epigraph of the mutation registry and has been since 10 October. Correct the fact-check.
- The draft paper gives the presentation as 1 December and the engine as 3,000 lines; the date on record here is 3 December and the engine is 4,227 lines. Reconcile before the talk.
- The current source enables the piece guard by default and ships a different move model; a build from it is not v35. Set the default back to v35's or pin v35's commit for every local run that claims to be v35.

### What the talk should carry

Chapters 1 to 4 as the system, Chapter 5 as the evidence, and this chapter as the plan. Any item above that passes its 100-game test before 3 December is a line in Chapter 5's table and one slide; any that fails is also a line, with the number that failed it.

## Sources

Repository paths are in `github.com/htansetiawan/iamavirus` (private) unless marked mist-c (`github.com/htansetiawan/mist-c`); the deployed engine is mist-c commit 97b60f1. Numbers are as of 31 October 2026, 10:10 UTC for the arena record and 17:40 UTC for the local results.

- Chapter 1: the course starter kit's `referee.py` (rules, observation, protocol, failure codes) and its README (arena box, validation, Elo); mist-c `src/front.c`, `src/main.c`, `src/belief.c`; `tests/test_rules.c` on the referee's 13,467 positions.
- Chapter 2: `chatroom/001`, `013`, `025`, `026`, `027`, `034`, `035`, `120`, `172`; `MUTATIONS.md` (the registry and its epigraph); `docs/methods.md`, `docs/timeline.md`, `docs/course-map.md`; mist-c `README.md` and `docs/SPEC.md`; `fable-submissions/analysis/perf-20261029/`.
- Chapter 3: `learning/README.md`, `GYM.md`, `ARCHITECTURE.md`, `chatroom/017` (the ceiling program); `docs/evaluation.md`; `chatroom/README.md`, `chatroom/ledger.jsonl`, `chatroom/cores.json`, `astra-submissions/AGENTS.md`; `chatroom/159`, `174`, `176`, `177`, `178`; the per-version record computed from `data/raw/accepted.jsonl`; lecture slides `L11_mechanism_design.pdf` and `L12_team_games.pdf` from [the course site](https://www.mit.edu/~6.7980/), both by Brian Hu Zhang; the course's Fog of War challenge page for the rules text.
- Chapter 4: mist-c `src/main.c` (budget, caps, guards, repetition), `src/belief.c`, `src/movemodel.c`, `src/gtcfr.c`, `src/cfr.c`, `src/sfeval.c`, `arena/run.sh`, `tools/package.sh`; `fable-submissions/README.md` (the version map and checkpoint log); `docs/evaluation.md`; `chatroom/177` (the confirmation protocol); `chatroom/120` (Astra's architecture audit).
- Chapter 5: `data/raw/snapshots/2026-10-31T101023…/leaderboard.json`; `data/raw/accepted.jsonl`; `fable-submissions/analysis/black-losses-20261030/` (loss anatomy and addenda), `black-conversion-20261030/`, `hazard-calib-20261030/`, `attack-reweight-20261031/`, `oracle-20261028/`, `oracle-share-20261029/`, `v35base-20261029/`, `perf-20261029/cap-test.md`, `guard-grid-20261029/`, `exploit-20261029/determinism.md`, `v23-confirm-20261030/`; `docs/skill-rubric-20261028.md`, `docs/top3-reanalysis-20261027.md`, `docs/v36-status-20261027.md`, `docs/paper.md` (Elo mechanics), `data/reports/daily/insights-latest.md`; `chatroom/180`, `182`, `185`, `186`, `187`.
- Chapter 6: the lanes above, including the follow-up section of the attack re-weighting result (the destination-coverage sweep: +20% truth share on the loss decisions, 112 of 120 losses lifted); `chatroom/182` (the share targets), `185` (v23), `187` (re-weighting); Astra's branch `astra/m4` in mist-c; the opening-choice spreads in `fable-submissions/analysis/black-losses-20261030/result.md`.
- Papers: B. H. Zhang and T. Sandholm, General search techniques without common knowledge for imperfect-information games, and application to superhuman Fog of War chess, [arXiv 2506.01242](https://arxiv.org/abs/2506.01242), ICLR 2026. Brian Liou, Misty (misty-chess 0.1.3, GPL-3.0), used only as a sparring partner.
- Earlier drafts this document supersedes: `fable-submissions/analysis/slides-factcheck-20261029/as-built.md` (the slide fact-check of 29 October) and `docs/paper.md` (mid-October).
