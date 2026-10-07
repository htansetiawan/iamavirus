# Session handoff

Written 2026-10-07 for a fresh session, including one on a different machine,
and updated the same day after the neural pipeline was implemented (v6).
Read this before changing anything; a good deal of it is the result of being wrong
several times and it will save repeating that.

## What changed in v6 (read this first)

The three bugs listed below are **fixed and regression-tested**, and the Astra
specification is implemented end to end: `learning/` (replay collection,
validation, histories, features, dataset, CNN/GRU model, stage A pretraining,
ONNX export with parity, simulator, league rollouts, recurrent PPO, evaluation
suites) and the C++ side (`rules_capi.cc` exposing the rules to Python,
`neural_observation.*`, `neural_inference.*`, and `cpp`/`neural`/`hybrid` modes
in `engine.*` and `bot.cc`). The runbook is `learning/README.md`; the version
note is `versions/v6-neural.md`; the numbers from this session are in the
"Measured" section at the end of this file.

## Where things are

| what | where |
|---|---|
| engine source (the submission) | this repository, root |
| per-version record | [versions/](versions/) |
| measurement tools | [harness/](harness/) |
| real-game corpus | [corpus/corpus-all.txt](corpus/) |
| design notes | [ENGINE.md](ENGINE.md) |
| learning pipeline and runbook | [learning/README.md](learning/README.md) |
| raw replays, datasets, checkpoints, releases | `data/`, `checkpoints/`, `releases/` (local only, git-ignored) |
| course starter kit | **not vendored** — GPL-2.0; `https://www.mit.edu/~6.7980/fow/starter/starter.zip`, kept at `~/git/fow-starter` on this machine |
| ONNX Runtime C++ SDK 1.24.2 | `~/git/onnxruntime-sdk/onnxruntime-linux-x64-1.24.2` locally (`ORT_HOME`); `/opt/onnxruntime` in the arena |

The arena ZIP is produced by `bash package.sh <out.zip>`. It deliberately
excludes the compiled binary: the course builds for Linux amd64 and the rules warn
against uploading a host executable.

## Current state

Arena Elo **1468** over 33 games (12W–21L). Leaders are near **2100**, so the gap
is about 650 Elo. We sit below both TA baselines.

Submitted: `5e0ef63` (v4). Committed but **not submitted**: `ff87bb3` (v5), because
its aggregate benchmark did not improve even though it robustly closed a specific
exploit. See [versions/v5-opponent-prior.md](versions/v5-opponent-prior.md).

## What is proven, and what is not

**Proven.** The C++ rewrite (44 k → 11 M nodes/sec; depth 6 → 12), exact rules
conformance (47,875/47,875 differential checks against `referee.py`), and two
belief-filter correctness bugs caught by tests written before the fix.

**Not proven.** Every strategic heuristic. Six were added with nineteen
hand-picked constants; none has been shown to improve playing strength at a
resolution the measurement could support. Two measured negative.

Do not treat any evaluation weight in this engine as validated.

## Three known bugs — fixed in v6

All three were verified locally with probes, and all three corrupted the search
and would have corrupted any training labels derived from it. Each now has a
regression test (`tests/search_test.cc`, `tests/engine_test.cc`); the original
descriptions are kept because they explain the tests.

1. **Quiescence stand-pat while the king is attacked.** At a quiescence node where
   the side to move's king is attacked and no capture escapes, "standing still" is
   treated as available. Measured: after `Qg7` in `7k/8/5K2/8/8/8/8/6Q1 w`, depth 1
   returns **+978** where depth 2+ returns **+28998**. A 28,000 cp error at the
   horizon, and it is symmetric — it also under-weights the opponent's attacks on
   our king.
2. **Transposition entries reused across fog contexts.** `SetContext` changes the
   fog term, but `Probe` matches on the board key alone and `NewGeneration` only
   affects replacement. Measured: same table after a context change returns −26
   where a fresh table returns −43.
3. **En passant lost in the engine integration.** `Engine::Observe` overwrites
   `previous_view_` with the current observation before `ChooseMove` compares them,
   so the inference always sees two identical views. Measured: 30 legal moves where
   the referee has 31, missing `e5d6`.

Bug 3 is a cautionary tale: the en-passant *helper* passes 100% of the conformance
checks while its *caller* is broken. Test the integration, not just the component.

