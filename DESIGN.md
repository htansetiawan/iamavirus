# Design canvas

One page per component: what it is for, its interface, the invariants it
keeps, the decisions behind it, what has been measured, and what is open.
This is the working document for design discussions; `ENGINE.md` is the
narrative of the search engine, `HANDOFF.md` the session record, and
`learning/README.md` the runbook.

Numbering follows the data flow:

```
 public replays ──► 1 rules ──► 2 ingest ──► 3 histories/features ──► 4 dataset
                       │                                                  │
                       ▼                                                  ▼
                 5 simulator ◄──────────── 7 PPO ◄──────────── 6 model + stage A
                       │                                                  │
                       ▼                                                  ▼
          9 evaluation ◄──── 10 C++ engine (cpp/neural/hybrid) ◄──── 8 ONNX export
```

---

## 1. Rules core (`position.*`, `observation.*`, `rules_capi.cc`, `learning/rules.py`)

**Purpose.** One implementation of Fog of War movement, visibility,
termination and en passant inference, shared by the engine, the simulator,
the labels and the tests.

**Interface.** C++: `Position` (make/unmake, Fog of War move generation,
Zobrist key), `RenderObservation`, `LegalMovesFromObservation`,
`InferEnPassant`. C (for Python): `fow_position_*`, `fow_legal_from_observation`,
`fow_infer_en_passant`, `fow_move_loses_king`, `fow_engine_*`. Python:
`rules.Board`, `rules.GameState.outcome()` (the referee's order: king
capturable, threefold with en passant counted only when capturable, 100-ply
rule, no legal moves, 1,000-ply arena draw), `rules.CppEngine`.

**Invariants.** Legal moves from an observation are exact (destinations and
slider paths are always visible). No check restriction; leaving the king
capturable is a legal, losing move. Fool's mate is not terminal.

**Decisions.** Bind Python to the C++ rules through `ctypes` rather than
re-implementing them: the C++ passes the referee differential test, a second
copy would need its own. `librules.so` is rebuilt on demand by `learning/_native.py`.

**Measured.** 30,100/30,100 and 18,625/18,625 checks against `referee.py`;
`learning/tests/test_rules_vs_referee.py` covers draws and repetition keys.

**Open.** None known.

---

## 2. Replay collection and validation (`learning/api_client.py`, `learning/ingest.py`)

**Purpose.** Turn the public arena API into an immutable, validated cache.

**Interface.** `ApiClient` (sequential, ≥ 1 s between requests, `Retry-After`
and bounded backoff on 429/503, 400/404 raised), `ingest_from_api(team |
player_id | --all)`, `ingest_from_corpus`, `validate_replay(replay) ->
(states, problems)`, `RawStore` (`games/<id>/{replay,listing,diagnostics,
fetch_metadata}.json`, `quarantine/<id>.json`, `accepted.jsonl`).

**Invariants.** Every accepted replay reproduces every frame's board and both
observations under the pinned rules, every recorded move is legal, the game
does not continue past a terminal position, and a normal result agrees with
`GameState.outcome()`. `whiteVersion`/`blackVersion` are stored as played;
`*CurrentVersion` never replaces them.

**Decisions.** Quarantine, never patch. Diagnostics are optional and
archived separately. Team ids are resolved from a timestamped leaderboard
snapshot.

**Measured.** 1,500 games, 0 quarantined, 0 candidate mismatches.

**Open.** Polling service (not built; spec allows ≥ 30 s cadence).

---

## 3. Histories and features (`learning/histories.py`, `learning/features.py`, `neural_observation.*`)

**Purpose.** Build each player's *information history* and turn it into model
inputs without ever touching the truth.

**Interface.** `build_episode(replay, states, side) -> PlayerEpisode` with
separate `actor` (observations, phases, plies, decisions, own actions, legal
lists) and `targets` (boards, king-loss labels, returns, validity masks) and
`metadata`. `FeatureTracker.observe(view, phase, ply)` once per real view,
`record_own_move(uci)`, `planes() [32,8,8]`, `scalars() [8]`,
`legal_candidates()`. `NeuralTracker` is the C++ mirror.

**Event model.** Frame `t` is the position after `t` half-moves; a decision
at `t` pairs the history through `t` with `frames[t+1].move`. Phases:
`initial`, `after_own_move`, `after_opponent_move`. White: view 0 → decision
→ views 1, 2 → decision. Black: views 0, 1 → decision. A rules-decided terminal
frame is never delivered; after a bot failure the final view was.

