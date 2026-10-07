# v6 — engine repairs and the replay-learning / PPO / hybrid pipeline (candidate)

Commit: see `git log`. Implements the Astra specification (replay learning →
recurrent PPO → ONNX deployment, with an optional hybrid player) and repairs the
three search/belief bugs recorded in the v5 handoff. Nothing here is a strength
claim; the measurements below say exactly what was and was not shown.

## The three repairs (M0)

| bug | fix | regression test |
|---|---|---|
| Quiescence stand-pat while the king is attacked (+978 reported for a +28998 position) | a threatened king has no stand-pat; all moves are searched and no move means a loss | `search_test: ThreatenedKingHasNoStandPat` |
| Transposition entries reused across fog contexts (−26 vs −43 from a fresh table) | a hash of the fog context and win magnitude is XORed into the table key | `search_test: TranspositionEntriesAreContextSpecific` |
| En passant lost in `Engine::Observe` (30 legal moves where the referee had 31) | the engine keeps the two latest views and infers across the pair bracketing the opponent's move | `engine_test: InfersEnPassantAcrossTheOpponentsMove` |

Search speed after the quiescence change: 6.6 M nps vs 6.3 M before on this
machine, depth 11 vs 12 in four seconds from the opening (the evasion search
makes the tree a little larger). All 30,100 differential checks against
`referee.py` still agree.

The multi-seed version of the `92of99z7` regression showed that the earlier
single-seed assertion on "risk seen" was seed-dependent in both the old and the
new code (seed 4 reported zero risk before the change too); the test now asserts
the contract across four seeds: the queen grab is never played, and the risk
term fires in at least one of them.

## Two more repairs found by the pipeline

| bug | fix | regression test |
|---|---|---|
| Rebuilt populations restored our own forfeited castling rights (an illegal `e1g1` in a simulator game) | own rights tracked from our own history, sticky | `belief_test: RecoveryKeepsLostCastlingRightsLost` |
| Systematic resampling picked the same successor offset in every particle's block, collapsing the population to one trajectory | the pool is visited in a random order before the stratified draw | `belief_test: BeliefMaintainsItsInvariants` (collapses 28 → 19, truth in population 565 → 621) |

The second one matters more than anything else in this version: every earlier
measurement of the engine was made on a belief that held a single hypothesis.
See `HANDOFF.md`, "Measured", for what the repaired posterior looks like on the
92of99z7 position and why that regression test's contract changed.

## What was built (M1–M5)

- `rules_capi.cc` + `learning/rules.py`: the C++ rules, observations, en passant
  inference and the engine itself, through a C interface, so the Python side
  never carries a second copy of the rules. Differential-tested against
  `referee.py` including the draw rules and the repetition key.
- `learning/`: API client, ingest with validation and quarantine, per-player
  histories with the three-phase event machine, features (32 planes + 8
  scalars), labels, dataset shards and splits, the CNN/GRU/four-head model
  (1,872,394 parameters, the specification's estimate exactly), stage A
  pretraining, ONNX export with parity, the simulator, the league collector,
  recurrent PPO, and the evaluation suites.
- `neural_observation.*`, `neural_inference.*`: the C++ tracker (exact parity
  with the Python one over thousands of events) and the ONNX Runtime adapter;
  `bot.cc` feeds every real observation once and scores only at the clock;
  `engine.*` gains `cpp`, `neural` and `hybrid` modes.

## Measurements

See the "Measured" section of `HANDOFF.md` for the numbers from this session
(dataset counts, stage A validation metrics, export parity, runtime, the
tactical corpus, and the simulator/arena matches), and `data/reports/` for the
JSON reports they come from.
