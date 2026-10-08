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

### Decomposing the ceiling (14:30 UTC)

Same 300 strike and 300 giveaway positions, real v15 configuration, one axis at a time:

| configuration | strike found | exact top-bot move | giveaway repeated | queen en prise |
| --- | --- | --- | --- | --- |
| v15 as deployed | 40.7% | 32.7% | 24.7% | 9.0% |
| **reveal only their king** | **69.0%** | 53.0% | 25.3% | 7.0% |
| reveal only their rooks, bishops, queens | 61.0% | 47.7% | **15.0%** | 3.0% |
| reveal only their knights and pawns | 55.0% | 44.0% | 17.0% | 3.3% |
| full information | 80.0% | 61.0% | 11.0% | 2.0% |
| top bot's move guaranteed a candidate row | 50.7% | 44.7% | — | — |
| 8× compute (30 s, 4 threads; 100 positions) | 41.0% | 33.0% | 27.0% | 9.0% |
| breadth (40 rows, 32 hypotheses, 8,192 particles, 30 s; 100 positions) | 48.0% | 40.0% | (running) | |

Reading:
- **Compute is not a ceiling.** Eight times the search changes nothing; the engine can be made leaner without losing strength on these capabilities.
- **The enemy king's location is the strike ceiling.** Revealing only their king recovers 28 of the 39 points between the deployed engine and full information. At those positions our belief puts on average 47.7% of its mass on the true king square; in 120 of 297 it puts less than 20%, spread over 7.2 candidate squares. Strike rate by that mass: < 0.2: 22%; 0.2–0.5: 32%; 0.5–0.9: 44%; ≥ 0.9: 59% (`data/reports/gym/strike-enemy-king-belief.txt`; cpp harness, 100k nodes).
- **Their sliders' locations are the discipline ceiling.** Revealing rooks, bishops and queens takes giveaway repeats from 24.7% to 15.0%; the king alone does nothing for giveaways.
- **Candidates matter, but less.** Offering the top bot's move as a guaranteed row lifts the exact match from 32.7% to 44.7%; under fog the engine still declines most of them, and with full information it accepts 61%.
- Breadth (more hypotheses and particles) helps a little (48.0%), consistent with the king finding: more hypotheses cover more king squares.

### Model ceiling (14:15 UTC)

Three sizes with one shared recipe (batch 32, 16 epochs, cosine, bf16) on manifest v4, selected on validation policy loss, scored on the game-disjoint test shard (`learning/model_ceiling_eval.py`, `data/reports/ceiling/model-sizes-test.json`):

| model | parameters | top six: top-1 | top six: top-4 | top six: policy NLL | belief loss | danger loss |
| --- | --- | --- | --- | --- | --- | --- |
| S, new recipe | 1.9M | 33.8% | 61.1% | 2.369 | 0.528 | 0.177 |
| M, new recipe | 8.5M | 35.1% | 62.6% | 2.316 | 0.491 | 0.143 |
| L, new recipe (best at step 1,880; overfits after) | 21.7M | 34.6% | 62.6% | 2.311 | 0.487 | 0.143 |
| v4 release: S, old recipe (batch 8, 8,451 steps) | 1.9M | 35.6% | 63.9% | 2.254 | 0.474 | 0.128 |

Reading: on this data (3,766 training games) size buys about one point of top-1 at a matched recipe and the 21.7M model overfits the policy; the small model trained longer with small batches beats all three. Imitation quality is data-limited, not capacity-limited. Size does help the auxiliary heads (danger false negatives 87% → 57% from S to L), which matters for risk but has not translated into strength before.

### What the ceiling says about v16 and beyond

1. Put the effort into **information about their king**, then about their sliders. Concretely: (a) track castling and king walks in the belief (where can their king be, given every square we have seen), measured by king mass on the strike corpus (47.7% → 75%); (b) value moves that locate the king (a scouting term: expected reduction in king-square entropy), measured by the same; (c) slider tracking for discipline (the line-of-sight work), measured by the giveaway corpus.
2. **Do not spend on compute or model size.** Compress instead: the same strength at less search is available now.
3. The learned policy predicts top-six moves at 62–64% top-4 from the mover's own view, against 36% for the hand prior on the true board; run from the opponent's seat it is the natural level-2 opponent model for the belief's prediction step.
