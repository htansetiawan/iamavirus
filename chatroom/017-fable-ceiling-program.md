# 017 — The ceiling program: find the ceiling first, then compress

For the user and Astra. Started 2026-10-08 11:40 UTC on the user's direction: "first find the ceiling performance, then figure out how to make it smaller, faster, leaner; don't assume we already found the right model size, hyperparameters and architecture."

## What "ceiling" means here, axis by axis

Each axis removes one deployment constraint while holding the rest at the v15 configuration, and is measured both on decisions (the gym corpora) and, where it matters, in games against the v15 bytes.

| axis | constraint removed | decision-level measurement | game-level measurement |
| --- | --- | --- | --- |
| information | the fog: the bot receives the true board | `gym_replay --oracle` | `ceiling_match --a-oracle` vs v15 |
| compute | 2 cores and ~5 s per move | `gym_replay` with 30 s per move, 4 threads | `ceiling_match` with a 1,800 s clock and 20 s per move |
| breadth | 12 matrix rows, 8 hypotheses, 2,048 particles | 40 rows, 32 hypotheses, 8,192 particles | if the decision level moves |
| candidates | the policy's top 8 | `--inject-real`: the strong player's move gets a guaranteed row | — |
| model | 1.9M-parameter CNN-GRU, batch 8, one recipe | sizes S 1.9M / M 8.5M / L 21.7M, one shared recipe (batch 32, cosine, bf16), policy NLL and top-4 on the top six's test moves | the best size in the hybrid gym, then lanes |

Tools: `learning/gym_replay.py` (the real bot binary at each corpus decision, hybrid, packaged model, modeled clock; oracle, injection and any `FOW_*` setting), `learning/ceiling_match.py` (asymmetric local matches on the shared rules, replay-format output), `learning/model_ceiling_eval.py`, `learning/configs/ceiling_{s,m,l}.yaml`. The bot gained `FOW_FORCE_FAST` (forced moves without search, for fast replay) and `FOW_INJECT_MOVE` (offline row injection); both inert unless set.

## Measurement correction

The gym baselines of note 015 were taken with the benchmark harness in cpp mode at 400k nodes per decision; the arena engine searches about 41M nodes per move (median of 248 v15 decisions) in hybrid mode. The first arena-fidelity number agrees anyway: on the strike corpus the real v15 configuration creates an unseen king threat in 40.7% of positions (harness: 39.1%), matches the top bot's move in 32.7%, leaves 3+ points en prise in 8.7% (the top bots' own moves: 6.3%).

## Results

(Filled in as the runs finish; summaries in `data/reports/gym/arena/summary.txt`, `data/reports/ceiling/`, `checkpoints/ceiling-*/`.)

### Information ceiling, decision level (12:20 UTC)

The real v15 configuration (hybrid, v1 model, modeled arena clock, 2 threads) at each of the 900 gym positions, once with its fogged view and once with the true board:

| corpus | metric | v15 as deployed | v15 given the true board |
| --- | --- | --- | --- |
| strike (300) | creates an unseen king threat | 40.7% | **80.0%** |
| strike | plays the top bot's exact move | 32.7% | 61.0% |
| strike | leaves 3+ points en prise | 8.7% | 5.7% |
| route (300) | plays the top bot's first fog-route move | 29.7% | 21.3% |
| giveaway (300) | repeats our old giveaway (3+ en prise) | 24.7% | **11.0%** |
| giveaway | leaves the queen en prise | 9.0% | 2.0% |
| giveaway | king lost | 2.0% | 0.0% |

Reading: the search and evaluation are good enough when they know the board; perfect information doubles the strike rate and halves the giveaways at the same budget. Information is the dominant ceiling on the capabilities that decide our games. The route corpus moves the other way because a fog maneuver is a move made under uncertainty; with the board known the engine plays more directly. Next (running): which hidden pieces carry that value (revealing only the king, only rooks/bishops/queens, only knights/pawns), whether the engine would choose the top bot's move if it were offered as a candidate, compute ×8, breadth, and the oracle in full games.
