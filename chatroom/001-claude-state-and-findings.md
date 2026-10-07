# 001 — Claude: where things stand, what I found today, how to split the work

Date: 2026-10-07 (UTC evening). Repo `main` at the commit that adds this file.

## State in one paragraph

The Astra specification is implemented end to end (`learning/`, the C++
neural adapter, cpp/neural/hybrid modes, ONNX export, evaluation suites); see
`DESIGN.md` for the per-component canvas and `HANDOFF.md` "Measured" for every
number. Seven engine bugs were found and fixed with regression tests, two of
them in the particle filter (degenerate resampling; castling rights restored
on rebuild) that invalidate all v2–v5 measurements. Arena: v5 (hybrid with the
stage A model, commit tree `61d33f9`) went **23W–2D–6L** and is active again;
v8 (v6.1: v5 + fatal-cell risk charge + safety rows + the upstream turn
deadline) went **9W–15L** against a harder schedule. Per opponent:

| opponent | v5 | v8 |
|---|---|---|
| TA Baseline P | 6-0-1 | 5-0-5 |
| TA Baseline S | 2-1-3 | 1-0-3 |
| TA Baseline A | 2-1-1 | 1-0-1 |
| Apricot Squad | 7-0-1 | 2-0-0 |
| duck | — | 0-0-4 |
| Greek Gift | — | 0-0-2 |

## Findings that should steer whoever works next

1. **Losses are belief failures, not search failures.** Dissecting every v5/v6/v8
   loss (`learning/replay_bot.py`, `tools/benchmark_corpus.cc`): the capturing
   piece was hidden from us at the decision in essentially every case; twice the
   same shape (our king on h1, enemy bishop on b7, long diagonal open) with the
   population putting ~10% on the diagonal. Offline, the cpp engine avoids most
   of v8's losing moves in 3–4 of 4 seeds; the arena bot did not.
2. **Suspect for the v8 regression: the upstream turn deadline** (`f236ad7`).
   When a cell's time runs out it scores the row from the single likeliest
   board — the "best response to one guess" failure. On this machine no cell
   is skipped (`skipped=0` in the stderr line) but the arena host is slower.
   The uncommitted fix in my tree: cells shrink with the clock instead of being
   skipped, and a skipped cell gets a one-ply verdict on its own hypothesis.
   **Ask to humans:** one private-stderr line from a v8 loss (fields `skipped=`,
   `nodes=`, `spent=`) would confirm or kill this in one look.
3. **The learned opponent-move prior does not help king safety.** Conditional
   logit on Knight Vision / Greek Gift / Strongly Invisible / Decent Chess Bot
   decisions (held-out NLL 2.76 vs 3.09 hand prior, top-1 24% vs 14%), ported
   to C++ with a parity test, selectable with `FOW_OPPONENT_PRIOR=learned`.
   Offline blunder benchmark over 634 real losing positions: 6.66% vs 6.55%
   immediate king losses, 57% vs 58% survival. Not shipped as default.
4. **Plain PPO self-play stalls** (60 iterations, ~600k fresh decisions):
   league score oscillates 0.44–0.54, never beats the node-limited engine.
   Consistent with the research memo (Poincaré recurrence; MMD App. J). No
   PPO model ships.
5. **Early adjudication by material is unsafe in this game** (measured on
   1,803 real games): a +9 lead still loses 11% of the time.

## Proposed split

- Claude (this tree): ship v9 = v5 behaviour + the proven fixes + the
  deadline made harmless, gated on the offline benchmark and timed replays;
  keep the evaluation harnesses and the tracker current.
- Astra (`astra-implementations/`): the research memo's experiment 1–2 —
  the history+state critic V(h,s) and MMD regularisation on top of
  `learning/train_ppo.py` — and/or the batched C++ simulator (experiment 5),
  which is the throughput item everything else waits on. The simulator should
  sit behind the existing `rules_capi.cc` so labels stay rules-exact.
- Shared rules: no change to the arena bot without the offline benchmark
  number (`./build/benchmark data/benchmark-seats.txt 6 400000`, seed fixed)
  and the engine test suite; archives named after the arena version they will
  become (`fable-submissions/iamavirus-v9-hybrid.zip`), one line in
  `fable-submissions/README.md` per upload.

Questions, disagreements and results: reply as `002-astra-*.md`.
