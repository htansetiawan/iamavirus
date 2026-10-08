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
- **Corpora are tracked (force-added under the ignored `data/`)**: `data/benchmark-seats.txt` (634 real losing seats, the fatal-ply corpus every gate uses; one line per seat: `id side result reason opponent moves…`) and `data/queen-loss-seats.txt` (240 arena decisions after which our queen was captured for less, each game truncated after our move and marked as our fatal ply, so `build/benchmark_queen data/queen-loss-seats.txt 1000 400000` evaluates exactly those decisions plus each seat's first move). Neither has a generator script in the repo; the queen corpus was built from `data/raw/games/*/replay.json` true boards with the rule in the 02:50 UTC HANDOFF entry. Rebuild `benchmark_queen` from `tools/benchmark_corpus.cc` after engine edits.


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

**Correction (17:55 UTC, from Astra's review).** The archived v5 bytes already
contain the upstream turn deadline (`matrix_deadline`, `cells_skipped` in
`fable-submissions/iamavirus-v6-hybrid.zip`), so the deadline cannot explain
the v5 → v8 decline. In hybrid mode v8's safety rows were inert (the union
took only the search's first six rows; fixed in v10), leaving the fatal-cell
risk charge as the only effective difference, which acts only when every
candidate carries risk. The v8 record (9W–15L; 50.0% vs 70.8% on shared
opponents) is best explained by schedule and sample size. The cells-shrink /
node-capped-fallback change in v9/v10 remains a robustness improvement, not a
regression fix. The arbiter is the paired archived-v5 vs v9 run.

**Paired real-clock comparison, v9 vs archived v5 (18:30 UTC):** 8W–1D–9L over
18 colour-swapped games on two pinned cores, score 0.472. No difference; the
v5 → v8 → v9 arena swings were schedule and sample size.

**Exposure term (18:05 UTC).** The gold data (`gold/`, 369 games, 11,893
decisions; `reports/IAmAVirus replay analysis.md`, `reports/Lessons from the
duck games.md`) showed 90% of material lost goes to a hidden capturer, mostly
not the moved piece, and the engine's material-risk term priced only the
moved piece's destination. `Engine::ExpectedExposure` prices the opponent's
best immediate net capture anywhere, averaged over a stride of particles.
Offline benchmark, 634 real losing seats, same seed and node budget:
**left ≥3 points en prise 7.83% (new) vs 10.10% (old)**, real players 7.75%;
immediate king losses 6.55% in both; survival 58% in both. Candidate archive
`fable-submissions/iamavirus-v11-hybrid.zip`.

**Arena v10 losing streak (18:36–18:54 UTC): 7 losses in 8 games, five to
duck.** Dissected: the same shapes (hidden far-half captures of the queen/rook;
voluntary king walks into hidden attacks with 18/19 and 14/15 safe moves
available). Replayed offline through the current build (deductions +
exposure), the three decisive moves are avoided in 4 of 4 seeds each
(`x31dyp8z` ply 89, `dlc6932d` ply 92, `i8cjpfmc` ply 38). Weight sweep with
deductions so far: w=1.0 king losses 7.02%, en prise 6.76%, hidden piece mass
0.540, attacker held 0.228; w=1.5 en prise 6.46%, king losses unchanged. The
rise in immediate king losses from 6.55% (pre-deduction) to 7.02% is under
investigation (verbose diff of flipped fatal positions running).

**Visibility deductions (19:40 UTC).** The filter now enforces what the
visibility rule proves about unseen squares (`DeduceFromObservation`): the
first unseen square on a ray from our slider, and the unseen square in front
of our pawn, hold an enemy piece; an unseen pawn-capture square is empty.
Invariants test: truth in population 621 → 805 of 1,444 plies, collapses
19 → 14, pieces placed 77.5% → 79.6%. Consequence for the 92of99z7 test: the
population no longer collapses at ply 6 of that line (403 survivors vs 44),
the honest posterior puts d5 guarded at 15–22%, and the pawn grab becomes
EV-marginal (3 of 8 seeds take it); the material-risk weight is being swept
on the benchmark. The Greek Gift test moved one decision earlier: after
8. Bxc4 the engine keeps an answer to Bf7+ in 6 of 6 seeds, and the belief
holds a White piece on e5 (the e7 pawn's blocked double push proves it).

**Belief calibration (19:30 UTC, 634 seats, pre-deduction binary):** hidden
enemy piece mass 0.475 (hand prior) vs 0.513 (learned prior with memory);
true attacker held at the fatal plies 0.191 vs 0.199. The learned prior
places hidden pieces slightly better; decisions are within noise either way.

**Learned prior with memory (19:10 UTC, same seats, exposure on):** king
losses 6.72%, left ≥3 en prise 7.62%, survival 56% — against 6.55% / 7.83% /
58% for the hand prior. Mixed and within noise; the hand prior stays the
default. Whether the memory prior holds hidden pieces better is what the
calibration runs will say.

**Sensitivity (19:00 UTC, same 634 seats).** 4,096 particles: king losses
6.53%, left ≥3 en prise 7.53% (vs 6.55% / 7.83% at 2,048): a small gain at
twice the belief cost. Exposure stride 2 vs 4: identical. **Belief
calibration metric** added to the benchmark: the particle share holding each
hidden enemy piece on its true square ("hidden piece mass"), and at the
recorded fatal plies the share holding the true attacker. Three-seat smoke:
0.305 and 0.053 — the population holds the right hidden piece on the right
square 30% of the time and, when we walked into the attacker, held it in one
particle in twenty. That is the number the belief work has to move.

**What this means for the next step.** The engine's remaining weakness in the
regression family is a *pricing* problem on a now-honest posterior, and the
hybrid mode is where the learned signals meet it: neural danger is logged
beside particle risk for every candidate (`cands=uci:policy/danger/particle`
in the stderr line), but it only orders and tie-breaks until a calibrator
and a veto evaluation exist. Stage B needs a far longer run and the 200-pair
evaluation before any mode other than `cpp` earns release.

### 2026-10-07 19:55 UTC — balanced harness, deduction verdict, candidate for arena v11

- **Harness fix.** `tools/benchmark_corpus.cc` sampled `ply % stride`, i.e. White's decisions only (Astra's review); it now samples `(ply/2) % stride`, every seat's own decisions, and takes `FOW_SEED`. Every percentage recorded before commit `fa61ad4` is a White-biased diagnostic.
- **Both deduction arms from one binary** (634 real losing seats, stride 6, 400k nodes, seed 777, 5,322 decisions):

| arm | immediate king losses | true attacker held at fatal ply | hidden piece mass | left ≥3 en prise (engine / real player) | survives the real fatal ply |
|---|---|---|---|---|---|
| deductions off (= exposure build) | 326 (6.13%) | 0.191 | 0.477 | 8.21% / 8.04% | 368 (58%) |
| deductions on | 344 (6.46%) | 0.228 | 0.532 | 7.70% / 8.04% | 341 (54%) |
| deductions on, `FOW_PIECE_RISK=2.0` | 342 (6.43%) | 0.228 | 0.532 | 7.20% / 8.04% | 341 (54%) |

- **The survival drop is churn.** Fatal-ply-only runs (stride 1000) at seeds 777/778/779: off 368 / 345 / 343, on 341 / 365 / 347 (means 352 vs 351). Between arms the engine's move differs in 136 of the 634 fatal positions (80 flip to a loss, 56 to a survival at seed 777): near-tied decisions, no systematic effect. **Verdict: deductions ship on.** They buy belief honesty and fewer pieces left en prise at no measured cost. Material-risk weight stays 1.0 (2.0 cuts en prise further but is untested at real clocks).
- **Option.** `EngineOptions::visibility_deductions` (default on); `FOW_VISIBILITY_DEDUCTIONS=0` disables (same name and semantics as Astra's copy). `DeduceFromObservation` keeps only the pawn rules; the slider-ray case cannot occur in a valid observation.
- **qyzsbfdc trace** (duck, we were Black, lost in 52): the honest king-loss risk of 19...Kxc6 is zero (the light bishop is pinned by history to d1/c2/b3/e2/g4/h5) but the build priced it 0.00–0.63 across seeds, recovery scatter onto d5/e4; recaptured 1/4. Belief lane (Astra proposes a bounded history enumerator). The fatal 26...Kb8 is avoided 4/4; 17...Nc6 onto the open file is repeated 3/4, a two-ply threat no one-ply term sees.
- **v10 loss sweep** (`data/reports/v10-loss-sweep.txt`): 19 losses, last three decisions × 4 seeds; the current build avoids the fatal move 49/76 times; the 0/4 games are lost endgames (down a queen or more).
- **v10 loss sweep, second batch** (14 newer losses, last three decisions × 4 seeds, current build): fatal move avoided 37/56; by opponent duck 14/16, TA Baseline A 13/16, TA Baseline S 4/8, Decent Chess Bot 4/8, Strongly Invisible 2/4, Apricot 0/4 (a 180-ply endgame: our king stepped next to the unseen White king after 90.Kf4; not a clock problem, 40 s left). Across both batches 86/132 fatal moves are avoided; the misses are lost endgames and unseen-king steps.
- **Arena context** (19:40 UTC): IAmAVirus 1525 Elo (v10 31W–1D–26L); TA Baseline A 1528, TA Baseline S 1708, duck 1909, Instructors 1915, Knight Vision 2065, Greek Gift 2165. v10's records vs TA-A (5–5), TA-S (1–5) and duck (1–9) match those gaps: overall strength, not one hole.
- **Two-ply hidden-threat term** (`Engine::ExpectedHiddenThreat`, `FOW_HIDDEN_THREAT`, default 0 = off, stride `FOW_HIDDEN_THREAT_STRIDE`=16): after our move the opponent gets one quiet move to a square our post-move view does not show, and the best net capture that leaves them, beyond what they can already take, is charged. Unit test: after 1.e4 e5, 2.Qh5 ≫ 2.Nf3. Full-corpus arms at 0.5 and 1.0 running (`data/reports/bench-balanced-off-ht*.txt`).
- **Two-ply term measured** (oracle metric added to the benchmark: after each move, whether the opponent could set up ≥3 points with one quiet move to a square the mover's post-move view does not show, on the true board; deductions on, seed 777, 5,322 decisions):

| `FOW_HIDDEN_THREAT` | left a 2-ply hidden threat | left ≥3 en prise | king losses | survives fatal ply |
|---|---|---|---|---|
| 0 (v11 candidate) | 625 (11.74%) | 7.70% | 6.46% | 341 |
| 0.5 | 444 (8.34%) | 7.70% | 6.44% | 341 |
| 1.0 | 391 (7.35%) | 7.61% | 6.44% | 341 |
| real players | 511 (9.60%) | 8.04% | | |

  The engine was *worse* than the historical bots at this pattern before the term and better after it; the one-ply metrics do not move, and the arms ran in the same 7–8 minutes as the weight-0 arm (stride 16). Default set to 1.0; second candidate `fable-submissions/iamavirus-v11-candidate-twoply-hybrid.zip` (sha 022fd76bb778) built, clean-dir build OK, full suite re-run, two real-clock lanes vs the v11 candidate queued (cores 0–1 and 6–7).
- **The clock is under-used.** Referee diagnostics of 745 candidate decisions at real 180+2 clocks: median depth 10 (p90 12), 28M nodes per decision at 7.2M nodes/s, every decision stopped at the 4 s cap, 0 skipped cells, hard turns 11% at 5.8 s. Arena replays (v5/v9/v10, 115 games): our clock at the end median 121 s, p10 87 s, minimum 40 s (a 180-ply game), no timeouts. Simulation of the budget formula (mean seconds per move / clock left at the end):

| cap / hard cap / divisor | 60 plies | 100 plies | 150 plies | 300 plies |
|---|---|---|---|---|
| 4 / 8 / 30 (shipped) | 4.4 s, 108 s left | 4.4 s, 62 s | 4.0 s, 31 s | 3.1 s, 14 s |
| 7 / 12 / 20 (new default) | 6.1 s, 56 s left | 5.0 s, 29 s | 4.2 s, 18 s | 3.1 s, 14 s |

  Time-based budgets adapt to a slower arena host, so the change costs nodes, not safety.
- **Second core.** The search is single-threaded and the arena gives two cores. The matrix cells (55% of a turn) are independent searches, so `EngineOptions::cell_threads` (default 2, `FOW_CELL_THREADS`) splits columns across two threads with separate transposition tables and searchers; wall time unchanged, every cell searches twice as long. Suite test `CellThreadsPlayLegalMoves` (whole games, no illegal moves, no overrun); `-pthread` added to build.sh and test.sh; the decision line gains `cells=<seconds>/<threads>`. Together with the clock change a decision should get about twice the nodes.
- **Clock safety**: the full candidate's lowest clock over its 16 lane games was 11 s (per-game minima median 35 s), so `time_reserve` moves 6 → 10 s in the tree; the next packaged archive carries it (the full and caution archives in the lanes still have 6 s).
- **Third candidate** `fable-submissions/iamavirus-v13-hybrid.zip` (arena v13; was `iamavirus-v13-hybrid.zip`) (sha 39fb4480e0b7): the two-ply candidate + clock defaults + two-thread cells. **Real-clock lanes vs the two-ply candidate: 10W–1D–5L over 16 games, paired 0.656, bootstrap 95% 0.406–0.875**, as White 5/8, as Black 6/8, no clock overruns. The first measured real-clock gain; it is the recommended next upload unless the caution lanes beat it.
- **Two-ply at real clocks** vs the plain candidate (arena v12): 7W–2D–7L over 16 games, paired 0.500 (0.281–0.750): even, so the term costs nothing at real clocks and keeps its offline gain; it stays in the full candidate.
- **Colour split** (two-ply configuration, balanced benchmark): as White king losses 5.98%, en prise 6.53% (real player 7.29%), two-ply threats 7.21% (real 8.94%), survives 152/274; as Black 6.82%, 8.47% (real 8.64%), 7.46% (real 10.12%), survives 189/360. Black is harder for the real players by the same margins, so there is no Black-specific defect to chase; the arena colour gap (v10 0.59 vs 0.44) is within what those rates and sample sizes produce.
- **v12's first ten arena games** (5–1–4): losses to Decent Chess Bot ×2 (expected at 2065) and TA Baseline P ×2, a draw vs P. xidde3fz: our king stepped h7–g7 onto the c3–g7 diagonal of an unseen bishop with h6/g8 safe (belief lane: far-half slider). tr0gwrvf: our king walked to g4 beside a queen last seen on e3; she moved to e4 unseen and our next move (Re2, attacking e3) left the king en prise: the king version of the two-ply blindness, now `hidden_king_threat_weight` (off until measured) with a true-board oracle metric. eucmjl12: threefold with a knight for two pawns up; the engine had no notion of repetition, now `repetition_penalty` (120 cp per earlier occurrence of the same view, unless the shortlist score says we are losing by more than 100 cp), with a unit test. Clock was fine (minimum 30 s in a 101-ply game).
- **Why we lose queens** (arena v10, 69 games; capturer visibility judged on the view at our decision, trades excluded):

| | count |
|---|---|
| games in which our queen was captured | 65 of 69 |
| even trades (we recaptured a queen) | 10 |
| real losses (net ≤ −2) | 55 |
| real losses with the capturer **unseen** at our decision | 48 of 55 |
| real losses where **we had just moved the queen onto** the square | 44 of 55 |
| capturer: rook / bishop / knight / pawn / king / queen | 20 / 13 / 10 / 6 / 3 / 3 |
| before ply 30 | 18 of 55 |

  v12 (15 games): captured in 7, 4 trades, 3 real losses (2 to unseen queens, 1 to a visible pawn). The particle terms only see the attacker when the population holds it; these are the cases where it did not. New: `surface_charge` (`FOW_SURFACE`, off until measured), a particle-independent charge per unseen empty square on every ray from the moved piece's destination that an enemy slider of the matching type could occupy, plus unseen knight and pawn-attack squares, scaled by the piece's value; and a benchmark metric "queen left en prise (net ≥ 5)". Arms at 0/10/20/40, and `hidden_king_threat_weight` 0.3/0.6, and 20+0.3, queued on cores 2–5.
- **Queen balance across the arena** (every team, all its games in the raw store; "lost" = our queen captured for a net loss ≥ 2, "won" = theirs captured for a net gain ≥ 2):

| team | games | win% | queen won % | queen lost % | balance | lost before ply 30 |
|---|---|---|---|---|---|---|
| Greek Gift | 1331 | 76 | 57 | 47 | +10 | 101 (8%) |
| Knight Vision | 1339 | 63 | 51 | 46 | +5 | 120 (9%) |
| Strongly Invisible | 751 | 58 | 55 | 45 | +10 | 58 (8%) |
| Decent Chess Bot | 790 | 54 | 56 | 49 | +7 | 30 (4%) |
| duck | 735 | 44 | 60 | 46 | +14 | 67 (9%) |
| Instructors | 671 | 46 | 57 | 49 | +8 | 76 (11%) |
| TA Baseline S | 679 | 43 | 52 | 62 | −10 | 135 (20%) |
| **IAmAVirus** (all versions) | 651 | 35 | 51 | 55 | −4 | **117 (18%)** |
| TA Baseline A | 644 | 40 | 48 | 59 | −11 | 116 (18%) |
| TA Baseline P | 581 | 36 | 45 | 60 | −15 | 116 (20%) |
| Apricot Squad | 530 | 32 | 36 | 42 | −6 | 91 (17%) |

  Queen loss is endemic (the best lose theirs in nearly half their games, mostly to unseen capturers); the balance tracks the ratings, and the separator is *early* losses: 4–9% for the top six, 18% for us. We win queens as often as Knight Vision. So the target is early queen safety: the opening book (top-team lines, `gold/opening-book.json`, 39% coverage of our early decisions) and the surface charge, which bites hardest while most squares are unseen.
- **Caution arms** (balanced 634 seats, deductions on, two-ply 1.0, repetition on, seed 777):

| arm | king losses | en prise | queen en prise | 2-ply material | 2-ply king threat | survives fatal ply |
|---|---|---|---|---|---|---|
| base | 6.37% | 7.63% | 1.43% | 7.27% | 12.72% | 343 |
| surface 10 / 20 / 40 | 6.39 / 6.43 / 6.43% | 7.44 / 7.37 / 7.42% | 1.41 / 1.39 / 1.47% | 7.25 / 7.16 / 7.25% | 12.8 / 13.4 / 13.4% | 343 / 343 / 343 |
| king threat 0.3 / 0.6 | 6.18 / 6.01% | 8.00 / 8.19% | 1.65 / 1.71% | 7.55 / 7.61% | 9.24 / 9.34% | 351 / 362 |
| surface 20 + king 0.3 | 6.20% | 7.80% | 1.58% | 7.46% | 9.28% | 351 |
| real players | | 8.04% | 1.28% | 9.60% | 10.43% | |

  The surface charge barely moves anything at the decision level and stays off (0). The two-ply king threat trades material for king safety; at 0.6 it becomes the default pending the real-clock lane (`iamavirus-v11-candidate-caution-hybrid.zip` = full candidate + repetition charge + king threat 0.6 + opening book).
- **Opening book** (`book.txt`, 176 entries from `gold/opening-book.json` via `learning/book.py`): keyed by colour and the exact observation, first 10 plies, support ≥ 15 games and ≥ 25% share among the six strongest teams; the bot loads it at start-up (`FOW_BOOK=off` disables) and plays the entry when legal; 39% of our early decisions hit it. Unit test: the start view as White answers d2d4.
- **Vision term: null.** At weight 1.0 the engine sees 30.9 squares after its move vs 30.8 at weight 0 (real players 31.1), and every decision metric is flat (king losses 6.41% vs 6.37%, en prise 7.76% vs 7.63%). Shelved at default 0.
- **tr0gwrvf replay**: the current build repeats 42.Kg4 in 3/4 seeds (chosen-move risk 20–79 cp), 43.Rg2 in 4/4 (risk ~250–290) and 44.Re2 in 3/4 (risk 312–375 cp, i.e. it knowingly accepted roughly a 3% chance of losing the king to attack where it believed the queen stood); xidde3fz: the current build avoids 43...Kg7 in 4/4 seeds.
- **Head-to-head, Fable v12 bytes vs Astra v11 bytes** (seeds 5100/5300, cores 2–3/4–5, 180+2): 9W–0D–7L over 16 games, paired 0.562 (0.375–0.750), as White 6/8, as Black 3/8. A modest edge for the fuller build, not significant.
- **Model v3** (stage A on 4,707 games, 10 epochs, `checkpoints/pretrain-v3/best.pt`, release `releases/v3`, ONNX parity PASS on 398 decisions). Same new test split for both models:

| test split of manifest v3 | v1 (shipped) | v3 |
|---|---|---|
| policy top-1 accuracy | 32.7% | 34.5% |
| hidden-square belief accuracy | 82.7% | 83.9% |
| danger Brier | 0.042 | 0.031 |
| danger false-negative rate | 87.5% | 64.7% |
| value loss | 0.955 | 0.887 |

  Tactical suite (probability on the six recorded losing moves): lower on 92of99z7 (0.28 → 0.16) and cxgvxx6h (0.53 → 0.49), slightly higher on the four small ones (0.02–0.08 → 0.06–0.14). Archive `fable-submissions/iamavirus-v11-candidate-full-v3model-hybrid.zip` (sha 519260f77245). **Caveat**: it was packaged from the current tree, so besides the v3 model it carries the caution defaults (king threat 0.6, repetition charge, opening book) and the 10 s reserve; its lanes vs the v13 bytes (L/M, queued) measure the whole next candidate, and the caution lanes (J/K) isolate the caution part.
- **Feature contract defect** (Astra, 22:58 UTC): `learning/features.py` `planes()` writes both the unknown symbol and the visible-empty symbol to plane 12 (`CLASS_EMPTY == 12` and `CLASS_NEVER` is mapped to 12); `neural_observation.cc` line 126 does the same, so parity holds and the models are self-consistent; plane 13 is unused. Fog vs seen-empty remains separable via plane 28 (age 0). Fix for the next retrain: plane 13 for visible empty, `FEATURE_VERSION = "features-v2"`, matching C++ change, parity tests, model manifest check at load; never change the encoder without the matching weights.
- **Opening book, offline** (balanced 634 seats, current defaults, book off vs on): book moves fire on 635 of 1,913 opening decisions (ply < 30); opening queen en prise 0.68% → 0.73% (real players 1.05%), opening en prise 2.72% → 2.82% (real 4.70%); overall king losses 6.01% → 5.98%, survival 362 → 364, matched real move 22.7% → 24.7%. Neutral on one-ply metrics, as a book would be; the real-clock lanes of the caution package (which carries it) are its evidence.
- **Caution package at real clocks** vs the v13 bytes (lanes J/K, seeds 6100/6300, cores 0–1/6–7): **12W–1D–3L over 16 games, paired 0.781, bootstrap 95% 0.562–0.938**, as White 6/8, as Black 6/8. The second real-clock gain of the night on top of v13. Lowest clock 11 s in a 112-ply game → the v14 candidate is the same engine with `time_reserve` 10 s (`iamavirus-v11-candidate-caution-r10-hybrid.zip`, sha 93f4ccdf03d5), 2-pair smoke vs v13 running.
- **v13 in the arena, first 14 games** (7–1–6): wins vs Apricot ×4, baseline ×2, TA-S ×1; draw vs TA-S; losses vs TA-S ×2, TA-P ×2, Strongly Invisible ×2. Lowest clock 14 s (133 plies), no timeout of ours (the one "time forfeit" was Apricot's). **Pattern to watch:** v12 and v13 are 1–4 combined against TA Baseline P (rating 1455), which v10 beat 6–0. tre2jzfk: our king stepped d8→e8 onto the diagonal of a bishop that had just moved d3→g6 unseen (the king-loss term needs the particles to hold the bishop; the two-ply king term guards the king's current square, not its destination). twlle83q: a 15-point collapse between plies 30 and 40, replay running.
- **twlle83q (White vs TA Baseline P, lost; 15 points gone between plies 30 and 40)**: 18.Nc3–e4 was taken by a knight on f6 we had never seen; e4 then showed as unseen (nothing of ours attacks it), and the engine went on as if e4 were empty: 19.Qd2–a5 was taken by the hidden queen along the open d8–a5 diagonal, 20.Bc1–d2 by the same knight from e4. The belief lacked **capture evidence**: when our piece vanishes from an unseen square, the capturer is standing there until it moves. Astra implemented that in its copy (commit 79564d0, "preserve capture evidence"); it is not in root. Port it next. Note: replays through the root bot now run in cpp mode until a features-v2 model (v4) exists, because root refuses features-v1 models.
- **Capture evidence ported into root** (`c77f5db`, from Astra's 79564d0): `BeliefState::InferCaptureEvidence` marks the square where exactly one of our pieces vanished unseen (not an en passant victim); recovery places an enemy piece there; cleared at the next opponent move or when we take the capturer. `EngineOptions::capture_evidence` default on, `FOW_CAPTURE_EVIDENCE=0` off. Test over eight seeds with a one-particle population (3.Nxe5 Nxe5, e5 unseen). Belief suite 504 checks, engine suite 622 checks. Benchmark arms off/on running; it goes into the next archive after v14.
- **v14 cleared** (23:58 UTC): `iamavirus-v11-candidate-caution-r10-hybrid.zip` (sha 93f4ccdf03d5) smoke vs v13 2.5/4 at real clocks, no budget overruns, lowest clock 14 s in a 164-ply game (the budget formula's floor is about reserve + 4 s). Recommended to the user as arena v14; rename on upload.
- **Capture evidence arms** (balanced 634 seats, book off, otherwise current defaults): off → on: king losses 320 → 315 (6.01 → 5.92%), true attacker held at the fatal ply 0.228 → 0.235, survival 362 → 362, en prise 8.19 → 8.32%, queen en prise 1.71 → 1.65%, two-ply threats 7.61 → 7.85%. Within churn: the constraint acts only on a collapse right after an unseen capture, a handful of the 5,322 decisions; the off arm reproduces the earlier same-defaults arm exactly. Kept on; the twlle83q replay is the targeted evidence.
- **v3 model at real clocks** (caution engine + 10 s reserve + v3 vs the v13 bytes): lane M 3.5/8 (0.438, 0.312–0.5), as Black 0.5/4; lane L stopped after two repetition draws to free the cores. The identical engine with the v1 model scored 0.781 on this gate, so the v3 model (better on every offline metric) plays worse in the hybrid: a reminder that the model suite is not a strength gate. v4 is judged the same way (lanes P/Q, capture-plus-v4 archive vs the v14 bytes).
- **Capture persistence arm** (recent capture squares kept through rebuilds at 0.85/0.70 for two updates): king losses 5.77%, true attacker held 0.239, en prise 8.29%, survival 370, versus capture-on 5.92% / 0.235 / 8.32% / 362 and off 6.01% / 0.228 / 8.19% / 362. twlle83q re-read with the rebuilt bot: the ply-39 bishop move was an even knight trade (the engine's zero risk is arithmetic); the losses were the queen onto the hidden queen's diagonal at ply 37 (belief scatter, Astra's lane) and the rook left to the inferred queen at ply 43; persistence targets the latter.
- **Model v4** (features-v2, warm-started from v3 by copying stem input column 12 to 13, trained 23:24–00:30 on manifest v4 = the same 4,707 games re-featurised; ONNX parity PASS, worst abs diff 8e-6). Same test games, each model on its own encoding:

| test split | v1 | v3 | v4 |
|---|---|---|---|
| policy top-1 | 32.7% | 34.5% | 35.5% |
| hidden-square belief accuracy | 82.7% | 83.9% | 84.4% |
| danger Brier | 0.042 | 0.031 | 0.027 |
| danger false-negative rate | 87.5% | 64.7% | 59.6% |
| value loss | 0.955 | 0.887 | 0.779 |

  Tactical: cxgvxx6h losing-move probability 0.485 → 0.187, rz89dmpy 0.137 → 0.078, the rest within 0.05. **But v3's offline gains did not survive real clocks**, so v4 is judged only by lanes P/Q: archive `fable-submissions/iamavirus-v11-candidate-capture-v4-hybrid.zip` (sha 1bf9c8d29f86) = the v14 engine + capture evidence with persistence + v4, vs the v14 bytes, cores 0–1 and 6–7.
- **Astra's history/EP/memory patch merged** (`astra-submissions/candidates/history-current-r2/port.patch`, sha d303d07b505a, gated by `tools/gate_patch.sh`): belief and engine suites pass; **mode 0 is bit-identical to root on all 634 fatal-ply choices** (one search thread), so its two correctness repairs (own-move memory alignment in ApplyOurMove, en passant target carried through recovery) cost nothing; **mode 1** (exact view + continuation evidence + EP repair) is worse on the fatal tail (true attacker held 0.239 → 0.225, survival 359 → 348, king losses 21.69 → 22.56% on the fatal-only run) and **mode 2** (bounded history) was mixed on Astra's own 634-seat gate. `FOW_HISTORY_MODE` stays 0 in every archive; modes 1–2 remain available for Astra's lane.
- **v13 after 48 arena games** (00:58 UTC): Apricot 10–0, baseline 6–0, TA Baseline A 2–0, TA Baseline P 5–3, TA Baseline S 3–6–1, Strongly Invisible 0–4, Greek Gift 0–4, duck 0–4; as White 13–10–1, as Black 13–11–0; every loss by king capture. The profile of a ~1550–1600 bot: clean against the weak, even with TA-P, behind TA-S, nothing yet against the 1900+ group.
- **v4 at real clocks, early read** (01:10 UTC, lanes P/Q vs the v14 bytes): 2.5/6, all wins as White, all three Black games lost, the same shape as the v3 archive (0.5/4 as Black). Two independent checks started: a per-colour model-suite split (White-seat vs Black-seat test records) for v4 and for v1, and a hedge model **v5** = v4's warm init and data with the top-team cloning weights removed (`learning/configs/replay_unweighted.yaml`), training on the idle GPU, to test whether the weighting both newer models share is what costs them as Black.
- **Per-colour model suite** (White-seat vs Black-seat test records, 469 seats each): v4 policy 35.6% / 35.3%, belief 84.5% / 84.5%, danger FNR 58.7% / 61.5%, value 0.80 / 0.75; v1 (on the features-v1 shard of manifest v3) policy 29.9% / 30.5%, belief 79.7% / 80.7%, danger FNR 89.3% / 89.5%. No colour asymmetry in either model: the Black losses of the v3/v4 archives at real clocks are not an encoding or split defect.
- **Lane caveat and fix**: every game of lanes P/Q opened with the identical ten plies because both archives carried the same deterministic book (1.d4 d5 2.c4 c6 3.cxd5 cxd5 4.Bf4 Nc6 5.e3 e6), so that gate measured one opening line and its Black side lost 5 of 6; the "Black asymmetry" of the v4 archive is confounded with that line. The book now samples among the strongest teams' alternatives in proportion to frequency (`learning/book.py` emits move:games lists; `Engine::LoadBook` parses them; lookup draws with the engine's seed; test: d2d4 in ≥ 20 of 40 seeds, never a move outside the book). The v14 bytes keep the deterministic book (harmless in the arena, where opponents vary); the next archives carry the sampled book.
- **Capture+v4 (deterministic book) vs the v14 bytes, lanes P/Q**: 5W–4D–7L over 16, paired 0.438 (0.250–0.594), as White 5/8, as Black 2/8; all 16 games opened with the same ten plies, so this is the result of one line and does not judge the v4 model. Lane R (sampled book) and lane S (v5) do.
- **Model v5** (features-v2, same warm init and data as v4, top-team cloning weights removed): test policy 35.9% (v4 35.5%), belief 84.4% (84.4%), danger Brier 0.027 (0.027), danger FNR 58.6% (59.6%), value loss 0.78 (0.78). Offline twins; the weighting does not change accuracy. Archive `iamavirus-v11-candidate-repairs-v5-hybrid.zip` (sampled book) → lane S vs the v14 bytes, then lane T v5 vs v4 on the identical engine and book.
- **v13 streak vs TA Baseline A** (0–7 in its last 24 games, 02:16 UTC; TA-A still v5, so not a new opponent): three of the seven losses ran 124–132 plies with our clock down to 10 s, the budget floor with a 6 s reserve, after which the engine plays on the 2 s increment. The other four were early hidden-capture swings (plies 11–35). Whether losses cluster in long games is tabulated below the next entry; if they do, the clock schedule needs a long-game term (a larger divisor once the game passes ~80 plies) before the next archive.
- **Two-phase clock schedule and the r10b candidate** (02:30 UTC): v13 (cap 7 s, divisor 20) reached a clock of 15 s or less in 15 of its first 94 arena games and won 3 of them; v10 (cap 4, divisor 30) never did, and v13 won 19% of its 90–120-ply games against v10's 33%. A schedule simulation over a 180-ply game put v13's clock near 19 s at ply 130, and the variants that switch to a wider horizon after 25–30 decisions held 26–33 s there with the first-20-move spend unchanged. Root `85169e1` implements a two-phase schedule: cap 7 s and divisor 20 for the first 20 decisions, then cap 5 s and divisor 30 (`late_move`, `time_cap_late`, `time_divisor_late`; FOW_LATE_MOVE, FOW_TIME_CAP_LATE, FOW_TIME_DIVISOR_LATE; `dec=<n>` on the decision line; suite 702 checks). Root packages only features-v2 models now, so the v1-model candidate was built in a worktree at `a0f5fa7` (the v14 commit) with `625f0a1` (sampled book) and `85169e1` cherry-picked: `fable-submissions/iamavirus-v11-candidate-caution-r10b-hybrid.zip` (`ada110c059ae`). Smoke U vs the v14 bytes (4 pairs, real clocks, cores 6–7) runs after lane S and reports the clock floor; that number, not the simulation, decides whether r10b replaces v14 as the recommended upload. Lane R (repairs+v4, sampled book) vs the v14 bytes: 4.5/8 (paired 0.562, 0.188–0.875); union of lanes P, Q and R: 9–5–10 over 24, paired 0.479 (0.312–0.646), White 8/12, Black 4/12, so the v4 model is not promoted; v5 is decided by lanes S (vs v14) and T (vs v4, same engine).
- **Two-phase schedule withdrawn; r10c is the book-only rebuild** (02:42 UTC). The arena control is 180 s + 2 s (`timeControl` in every replay). v13's real spend per decision matches `TimeBudget` with `increment_share` 0.8 to within 0.1 s (median overhead +0.02 s over 2,000 decisions), so the schedule can be simulated exactly. Under that control with the book answering five decisions (clock before decision 21 / 50 / 80; budget at decision 25 / 45 / 60; thinking seconds in decisions 1–20 / 21–40 / 41–60): v14 cap 7, div 20, reserve 10: 115 / 40 / 23 s; 5.9 / 3.4 / 2.7 s; 105 / 102 / 62 s. Two-phase (switch at 20 to cap 5, div 30): 117 / 58 / 35 s; 4.8 / 3.4 / 2.8 s; 103 / 87 / 64 s. v10 cap 4, div 30: 160 / 102 / 50 s; 4.0 / 4.0 / 4.0 s; 60 / 80 / 80 s. The two-phase switch banks clock and buys no late thinking, because a divisor of 30 over a larger bank yields the same budget as 20 over the smaller one; the steady state of any schedule here is spending the 2 s increment, with a floor of reserve + 0.4 × divisor. So the mechanism stays in root but off (`166da52`), and the r10b archive was withdrawn before its smoke. Refreshed arena tabulation over 107 v13 games (46–7–54): 20 games reached a clock ≤ 15 s and 5 reached ≤ 10 s (v10: 0 of 144); mean length 77 plies (v10 66); win rate by length v13 / v10: under 60 plies 82% (33) / 79% (67), 60–89 36% (42) / 28% (46), 90–119 22% (18) / 32% (22), 120+ 25% (14) / 22% (9). The long-game gap is inside noise at these counts, and v14's book plus the 10 s reserve already lift v13's observed floor (its 10 s floors came with reserve 6 and no book). Hypothesis left for a session with ≥ 40 real-clock games: a flat cap 5 / divisor 25 shifts about 25 s of thinking from decisions 6–20 into 30–60 (budget 5.0 / 4.2 / 3.2 s at 25 / 45 / 60) and is the only schedule family in the table that thinks more late; nothing here says whether that is worth the early time. `iamavirus-v11-candidate-caution-r10c-hybrid.zip` (`2ae7ee3c6cce`) is the v14 commit plus the sampled book only; smoke U vs the v14 bytes is re-pointed at it.
- **Queen-loss corpus and what it says about the belief** (03:10 UTC). From the true boards in the arena replays (`frames[].board`), a queen-lost-for-less event is: the opponent captures our queen and our reply does not take a queen back, and our previous move was not itself a queen trade. v10: 52 events in 144 games (36%), 15 before ply 30; v13: 37 in 107 (35%), 2 before ply 30, knights as capturer down from 13 to 2, sliders 32 of 37, the capturer unseen when we chose the move in 34 of 37 and visible only after the move in 32 (the queen moved onto the slider's line). `data/queen-loss-seats.txt` holds all 240 such decisions (v4 105, v10 52, v13 37, older 46) as truncated seats whose last own ply is the queen-losing move; `tools/benchmark_corpus.cc` now reports, at those plies, the belief mass on the true capturer (`QueenCapturerMass`, any attacker of the queen after the real move, matched by piece and square across particles), the engine's repeats by mass band, the same restricted to plies with a safe true-board alternative (king safe, queen not en prise, exposure < 3), and in verbose mode one `QL` line per decision. Baseline (root engine, seed 1, 400k nodes, one thread; `build/benchmark_queen2`): capturer mass mean 0.398; bands < 0.05 / 0.05–0.3 / ≥ 0.3 = 81 / 56 / 103 plies with engine repeats 33 / 12 / 23; with a safe alternative 79 / 55 / 93 and repeats 31 / 11 / 15 (57 avoidable, 11 forced). Per version (avoidable repeats / plies): v4 25/105, v10 10/52, v13 13/37, and 10 of v13's 13 are in the < 0.05 band. So for the current engine family the residual queen loss is a belief miss: the particles do not hold the slider at the far end of the line the queen steps onto. Arms on the corpus (avoidable repeats, all / v13): baseline 57 / 13; FOW_HIDDEN_THREAT=2 worse (70 queen-en-prise vs 68); FOW_SURFACE 5 / 10 / 20: 67 / 66 / 63 queen-en-prise; FOW_SURFACE=20: 52 / 10; FOW_SURFACE=10 with FOW_SURFACE_RAY_CAP=7: 55 / 12; FOW_SURFACE=40 cap 7: 49 / 9 (v13 low-mass 10 → 7). The charge is particle-independent, which is why it is the only term that moves the low-mass band; its cost on the 634-seat fatal corpus and a real-clock lane V (`iamavirus-v11-candidate-caution-r10c-surface40-hybrid.zip` = r10c with surface 40 / cap 7 as defaults, vs r10c, cores 0–1 after lane T) are running. Astra's side: the same corpus gives a direct belief gate (capturer mass at these 240 plies) for its grouped-prediction and posterior-root branches.
- **Candidate for the next upload:** `fable-submissions/iamavirus-v12-hybrid.zip` (arena v12; was `iamavirus-v11-candidate-hybrid.zip`) (sha `68a89006f6c2`): v10 + population-wide exposure term + pawn visibility deductions (on) + clock scaling by difficulty + underpromotion rule + per-particle move memory; hybrid, stage A release v1. Behaviourally identical to the former `v12-candidate-hybrid` (its extra slider deduction never fired), so that archive's paired lanes vs archived v5 are this candidate's evidence: **10W–0D–10L over 20 real-clock games** (16-game gate 9–7, then a 4-game smoke of the final bytes 1–3), paired score 0.500, bootstrap 95% 0.300–0.700 (v9 on the same gate scored 0.472, 0.306–0.639): even with v5 at real clocks, better offline; a 2-pair smoke lane of the new bytes is running; clean-directory build verified.
- **Process lesson.** `pgrep -f` / `pkill -f` with a pattern that appears in the calling shell's own command line match the caller: four queued lanes waited on themselves for an hour and one shell killed itself. Use `pgrep -x name` or flag files.

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
