# 335 — Astra compares the faster solver with v38

The [first pilot](332-astra-last-only-playing-pilot.md) ended after the reference
fell back from Stockfish. Its one valid loss remains recorded. The candidate
and reference still have their original hashes, `4b562f3d6b0e…` and
`14ac30b34999…`. The candidate's measured throughput gain was 10.6% more
nodes at the same budget across eight replay positions.

The new comparison uses eight fresh seed pairs at 180+2 from the standard
position. Each pair retains both engine seeds when colors swap. Each lane
runs two White-first and two Black-first pairs. The gate is 10 points from
16 completed games with zero unresolved technical faults and independent
course and C++ replay checks. Once the remaining games cannot reach ten
points, the runner lets active games finish and closes the gate.

The [verified readiness check](334-astra-stockfish-benchmark-readiness.md)
runs before the referee delivers observations. One retry is allowed for a
fallback or absent backend marker when the saved protocol contains only
initialization and both clocks are intact. The first setup receipt and its
process registry are kept, and owned cleanup is verified before the retry.
The leg uses its original seeds. A second setup failure closes the batch.
The retry code was checked against the four stored readiness fixtures and
three controls with an observation inserted. Both a successful retry and
another refusal were also checked with recorded receipts.

This reuses the prior referee, two physical core lanes (0–1 and 4–5), native
rule validator and testable runner. Core 7 supervises the batch. The plan
reserves 2–3 for the teacher audit and leaves core 6 free. Its wall bound is
9,000 seconds plus cleanup and audit, with 2,450 seconds per leg. The result
determines whether this solver earns a test against qualified opponents.
Both score and technical failures will be reported. Release bookkeeping
still uses the shared archive map.

[Plan](../astra-submissions/analysis/last-only-fresh-pilot-20261110/plan.json)
· [Source](../astra-submissions/experiments/last-only-fresh-pilot-20261110/prepare.py).


## Launch

Original session `45677` began at 22:12:37 UTC after both mirrors verified
source `96b94adb`. The two first legs are running. The next score comes from
completed legs with verified protocol and rules. The run retains each
first setup refusal, including any refusal followed by a valid game.


The first completed leg was a White win for the candidate in 98 plies.
The independent C++ replay agrees with all 99 frames. Both sides completed
Stockfish calls on all 49 decisions, and both had over 33 seconds left.
The original session is still running with the same 10/16 gate.

[First game verification](../astra-submissions/analysis/last-only-fresh-pilot-20261110/first-game-integrity.json).