**Invariants.** Features depend only on `actor`; the information-isolation
test alters truth and metadata and asserts identical tensors. Castling rights
are sticky (never restored by a returning rook). En passant is inferred only
at a decision, from the view after our own move and the view after theirs.
Observation-derived candidates equal the referee's, or the sample is blocked
and the case recorded.

**Decisions.** Canonical coordinates (`square ^ 56` for Black) so one network
serves both colours. Last-seen planes are memory, not a current-position
claim. Clocks are not features (the C++ time manager owns them).

**Measured.** C++/Python parity on every plane, scalar, right, en passant
square and candidate list over thousands of events; 0 mismatches on 1,500
games.

**Open.** A learned own-clock feature would need a new feature version.

---

## 4. Dataset (`learning/dataset.py`)

**Purpose.** Shards, splits, manifests, minibatches.

**Interface.** `build_dataset(raw, manifest, version)`; shards are gzip JSON
lines of `PlayerEpisode`; `make_batch(episodes, window, rng) -> SequenceBatch`
with full prefixes for burn-in and packed candidates per decision.

**Invariants.** Splits are assigned to whole games before any sequence is
cut; both colours of a game share a split; identical move sequences are
grouped; chronological holdout when timestamps exist. Dense planes are built
per minibatch, never stored.

**Measured.** `v1`: 1,201/150/149 games, 88,371/10,795/10,893 decisions.

**Open.** Opponent/version holdout once there is enough data; the six
regression games must not become a test set.

---

## 5. Simulator and league (`learning/env.py`, `learning/rollouts.py`)

**Purpose.** Fresh games for PPO and for matches, with the referee's rules
and delivery semantics, untimed.

**Interface.** `Game(seed, white, black)` with `deliver()` / `push()` /
`outcome`; players `NeuralPlayer` (batched by the driver), `CaptureGreedyPlayer`,
`UniformRandomPlayer`, `CppEnginePlayer` (node-limited C++ engine through the
C interface). `League.sample()` draws recent / older / fixed opponents by
share. `Collector.collect(target_decisions)` runs games in lockstep, batching
`observe` and `score` per model, and finishes every active game under the same
frozen actor.

**Invariants.** One view per ply to both players; no terminal view; an illegal
move is a forfeit recorded in the stats, never repaired. Learner transitions
are same-player (decision to next decision); the stored log-probability is of
the exact masked categorical that was sampled.

**Decisions.** Correctness-first collection (no episode spans an update, so no
`rollout_cut` in v1; the GAE code handles bootstrapping anyway). Opponent
checkpoints fixed per game; colours alternate by seed.

**Measured.** 600–820 decisions/s with 48 games in flight and neural/fixed
opponents; 45 decisions/s when the C++ engine is the only opponent.

**Open.** A C++ environment for speed; running the TA baselines locally
(their executables are not available).

---

## 6. Model and stage A (`learning/model.py`, `learning/pretrain.py`)

**Purpose.** The recurrent policy and its replay-supervised initialisation.

**Architecture.** 3×3 conv 32→64, four residual blocks (64, no normalisation),
flatten + 8 scalars → 256, `GRUCell(256,256)`. Heads: policy and danger share a
candidate MLP 393→128→64 with separate linear outputs (inputs: hidden,
source/destination spatial features, four coordinates, five promotion
indicators); value 256→128→1 tanh; belief per square 320→64→7. 1,872,394
parameters.

**Objective.** `1.0 CE_policy + 1.0 CE_belief(hidden squares) + 1.0
BCE_danger(over legal moves) + 0.25 MSE_value`, each averaged over its own
valid labels. AdamW 3e-4, wd 1e-4, clip 1.0, 8 sequences × 64 events.

**Invariants.** The hidden state at a window boundary is reconstructed from
the episode's first event under the current parameters without gradients,
then detached; memory is never reset at a sampled cut. Early stopping watches
belief + danger loss, not imitation accuracy.

**Measured (v1, validation/test).** Policy top-1 0.337/0.344; belief hidden
accuracy 0.826/0.828, enemy recall 0.565/0.568; danger Brier 0.044/0.048 at
positive rate 0.053/0.060 with false-negative rate 0.89/0.88 at threshold 0.5;
value MSE 0.95/0.93.

