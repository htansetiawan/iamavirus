# IAmAVirus: two-page human review

[Download the printable PDF](assets/presentation/iamavirus-v38-review-20261111.pdf).

*Local source-checked review, 11 November 2026. The website deployment remains disabled.*

## How one move works

The arena ends when a mover leaves its own king capturable. Attacking the other king alone does not end the game.

1. **Observe.** Read our 64-square private view and clock. A hidden square is unknown; it is not a visibly empty square.

2. **Infer.** Advance weighted possible positions through compatible moves. Merge native position keys. The configured retained-population cap is 200,000.

3. **Screen and sample.** Apply root king/queen risk guards. Normally draw 32 worlds by weight with replacement; merge repeated draws into chance branches.

4. **Grow and evaluate.** Build one local game tree. Stockfish depth-1 child scoring sees both sides on each complete imagined board, not the live true board.

5. **Update the strategy.** PRM+ compares each action with the current mixture using counterfactual values. These regret updates happen inside this move, not across old games.

6. **Act.** Execute the highest-probability permitted root action. Retain belief/front-end history. Discard the FoW tree and regret arrays before the next move.

Tree growth, evaluation and regret updates alternate within the move budget.

## A real prefix: 128 positions → 32 draws → 2 branches

| Position | Belief weight | Draws | Search share |
| --- | ---: | ---: | ---: |
| W98 | 93.7145% | 29 | 90.625% |
| W36 | 6.2280% | 3 | 9.375% |
| Other 126 | 0.0575% | 0 | 0% |

Both branches share one root strategy across 39 actions. The sampler keeps all 128 positions in belief for later observations.

Fresh two-second reconstruction of c8ozqj0m, White decision 5. Both local runs choose g1f3; the recorded arena action is c2c3. This is a teaching trace.

Belief and front-end history survive between moves. Stockfish can retain its own cache. The FoW tree is rebuilt; coefficients and history counts stay frozen between uploads.

## Evidence and limits

**Scoring.** 1.57–1.68× scorer throughput; about 38% more equal-time nodes on the fixed panel. Scores change: the scorer is approximate. The failed Misty gate remains failed; the arena trial was separately authorized.

**Inference → play.** Replay panel: 63 games, only two IAmAVirus observers; truth-log-share gain +0.47277 nats. The full-engine pilot ends 1W–8L under futility, seven legs unstarted; all 901 frames pass rules checks. Configuration closed.

**Arena snapshot.** 11 Nov, 03:27 UTC: 339W–27D–254L in 620 games; raw score 56.9%. The later 493 games track v37's historical same-opponent level. Changing opponents and scheduling limit causal claims.

- **Belief and sampling.** Capping can lose the real position; weighting can underrate it; a small sample can omit it. These are separate failure modes.

- **Information model.** One representative opponent history per position. Opponent-compatible past alternatives, full 2-KLUSS gadgets and cross-turn blueprint reuse are absent from v38.

- **Continuation values.** Stockfish is a perfect-information evaluator on imagined boards. No qualified learned FoW frontier value replaces it.

- **Strategy output.** The root takes an argmax. World-sampling randomness is distinct from drawing an action from the computed mixed strategy. No full-game Nash certificate.

- **Data lineage.** Raw collection, taxonomy, exported examples, fitting and packaged models advance separately. Historical metadata and holdout limitations remain explicit.

Shipped: two 28-coefficient move models and one 359,889-record history file; borrowed Stockfish NNUE. The historical CNN–GRU/PPO policy and neural regret approximation do not play in v38.

Our contribution is native implementation, replay instrumentation and measured engineering around published ideas. Faster scoring is established on its panel; a lasting arena strength gain is not established.

## Evidence paths

- Runtime and table inventory: `astra-submissions/analysis/presentation-audit-20261111/`.

- Real multi-world trace: `astra-submissions/analysis/presentation-multistate-20261111/`.

- Speed and release decision: `astra-submissions/v38-release.md`.

- Confirmed prior and rejected playing pilot: `chatroom/355 and chatroom/357`.

- 620-game reading: `fable-submissions/analysis/v38-arena-20261108/result.md`.

- Information-set example and source comparison: `docs/presentation-knowledge.md and chatroom/358`.

Read next: [runtime and tables](presentation-tables.html), [real move trace](presentation-move.html),
[experiment record](presentation-experiments.html), [who knows what](presentation-knowledge.html).

This handout does not report a new experiment, candidate, live rating, model update or deployment.