Fixes: a threatened king has no stand-pat in quiescence (all moves searched, no
move is a loss); a hash of the fog context is XORed into the transposition key;
the engine keeps the two latest views and infers en passant across the pair
that brackets the opponent's move.

## How to measure anything here

Read [versions/MEASUREMENT.md](versions/MEASUREMENT.md) first. The short version:

- **Run `harness/selftest.py` before trusting the harness.** A configuration
  against itself must score 0.500. This was never run for the first four versions.
- **Use `FOW_NODE_BUDGET`.** The engine is time-limited, so its strength varies
  with machine load; node limits make results reproducible and let every core be
  used. Especially important on a GPU box where training will compete for CPU.
- **Prefer the offline benchmark** (`tools/benchmark_corpus.cc`) over self-play.
  It gives thousands of ground-truth-labelled decisions from opponents hundreds of
  Elo stronger, where self-play is nearly blind to a flaw both sides share.
- **Match the experiment to the effect.** +100 Elo needs ~50 games; +15 needs
  ~2,100. At 650 Elo behind, chase structural changes, not constants.
- **Sweep seeds.** A single-seed regression test passed by luck for a fix that was
  a coin flip (7/15 across seed and population combinations).

## The failure family that matters

Five rated losses share one cause: the king moving onto, or capturing on, a square
covered from beyond the fog — `qp6mfacx`, `z6mbi981`, `cxgvxx6h`, `rz89dmpy`,
`92of99z7`, across three different opponents, twice by the top-rated team in both
colours. One bug, five times. Any candidate should be checked against all five.

## Plan, and the reordering of the neural specification

(Written before v6. The bug fixes and the Astra stages A, B and the hybrid are
now implemented; the learned opponent prior for the particle filter, step two
below, is still the open idea and is deliberately *not* done by the belief head,
which the specification forbids multiplying into the filter.)

Astra's specification (replay learning → recurrent PPO → hybrid deployment) is
sound and careful; the sections on the information boundary, frame alignment, the
observation event state machine, and evaluation discipline are all correct and
worth following closely. Two substantive disagreements:

1. **In its version 1 the belief head does not affect play** (it is described as
   representation learning and diagnostics), and the danger head approximates
   something the engine already computes *exactly* over 2,048 hypotheses in ~2 ms.
   So the only head changing decisions is policy ordering, which for an 11 M nps
   search is a modest gain.
2. **It never wires a learned opponent model into the particle filter's prior.**
   That is the function hand-coded in v5 as `×0.06 / ×2.5 / ×3.0`, and it is what
   closed the Greek Gift trap 13/15 where three decision-rule attempts failed. It
   is also the one assumption *measured* to be the binding constraint.

Suggested order:

| step | needs GPU? | why first |
|---|---|---|
| fix the three bugs above | no | they corrupt the search and every training label derived from it |
| learn `P(opponent move \| observation)` cheaply and wire it into the belief prior | **no** | replaces five hand-tuned constants; targets the measured weakest link |
| Astra's Stage A (CNN+GRU, four heads) | yes, ~minutes | policy ordering and a calibrated danger estimate for the hybrid |
| Stage B recurrent PPO | GPU barely helps — **simulator-bound on CPU** | last resort; the course states superhuman is reachable without end-to-end deep RL |

**A hard computational constraint on the second step:** the prior is evaluated
*per particle*. With the big CNN that is `2048 × 2–4 ms ≈ 5.8 s per ply`,
infeasible. It must be a cheap model — logistic regression or a tiny MLP on
handcrafted features, microseconds — not the 42 MFLOP network.

## Measured in the v6 session (2026-10-07)

From the reports in `data/reports/` and the logs under `checkpoints/`. Every
number is from this machine, one session, small samples; none is a strength
claim against the arena's opponents.

