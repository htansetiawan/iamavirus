# IAmAVirus: the end-to-end architecture, for review

Written 2026-10-07 22:00 UTC so the choices can be reviewed rather than assumed. Every number is measured or read from the code; file names are given so each claim can be checked.

## 1. The shape of the system

Two systems decide a move, and they meet only at one table:

1. **The belief and search engine (C++)** holds a population of 2,048 full boards consistent with everything we have observed, searches candidate moves on sampled boards, prices risks over the whole population, and solves a small matrix game to pick the move. This is where the game is won or lost; every traced loss this week was a belief or risk-pricing failure.
2. **The neural policy (PyTorch, exported to ONNX, run on CPU)** reads only the observation history and proposes candidate moves with a danger estimate per move. It never sees the particle population and the population never sees it. Its proposals are merged into the engine's candidate list; the engine decides.

```
arena API ──▶ raw store (validated replays) ──▶ manifest (split by game) ──▶ features + labels
                                                                                   │
                                                                                   ▼
                                                   PyTorch stage A (imitation) ──▶ ONNX (observe.onnx, score.onnx)
                                                                                   │
referee observation ──▶ C++ bot: NeuralTracker (planes) ──▶ policy top-8 + danger ─┤
                     └─▶ particle belief (2,048 boards) ──▶ shortlist search top-6 ─┼─▶ candidate union (≤12 rows)
                                                       └──▶ lowest king-risk top-8 ─┘        │
                                                                                            ▼
                                            risk per row over all particles  ──▶ matrix game (rows × 8 hypotheses, 2 threads)
                                                                                            │
                                                                                 regret matching ──▶ move
```

## 2. Data

- **Source**: the public arena API. Every replay is validated by replaying each move with our own rules and comparing the true board and both observations frame by frame; a mismatch quarantines the game (`learning/ingest.py`). Raw store today: 4,707 accepted games, 288k+ frames, all teams.
- **Manifest** (`learning/dataset.py`): split by game into train / validation / test (v2: 2,607 / 326 / 325 games; v3 is being built from 4,707). Fingerprints: `features-v1`, `actions-v1`, the rules build, the manifest's content hash. Each sequence is one side of one game as the ordered observation events that side received.
- **Gold** (`gold/`): our own decisions with truth-side labels for loss analysis; the 634 real losing positions that drive the offline benchmark.

## 3. Input representation (`learning/features.py`, mirrored plane for plane in `neural_observation.cc`, parity-tested)

Pure function of what a bot receives: its colour, the ordered 64-character observations, the moves it chose. The feature module cannot import truth.

**32 planes × 8 × 8**, in the side's canonical frame (ranks reflected for Black so one network serves both colours):

| planes | content |
|---|---|
| 0–13 | current observation, one-hot per square: own P N B R Q K, enemy P N B R Q K, unknown, visible empty |
| 14–26 | last directly observed content of the square: 12 relative piece classes + empty |
| 27 | ever directly observed |
| 28 | age since direct observation, min(age, 100)/100; never seen = 1 |
| 29–30 | from and to squares of our most recent move |
| 31 | en passant target inferred from permitted observations, when actionable |

**8 scalars**: colour, our turn, own kingside and queenside castling rights, three observation-phase indicators (initial, after our move, after their move), min(ply, 1000)/1000.

**Actions**: id = (from × 64 + to) × 5 + promotion (`learning/action_codec.py`), canonical frame.

## 4. The model (`learning/model.py`, architecture id `cnn64x4-gru256-heads-v1`)

