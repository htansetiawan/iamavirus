# 052 — Astra: full games expose setup failure; root-policy pilot mixed

The first actual 180+2 pair against your frozen mist-c v8 is **1–1**, both
king-capturable endings. This is not a clean strength gate or an Elo estimate.

- White loss: 71 plies. Rb3–b8 uncovers the hidden Qd5 diagonal into Ka2.
  All72 recorded frames, observations and moves validate against the referee.
  The only true immediate-safe actions were five pawn pushes. Original
  diagnostics lost the first M4 record to the referee's16KiB rolling tail.
- Black win: 83 plies. Full diagnostics expose an actual M4 failure at ply17:
  carry7041/offI1614,6050 Stockfish calls,4.71s evaluator time,5.02s setup,
  `ok=0`. The frontend used visible-board search, then M4 restarted next turn.
  The remaining two planned baseline jobs are held for this defect.

## Capture repair

The local runner now retains stderr up to the referee's existing1MiB output
budget, preserving the original total-output and line-limit warnings. A24,210
byte subprocess test retains first/last markers and confirms excess-line
warnings still fire. Turn buffering, group pausing, exit/timeout classification
and cleanup pass. Native rules/referee source and engine binaries are unchanged.
The original loss and incomplete diagnostic remain immutable; no rerun/exclusion.

## Root-policy experiment: published, default off

`htansetiawan/mist-c` branch `astra/m4`, commit `c887a84`, adds
`MIST_M4_DOMINANCE=1`. Full-precision, gadget-reach-weighted risk/value profiles
redirect played mass only toward lower-risk/no-lower-value actions. A sorted
frontier gives O(A log A) selection; board-profile computation remains O(RA).
The carried blueprint is retargeted with the executed distribution, including
zero-support destinations. Regrets are not reused. This is an empirical
extension, not an equilibrium guarantee or a calibrated posterior risk.

The new six-decision pilot (three seats × off/on) records3 immediate losses
off versus1 on. It saves s24 seed12 and the newly observed White rook exposure;
it **does not fix s24 seed11 reliably** (e3d3→e3f2, both fatal). Final wall-clock
solver profiles differ, so these are not counterfactuals on one identical tree.
The originally motivating post-hoc saving does not automatically reproduce.
No default change, archive or strength claim.

## Setup work in progress

Real-Stockfish correctness testing found an independent capacity defect: a
carried tree could fit the node cap without room to expand all current roots.
A preflight now restarts from sampled belief when the complete closure plus
necessary action rows cannot fit. The exact failing30,000-node test passes:
Black decision4 restarts from12 belief worlds, completes40 iterations and
saves a snapshot in~0.21s, rather than falling through to visible-board search.

A second, opt-in `MIST_M4_FAST_ROOTS=1` uses internal initial values only for
new children of carried current frontier roots. Search expansion and fresh
child alternates retain Stockfish. This avoids a blocking external call for
thousands of mandatory setup rows, but changes heuristic initialization and
needs a strength test. A frozen paired searched-prefix diagnostic of the
actual ply17 game is running on6–7; earlier wall-clock solves need not reproduce
its exact saved tree. Default remains off.

Evidence: `astra-submissions/analysis/m4-clock-20261011/`,
`astra-submissions/analysis/m4-root-policy-20261011/`, and the immutable
Seagate runs named in their manifests. No GPU use. No new phone messages.

## Update — setup replay completed, repaired full games started

C commit **fd7b764** is pushed to `astra/m4`; the full M4 suite and both-color
real-Stockfish carry test pass. The standard searched prefix reproduces the
ply17 failure with6819 roots after5.0203s. Cheap initialization completes:
6334 carried roots,6172 initialized cheaply,0.5347s setup,4.4839s solving,
0.0765s snapshot,valid result. Earlier trees differ; do not quote a precise
speedup from this pair.

A fresh four-game180+2 screen against the same frozen v8 has started at11:15UTC
on6–7. Fast roots on; dominance off; scale1; seeds11/12,both colors. Original
1–1 results remain separate. No loss is dropped, and faults stop the batch.
See `astra-submissions/analysis/m4-root-setup-20261011/` for the plan, manifests,
paired results and correctness evidence.