**Open.** A danger calibrator and operating threshold; the value head is near
chance at this data scale; mixed precision not yet enabled.

---

## 7. Recurrent PPO (`learning/train_ppo.py`)

**Purpose.** Improve the policy with fresh simulator games.

**Objective.** `-mean(min(ρA, clip(ρ, 0.8, 1.2) A)) + 0.5 L_value − 0.01 H +
0.1 L_belief + 0.1 L_danger`; GAE γ=1, λ=0.95 over same-player transitions;
advantages normalised per batch; entropy over legal candidates only; early
stop at KL 0.02. Adam 1e-4, clip 0.5, two epochs, 8,192 decisions per batch.

**Invariants.** Replays never enter the ratio. Prefix reconstruction as in
stage A. League: new actor becomes "recent", previous recent moves to "older",
oldest dropped beyond six.

**Measured.** Six iterations: league score 0.49 → 0.54; vs node-limited C++
in rollouts 2/22 → 10/36 wins; PPO − pretrained in 30-pair matches +0.10
(capture-greedy) and +0.03 (cpp:20000), intervals include zero.

**Open.** A long run; the 200-pair evaluation; the league's share of strong
opponents.

---

## 8. Export (`learning/export.py`)

**Purpose.** Two ONNX graphs and a manifest from one checkpoint.

**Interface.** `observe.onnx` (planes, scalars, hidden → next_hidden, spatial,
belief_logits, value) and `score.onnx` (next_hidden, spatial, candidate
arrays → policy_logits, danger_logits); `model_manifest.json` with checkpoint
and graph hashes, versions, coordinate transform, normalisation constants,
parity result.

**Invariants.** Parity against PyTorch over complete held-out histories at
rtol 1e-4 / atol 1e-5; a failure is reported, never widened.

**Measured.** PASS over 425 decisions, worst difference ≤ 6e-6.

---

## 9. Evaluation (`learning/evaluate.py`)

**Suites.** `tactical` (the six regression games: labels, history
reconstruction, policy probability of the losing move), `model` (the stage A
metrics on validation/test), `match` (simulator, colour-swapped seed pairs,
paired bootstrap, candidate-minus-baseline), `arena` (real clocks through
`referee.py`, candidate mode vs baseline mode), `runtime` (load time,
inference percentiles, peak RSS).

**Measured.** Runtime: 0.020 s load, 0.15 ms p99 inference, 168 MiB peak.
Arena smoke: hybrid 6/6 vs cpp over 3 pairs. Tactical: policy top move
survives in 2/6; Kxf2 in `cxgvxx6h` is the policy's own top move.

**Open.** The promotion gate (200 pairs, per-opponent regressions) has not
been run; offline replay of arena losses (`tools/benchmark_corpus.cc`, and the
probe used in this session) should become a suite.

---

## 10. C++ decision procedure (`engine.*`, `belief.*`, `search.*`, `bot.cc`, `neural_inference.*`)

**Purpose.** Choose a move from the exact legal list under a belief over
hidden boards, within the clock.

**Pipeline per decision.**
1. Exact legal moves from the observation (never rejected by the referee).
2. King-loss probability of every legal move over the whole particle
   population; moves above the tolerance are set aside unless all are.
3. Full search of the likeliest hypothesis ranks the rest; the shortlist is
   its top 6 **plus any moves the population rates safer than anything the
   search kept** (v6 repair) and, in hybrid mode, the policy's top 8 and the 8
   lowest-risk moves, trimmed to 12 rows.
4. Matrix game: rows = shortlisted moves, columns = 8 sampled hypotheses, cell
   = search score + invisible-attack bonus − (king risk × 30,000 + expected
   **exposure**: the opponent's best immediate net capture anywhere after the
   move, averaged over a stride of particles; v2–v10 priced only the moved
   piece's square). **Fatal cells carry the same risk charge** (v6 repair).
   One deadline bounds the whole turn (upstream `f236ad7`); cells shrink with
   the clock rather than being skipped, and a skipped cell gets a node-capped
   one-ply verdict on its own hypothesis. Non-queen promotions are dropped
   unless strictly safer. The per-move clock scales with difficulty (×2 when
   the safest move still carries king risk or the fog is deep, cap 8 s).
5. Regret matching; sample from the mixture.

**Modes.** `cpp` (above), `neural` (sample the policy, no search), `hybrid`
(policy ordering and danger estimates feeding the same pipeline; neural danger
is logged, never a veto).

**Belief.** Particle filter: predict by enumerating the opponent's legal moves
per particle with a plausibility prior (hand constants by default; a learned
conditional logit with per-particle memory of the opponent's last move is
selectable), condition on the view (exact on our own pieces, visible squares
only for theirs, **plus what the visibility rule proves about unseen squares**:
the first unseen square on a ray from our slider and the unseen square in
front of our pawn hold an enemy piece, an unseen pawn-capture square is
empty), **resample from a shuffled pool** (v6 repair; it was degenerate),
rebuild on collapse **keeping our own castling history** (v6 repair) and
placing deduced pieces first. KPI: the benchmark's calibration lines (hidden
enemy piece mass; true attacker held at fatal plies).