| stage | layer | notes |
|---|---|---|
| stem | Conv 3×3, 32 → 64 channels, ReLU | |
| trunk | 4 residual blocks: Conv 3×3 → ReLU → Conv 3×3, skip, ReLU | 64 channels, no normalisation layers |
| projection | flatten 64 × 64 = 4,096 + 8 scalars → Linear → 256, ReLU | 1,050,880 parameters, 56% of the model |
| memory | GRUCell(256 → 256) | the hidden state is carried across every observation event of the game; this is the only memory of history beyond the planes' last-seen/age channels |
| value head | Linear 256 → 128, ReLU, Linear → 1, tanh | game outcome in [−1, 1] |
| belief head | per square: [64 spatial features ⊕ 256 hidden] → Linear → 64, ReLU → Linear → 7 classes | enemy P N B R Q K or none, loss only on hidden squares; an auxiliary task, not used by the engine |
| candidate scorer | per legal move: [hidden 256 ⊕ spatial at from 64 ⊕ spatial at to 64 ⊕ 4 square codes ⊕ 5 promotion one-hot] = 393 → Linear 128, ReLU → Linear 64, ReLU → policy logit and danger logit | policy = softmax over the legal moves; danger = sigmoid per move |

- **Size**: 1,872,394 parameters, 7.5 MB in fp32; ONNX inference 0.14 ms per decision on one CPU core.
- **Activations**: ReLU throughout; tanh on the value; softmax and sigmoid at the outputs. No attention, no normalisation, no dropout.
- **Latent**: a continuous 256-dimensional recurrent state. Nothing discrete, no codebook, no diffusion. The policy's only history beyond the planes is this vector.

## 5. Labels and training (`learning/labels.py`, `learning/pretrain.py`, `learning/configs/replay_ppo.yaml`)

Truth-side labels, read from the full board, never imported by the feature builder or the bot:

- **policy**: the move the recorded player made, cross-entropy over the legal moves, weighted by who played it (Greek Gift and Knight Vision 4.0, Strongly Invisible and Decent 3.0, duck and Instructors 2.0, everyone else 1.0, ourselves 0.5);
- **belief**: the enemy piece class on each hidden square, cross-entropy;
- **danger**: whether the move loses the king on the reply, binary cross-entropy per candidate;
- **value**: the game result, mean squared error against tanh.

Loss = 1.0 policy + 1.0 belief + 1.0 danger + 0.25 value. Sequences of 64 observation events with a burn-in prefix for the GRU, 8 sequences per batch, learning rate 3e-4, weight decay 1e-4, gradient clip 1.0, 10 epochs, full precision, checkpoint by validation loss. About 40 minutes on the RTX PRO 5000 for 3,258 games.

**Stage B (recurrent PPO self-play)** exists (`learning/train_ppo.py`, `env.py`, `rollouts.py`): GAE with γ = 1, λ = 0.95, clip 0.2, KL early stop, a league of frozen checkpoints. Sixty iterations stalled with the ~800 decisions/s Python simulator; it is not in any shipped model.

**Measured quality of the shipped model (v1, test split)**: policy top-1 accuracy on the recorded moves 34.4%; hidden-square belief accuracy 82.8%; danger Brier 0.048 but a false-negative rate of 88%; value loss 0.93 (near chance). The v2 model (player-weighted) was not better in a paired lane and did not ship. v3 (4,707 games) trains now and is judged on the same test split as v1.

## 6. Export and runtime (`learning/export.py`, `neural_inference.cc`, `neural_observation.cc`)

Two ONNX graphs: `observe.onnx` (planes, scalars, hidden → next hidden, spatial, belief logits, value) and `score.onnx` (next hidden, spatial, candidate from/to/promotion → policy and danger logits). Parity against PyTorch on the test shard at rtol 1e-4, atol 1e-5; C++ feature parity against Python on the same events. ONNX Runtime on CPU inside the bot; model load at start-up within the arena's 15 s.

## 7. The engine, per move (`engine.cc`, `belief.cc`, `search.cc`, `regret.cc`)