**Rules and data.** 30,100/30,100 and 18,625/18,625 differential checks against
`referee.py` (two runs), plus the Python binding's own differential test
including the draw rules and the repetition key. 1,500 public replays ingested
(IAmAVirus's 68, the 164-seat corpus, and 1,296 recent games across all teams);
**0 quarantined**: every frame reproduced exactly, and every decision's
observation-derived legal list matched the referee's (0 candidate mismatches).
Dataset `v1`: 1,201 / 150 / 149 games (train / validation / test, by game,
duplicates grouped, chronological holdout), 88,371 / 10,795 / 10,893 decisions.

**Stage A (10 epochs, ~3 min each on the RTX PRO 5000, batch 8 × 64 events).**
Validation / test: policy accuracy 0.337 / 0.344 (entropy 2.37); belief
hidden-square accuracy 0.826 / 0.828, enemy recall 0.565 / 0.568; king-danger
Brier 0.044 / 0.048 at a positive rate of 0.053 / 0.060, false-negative rate at
the 0.5 threshold 0.89 / 0.88 (the head is calibrated-ish but not sharp: a
calibrator and a lower operating threshold are needed before it can veto
anything); value MSE 0.95 / 0.93 (near chance; returns are weakly predictable
from a single history at this data scale). `data/reports/v1-model.json`.

**Export.** Release `v1` (pretrained) and `v2-ppo`: ONNX/PyTorch parity PASS
over 425 held-out decisions, worst absolute difference ≤ 6e-6 on every output.

**Runtime (real referee, 180+2, neural mode).** Model load 0.020 s; inference
p50 0.13 ms, p99 0.15 ms per decision; peak RSS of the hybrid bot on a
scripted turn 168 MiB (transposition table included). Far inside the 15 s /
100 ms / 3 GiB targets. The search-free neural bot won 1 of 2 such games
against `baseline.py`. `data/reports/v1-runtime.json`.

**Tactical corpus (six losing games, our seat).** Danger labels and history
reconstruction validate on all six with zero candidate mismatches. Policy
probability on the recorded losing move, pretrained → PPO: `cxgvxx6h` 0.53 →
0.59 (Kxf2 is also the policy's top move: the replay data itself plays into
hidden protection), `rz89dmpy` 0.08 → 0.07, `92of99z7` 0.28 → 0.26,
`ky4pm8o2` 0.03 → 0.03, `gxmut7rr` 0.02 → 0.02, `zviidq21` 0.03 → 0.04. The
policy's top move survives the true board in 2 of 6. The danger head's
estimate on the losing move ranges 0.03–0.41. Reports:
`data/reports/v1-tactical.json`, `data/reports/ppo-tactical.json`.

**Stage B (6 iterations × ~8,900 decisions, league = recent/older checkpoints
+ capture-greedy + uniform-random + cpp at 20k nodes).** Throughput 600–820
learner decisions/s with 48 games in flight (45 dec/s when the C++ engine is
the only opponent, since it runs sequentially); every iteration early-stopped
at KL 0.02–0.04 after a few updates. Rollout score vs the league 0.49 → 0.54.
Against the node-limited C++ engine inside the rollouts: 2/22 wins at
iteration 0, 10/36 at iteration 5.

**Simulator comparison, PPO minus pretrained, 30 colour-swapped seed pairs per
opponent (paired bootstrap 95%).** vs capture-greedy: +0.10 [−0.07, +0.27]
(PPO scores 0.72); vs cpp:20000: +0.03 [−0.08, +0.15] (PPO scores 0.17).
**Inconclusive**, as expected at this size; the spec's 200-pair final
evaluation was not run. `data/reports/ppo-vs-pretrain-match.json`.

**Arena-like comparison (real 180+2 clocks through `referee.py`, this machine,
hybrid release v1 vs the repaired cpp bot, 3 colour-swapped seed pairs).** The
hybrid won **6 of 6** games against cpp (as White and as Black, all by king
capture, 44–93 plies); the baseline arm (cpp vs cpp with the same seeds) scored
2 of 6. Paired candidate-minus-baseline +0.67, bootstrap interval [0.50, 1.00]
over only three pairs, so it is a smoke result, not the promotion gate: the
specification's 200-pair evaluation across opponents has not been run, and
the hybrid's candidate union (search top 6 + policy top 8 + lowest-risk top 8,
trimmed to 12 rows) has not been ablated. `data/reports/v1-arena-hybrid.json`;
the twelve replays are in `data/arena/`.