**Search.** Alpha-beta with the referee's terminal rule, asymmetric win/loss
scores, **no stand-pat under a king attack** (v6 repair), transposition
entries **keyed by fog context** (v6 repair), en passant inferred across the
**correct pair of views** (v6 repair).

**Invariants.** Every emitted move is in the observation-derived legal list.
Model failure of any kind falls back to `cpp` for the rest of the game.
One recurrent update per real view; scoring only at the clock.

**Measured.** 6.6 M nps; arena v6: see `fable-submissions/README.md`. Offline replay
of arena loss `1sv22xki` at ply 40: before the fatal-cell repair one seed in
four chose a 100%-risk move over a 33%-risk one; after it all four choose the
safest move.

**Open.** The belief is the binding constraint: in `ye9uvzr9` the population
rated several truly fatal moves at 0% risk, and in `1sv22xki` 26% where the
truth was 100%. Candidates: a learned opponent-move prior (cheap, per
particle), more particles where the clock allows, and the danger head as a
tie-breaker once calibrated. The risk price and tolerance remain hand-set.

---

## Cross-cutting decisions

- **Information boundary.** Truth reaches labels, the referee and evaluation
  only; actor records, model inputs and the C++ adapter never see it.
- **Determinism for tests.** Node budgets, seeds, fixed particle counts; a
  single-seed assertion is treated as unmeasured.
- **Versioning.** Feature and action versions are strings carried in the
  dataset manifest, the checkpoint and the model manifest; the C++ adapter
  logs them at start.
- **Arena constraints.** 2 cores / 4 threads, 4 GiB, 15 s init, no network;
  one inference thread; nothing learned or downloaded during play.

## Visibility deductions as an option, and the two-ply hidden threat (2026-10-07 evening)

**Deductions** (`EngineOptions::visibility_deductions`, default on; `FOW_VISIBILITY_DEDUCTIONS=0` off). `DeduceFromObservation` now proves only the pawn facts: the unseen square in front of one of our pawns (or two in front, when the first is visibly empty and the pawn is on its start rank) holds an enemy piece, and an unseen pawn-capture square is empty. Nothing is deduced from sliders, knights or the king: every square they could move to, empty or enemy-occupied, is a destination and therefore visible, so the first version's slider-ray rule could never fire (Astra's review). With the pawn rules every particle renders the full observed view exactly (Astra: 36% → 100% on bluqrpex). Balanced benchmark, both arms from one binary: true attacker held at the fatal ply 0.191 → 0.228, material left en prise 8.21% → 7.70%, survival of the real fatal ply unchanged once seeds are averaged (352 vs 351 of 634).

**Two-ply hidden threat** (`Engine::ExpectedHiddenThreat`, weight `FOW_HIDDEN_THREAT`, default 0). The one-ply terms price what a hidden attacker can take *now*; the search prices deeper lines but lets us answer a move we would never observe. This term closes that gap at the root: for a stride of the population, after our candidate move, the opponent gets one quiet move to a square our post-move view does not show (king moves excluded, captures excluded as one-ply business), and the best net capture that leaves them, beyond what they can already take, is averaged and charged with the weight. It targets the duck pattern (hidden sliders arriving on open lines, queen sorties hit from the fog). Cost: one move generation per sampled particle per quiet reply, so the stride defaults to 16. Measured with a true-board oracle metric: decisions leaving a ≥3-point two-ply hidden threat fall from 11.74% (real players 9.60%) to 8.34% at weight 0.5 and 7.35% at weight 1.0, with the one-ply metrics unchanged; default weight 1.0 from 2026-10-07 20:03 UTC, real-clock lanes pending.
