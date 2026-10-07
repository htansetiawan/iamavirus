# Session handoff

Written 2026-10-07 for a fresh session, including one on a different machine.
Read this before changing anything; a good deal of it is the result of being wrong
several times and it will save repeating that.

## Where things are

| what | where |
|---|---|
| engine source (the submission) | this repository, root |
| per-version record | [versions/](versions/) |
| measurement tools | [harness/](harness/) |
| real-game corpus | [corpus/corpus-all.txt](corpus/) |
| design notes | [ENGINE.md](ENGINE.md) |
| course starter kit | **not vendored** — GPL-2.0; download from the course site |

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

## Three known bugs, still unfixed — highest-value engineering work

All three were verified locally with probes, and all three corrupt the search and
would also corrupt any training labels derived from it.

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
- Training data: `corpus/corpus-all.txt` is already here. For a larger corpus use
  `harness/corpus_download.py`; the public API rate-limits and returns 503 when
  busy, so keep `--pause` at 1.2 s or more.

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