**Two more engine bugs found by the pipeline, both fixed with tests.**
(1) `BeliefState::Recover` rebuilt *our own* castling rights from the board,
restoring a right the king had forfeited by moving away and back; the C++
engine played an illegal `e1g1` as a simulator opponent. Own rights are now
tracked from our own history (sticky). (2) **Systematic resampling was
degenerate:** the successor pool is particle-major and each particle's block
carries exactly one unit of mass, so a stride of one unit selected the same
offset in every block. From identical particles the filter chose the same
hidden move for every particle, i.e. the population was a single trajectory
until a collapse forced a random rebuild. Shuffling the pool fixes it:
invariants test truth-in-population 565 → 621 of 1,444 plies, collapses
28 → 19, pieces placed 74.6% → 77.5%. **Consequence:** the 92of99z7 regression
had been passing on that degenerate population. With a real posterior (hidden
knight on c3 in 5–22% of hypotheses, d5 guarded in 17–46%) the verdict is
marginal: at 512 particles with a 0.5 s clock the engine took the pawn in 2 of
8 seeds; at 1,024 particles with a 400k-node budget (the upstream commit's
parameters) it declines in 8 of 8. A ~20% chance of losing the queen is priced
at ~160 cp against a pawn plus the evaluation's positional terms. The test now
uses the node-limited setting and pins the measured contract (posterior
informative in 8/8, risk term fires in 8/8, grab declined in 8/8). Every v2–v5
measurement was made with the degenerate filter and should be treated as
unmeasured.

**Two repairs from the first arena losses of v6 (v6.1).** Replaying
`1sv22xki` through the engine at ply 40 (our king attacked by a queen on f2,
hidden bishop on c5 covering it): the particle risk of the three king moves
was 26–77% and every other move 100%, yet one seed in four played a
100%-risk rook move. The matrix cells for an outright loss scored a flat
−30,000 with no risk charge, while the probable escapes scored their search
value minus the charge (≈ −39,900), so the certain loss *outranked* them.
Fatal cells now carry the charge, and moves the population rates safer than
anything the search shortlisted are appended as rows. After the fix all four
seeds choose the safest measured move there, and in `j8zn0ugw` ply 46 (a
25/26-safe position where v6 played the one fatal move) all four seeds avoid
it. The remaining v6 losses (`7tkm78ho` ply 45, `6blt5n5j` ply 60) are belief
failures: the population rated the fatal move at 0% risk, and the repaired
engine repeats it in 2 of 4 seeds.

**What this means for the next step.** The engine's remaining weakness in the
regression family is a *pricing* problem on a now-honest posterior, and the
hybrid mode is where the learned signals meet it: neural danger is logged
beside particle risk for every candidate (`cands=uci:policy/danger/particle`
in the stderr line), but it only orders and tie-breaks until a calibrator
and a veto evaluation exist. Stage B needs a far longer run and the 200-pair
evaluation before any mode other than `cpp` earns release.

## GPU machine checklist

- Clone this repository. Download the course starter kit separately and create its
  virtual environment (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).
- **Install a real GCC.** The course builds with g++ 12 and libstdc++; Apple clang
  with libc++ pulls in headers that libstdc++ does not, and a submission once
  failed to build for exactly that reason (bare `size_t` in `regret.h`). 19 files
  needed explicit headers. If the machine is already Linux with g++, this is moot.
- `bash build.sh && bash test.sh` must pass before anything else.
- Set `FOW_PYTHON` to the kit's venv python and `FOW_KIT` to a directory holding
  `referee.py` and `vision.py` to enable the differential test.
- Training data: `corpus/corpus-all.txt` is already here, and
  `python -m learning.ingest` collects and validates full replays (paced at one
  request per second, with backoff). `harness/corpus_download.py` is the older
  move-list downloader.
- `uv venv .venv --python 3.12` in the repository and install torch (cu128),
  numpy, onnx, onnxruntime, pyyaml, pytest, chess==1.11.2; see `learning/README.md`.

## What not to redo

- Do not re-derive the exact-legal-move argument; it is settled and is why an
  illegal-move forfeit is structurally impossible.
- Do not re-benchmark against `baseline.py`. It is Elo 1000, we beat it 10–0, and
  it cannot separate strong configurations.
- Do not re-run the duplicate-game investigation. 32/32 games were distinct; the
  error bars were honest.
- Do not try to fix the Greek Gift trap with another decision rule. Three were
  tried (threshold, band, continuous price); the problem is the belief, not the
  rule.
- Do not use the public API to submit. It is read-only; the arena's own
  `/api/submissions` is token-authenticated and undocumented, and the token must
  never go into source or a ZIP.

## Honest framing for the next session

The user's own critique is worth carrying forward: this had become heuristics
piled on heuristics, with hand-fitted constants estimating quantities that could be
learned from the ~3.9 M real labelled decisions the public API exposes. The
measurement work was necessary groundwork, but it is not progress by itself. The
next real gain is either the three bug fixes or a learned opponent model — not
another constant.
