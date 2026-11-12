# V38 worker scheduling and residual scorer work

Source review and saved-profile arithmetic only. Seven archived source files
match the immutable v38 manifest; the ZIP remains SHA-256
`ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
No native engine, model, timing, syscall trace, match or new candidate ran.

## Correction for the final report

V38 defaults to **two Stockfish workers in synchronized waves**. The normal
loop runs solver iterations, picks leaves, submits a wave and collects its
answers. The main thread can wait during collection. Continuous pipelining
requires nonzero `MIST_ASYNC`; the archived launcher does not set it.
`MIST_ITERS` is read only in that optional branch. All eight saved315 profiles
record `async=0`.

The older specification's “on” value and the first M4 review table's
unqualified “asynchronous” label were incorrect descriptions of the archived
default. The source supports the optional path; this is not evidence that it
was enabled. An unrecorded arena-side environment override remains unknown.

## What a speed claim would need

Existing256 already removes repeated ordinary MultiPV root passes. It changes
search trajectories and scores, so it must not be described as a bit-exact
quadratic-to-linear optimization of the whole evaluator. Linear membership
and result-record searches remain inside the Stockfish root loop. The C-side
score parser also linearly matches a UCI move against native moves for every
accepted score line.

Output construction additionally computes hash occupancy for every emitted
PV, formats a full line and requests a stream flush. Source alone establishes
neither syscall count nor the proportion of latency attributable to that work.

An illustrative 35-action, full-coverage response with one accepted unique
score per action performs630 native parser string comparisons. Thirty-five
hash-occupancy calls each visit3000 entries, or105000 entry visits. These are
operation-count examples, not recorded native counts, timings or NNUE costs.
Aspiration retries, cutoffs, repeated/bounded lines and actual move counts
change the work. The ordinary-root full-sweep triangle is likewise a simplified
illustration, not a claimed measured eighteen-fold speed opportunity.

## Reconstructing315 without rerunning it

| Saved aggregate, eight decisions | Seconds |
| --- | ---: |
| Target-turn wall |50.310650950|
| Search wall |43.527088748|
| Stockfish-wrapper wall |20.997449393|
| Stockfish-wrapper caller CPU |2.758547910|
| Solver plus strategy wall |19.534797832|

Wrapper wall includes worker computation, waiting, scheduling and transport.
Caller CPU is not the worker's formatting/search CPU. Subtracting these
measurements does not identify pipe overhead. The caller CPU is5.483% of
target-turn wall on this panel; eliminating all of it gives a1.058-fold
**serial fixed-work illustration**, not a parallel critical-path bound.
Halving all scorer-wrapper wall similarly illustrates1.264-fold whole-turn
speed. Neither number predicts more nodes or Elo under adaptive search.

**Decision: stop before a transport rewrite.** Worker formatting, diagnostics,
flushes and pipe-only cost remain unmeasured. There is no supported large-gain
claim or new candidate qualification. The current phase is understanding v38.

## Prior work and evidence boundary

055's older ordinary-MultiPV stream found only5.78% exact-FEN repetition,
with1728/1734 repeated score maps changing. That closed naive exact-FEN caching
on that run; it is not a duplicate-rate measurement of the new all-child mode.
315's current profile replaces the old v37 cost budget for these conditions.
335's last-only playing screen9/16 and351's combined speed build4–7 remain
closed. This source review does not reopen any of them.

`plan.json` states the scope and stop rule. `result.json` pins twelve source/
saved-result inputs and nineteen locations in seven ZIP members.
`review.json` independently checks those pins, source locations and eight
raw profile rows. The auditor is
`../../tools/audit_v38_scorer_transport.py`; it does not execute a native program.
