# 160 — Astra: fixed ownership, working depth prototype, first screen

Fable's final ledger decision at 19:52:21 UTC settles the crossed messages:
**Astra owns depth 1 versus 3 and independent review; Fable owns combined
material risk.** Note159's implementation contract and the corrected schedule
govern. My note157 capture-history proposal is deferred before fitting; no
training run occurred. No more ownership changes are needed.

## Implemented now

`astra-submissions/tools/build_leaf_depth_candidate.py` extracts the immutable
v35 archive, changes only `src/sfeval.c`, and builds a controlled depth setting.
The default remains depth1. Belief, model, table, guards, clock, MultiPV and CFR
are unchanged. Source/binary/Stockfish/table hashes are pinned in
`astra-submissions/analysis/leaf-depth-20261026/build.json`.

Nine UCI transport tests pass, including command depth, invalid settings and
latest-depth score parsing. The original native Stockfish test passes at depth1.
At depth3 its mirror tolerance (chosen for depth1) fails: 0.148 versus 0.12 on
one position. That failure is retained. A separate native contract check records
mirror differences instead of imposing the depth1 tolerance; supported move
coverage, illegal-standard-chess castling exclusion, refused-position handling
and continued worker operation pass. This is an interface result, not strength.

## Frozen first screen

- One implementation, depth1 and depth3, versus the same Misty-v16 wrapper.
- Eight matched blocks: both colours for both settings, 32 games total.
- Same seeds within matched comparisons; alternating depth order across blocks.
- Real 180+2, cores0–1, maximum three hours wall time, no parameter sweep.
- Record all results, clocks, binary hashes and replay hashes. Report incomplete
  blocks separately if the cap stops the run. Stop for reliability review on a
  time/protocol/crash/illegal termination by either bot.
- A first-screen lead of at least three points across 16 games per setting and
  no reliability failure earns further evaluation. It does not prove Elo gain.
  A negative or inconclusive result is reported without extending this screen.

## Independent review of the material contract

1. Use the immutable v35 behaviour as parent. Current mist-c main has the
   standing fog term enabled at 0.5; silently inheriting it would confound the
   proposed material-only change. Pin the baseline and candidate settings.
2. Outcome after a material loss is observational, not a causal estimate of
   that piece's value. Treat fitted lambda as a provisional loss cost, with
   opponent/phase/material matching and a held-out check. Do not advertise
   that fit alone as proof the guard is calibrated.
3. Include ordinary positions from losses as controls, not only wins/draws;
   otherwise controls can be systematically easier. Check king fatalities and
   selected-move quality, not merely avoiding the historical losing move.
4. Define overlap when a world permits both a queen loss and a minor/rook loss.
   Excluding queen capture actions alone does not make those world events
   disjoint; explicitly choose an incremental-cost or mutually exclusive rule.
5. Report same-clock runtime and both colours. The 40-game bench is a screen;
   a bounded arena trial may follow credible combined evidence without waiting
   for a statistically proven local Elo gain.

## This week's checkpoints

- **27 Oct, 20:00 UTC:** measured prototypes and candidate-or-reject reports.
- **28 Oct, 20:00 UTC:** local gates and independent review evidence.
- **Thursday 29 Oct:** submit-or-reject decision; a combination is evaluated
  only if its individual components warrant it.
- **Friday 30 Oct:** outer human review; any arena trial has a 20-game early
  check and a 100-game retain/revert review when that many games are available.

Rank5 is the competitive target, not a guaranteed consequence of a new ZIP.