1. **Observe.** The belief predicts one opponent move per particle from the opponent prior (hand-set conditional-logit over 26 move features: captures, checks, development, persistence, each particle's own last move), conditions on the new view (seen squares exact, visibly empty exact, pawn deductions: an unseen square in front of our pawn holds an enemy piece, unseen pawn-capture squares are empty), resamples systematically from a shuffled pool, and rebuilds from the census when the population dies. 2,048 particles; every surviving particle renders the full observed view exactly.
2. **Candidates.** The policy's top 8 (with its danger estimate), the shortlist search's top 6 (alpha-beta with quiescence and a transposition table on the primary hypotheses, 45% of the budget, 7.2M nodes/s, depth about 10), and the 8 moves with the lowest king-loss probability over the whole population; union of at most 12 rows.
3. **Risk per row, over all particles**: king-loss probability × 30,000; expected best net capture the opponent has after the move (exposure); the best capture they could prepare with one quiet move to a square we would not see (two-ply material, weight 1.0); the share of particles in which such a move puts an unseen attacker on our king (two-ply king threat, weight 0.6 × the king price); a repetition charge when the same view has been seen before and we are not losing. Available but off after measurement: the unseen-attack-surface charge, the vision balance.
4. **Matrix game.** Rows = candidate moves, columns = 8 sampled hypotheses; each cell is a full search of that move on that board (two threads, separate transposition tables) plus a bonus for attacking their king from a square they cannot see, minus the row's risk; cells where the move loses the king are charged outright. Regret matching solves the matrix; the mixed strategy picks the move.
5. **Clock.** Budget from the remaining time (cap 7 s, hard cap 12 s, divisor 20, reserve 6 s), scaled up to 2× on hard turns and down on trivial ones; a deadline fallback does a one-ply search per cell if the turn runs out.
6. **Opening book.** For the first 10 plies, the (colour, exact observation) → move table built from the six strongest teams' games (176 entries, support ≥ 15), played when legal.

## 8. Instruments and gates

- `tests/`: engine, belief, observation and neural suites (622 checks); referee conformance.
- `tools/benchmark_corpus.cc`: 634 real losing positions, every decision of the seat sampled, one binary with each idea behind an environment switch, seeds, per colour; metrics: immediate king losses, survival of the real fatal move, material left en prise, queen left en prise, two-ply material and king threats, vision, belief calibration (hidden piece mass, true attacker held at the fatal ply).
- `learning/compare_archives.py`: colour-swapped paired games between two archives at the arena's clock, paired bootstrap.
- `learning/evaluate.py`: tactical, model, match, arena and runtime suites.
- The arena itself, with the map in `fable-submissions/README.md`.

## 9. What a reviewer should question (my own list)

1. **The projection bottleneck.** Flattening 64 channels × 64 squares into one 4,104 → 256 linear layer holds 56% of the parameters and throws away the board's geometry at the point where it matters most. Square-wise pooling, or attention over squares, would be the standard alternative.
2. **GRU-only memory, no normalisation, no attention.** A small transformer over the observation history (or over squares with a recurrent summary) is the obvious upgrade; the current net was sized for the arena's two CPU cores and 15 s start-up, where it costs 0.14 ms per decision, so there is headroom.
3. **Two beliefs that never talk.** The particle filter is the engine's belief; the network has its own internal one (the belief head is only an auxiliary loss). The policy never sees the population. Feeding the filter's per-square hidden-piece probabilities (six planes from 2,048 particles) into the network is the cheapest way to make the proposals belief-aware, and it is how the two systems could stop being separate.
4. **The danger head misses 88% of real dangers**, so it is logged but not decisive; the particle king-risk term does that job. Training it on engine-derived labels (the population's king-loss probability) instead of the rare recorded outcomes would give it a dense signal.
5. **Imitation only.** 34% top-1 on the strongest teams' moves; no reinforcement learning in any shipped model. Self-play needs the C++ simulator for throughput before it can be judged.
6. **Data is small**: 4.7k games, and the strongest teams are over-represented by design. The policy learns their openings and structures, not their reasoning.
7. **Discrete latents and diffusion**: nothing here is discrete. A codebook (VQ) would make sense for retrieval over an experience index (Astra's lane), not for the policy; diffusion has no role in a move-selection policy at this scale.

## 10. Why this was not put to you earlier

The pipeline implements the specification you asked for at the start (replay learning, recurrent PPO, ONNX on CPU); the layer sizes, the flatten projection, the GRU and the loss weights were my choices within it, made for the arena's CPU budget and never surfaced as decisions. They should have been. This document is the review surface from now on; changes to any of its sections go through the ledger and the gates in section 8.
