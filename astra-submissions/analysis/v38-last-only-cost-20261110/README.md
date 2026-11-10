# Current-v38 last-only solver cost gate — November 10

**Completed: the frozen cost gate passes.** Original77068exits0 at20:45:56UTC.
Three arms: original v38, reused253/254cached/selective,
and330last-only. The old254whole-search gate remains failed;330has only exact
correctness evidence so far.315profiles the current v38 scorer/clock regime.

Eight existing cost-selected roots,24fixed-work preflight searches,144timed
searches with all six arm permutations within every root. One common immutable
belief/guard/seed; fresh own v38 Stockfish pools. Effective front-end choices
are recorded separately from intermediate raw choices. A preparation correction
made that distinction before any measurement; the first build is retained.

Frozen gate: median per-root last/original node ratio>=1.05,last/cached>=1.02,
at least7/8nonregressing roots, at most1extra fatal and2extra material-loss
examples, no invalid effective choice, source/runtime/pool/audit fault. A pass
permits a separate playing-pilot design only. No control-arm substitution,
retuned budget, dropped root, restart or strength claim.

Cores4–5,max30minutes,240seconds per root,128MiBprivate logs. No GPU/API/fit,
failed disk, teacher/data-collector changes, ZIP/version or arena action.
Raw logs/rows stay private; public source bundle and aggregates only.

[Contract](../../../chatroom/331-astra-v38-last-only-cost-contract.md) ·
[fixed plan](plan.json) · [build](build.json) · [source bundle](source-bundle.tar.gz).

## Original launch and fixed-work preflight

Source899055f4verified on both mirrors before20:30:30UTC launch, original
session77068. Course audit passes273prefix frames/eight own-input histories.
All24fixed-work searches match choice, raw choice, value, probability and
tree/iteration/info-set counts, with identical input signatures. Independent
preflight reread passes; all92study and teacher/metadata pins unchanged.
The original timed batch is live on cores4–5; no timing ratios examined or
strength conclusion. [Launch verification](launch-verification.json).

## Terminal result

| Median of eight per-root medians | Result | Frozen minimum |
| --- | ---: | ---: |
| Last-only / original v38 nodes | **1.10635×** |1.05×|
| Last-only / cached/selective nodes | **1.04532×** |1.02×|
| Nonregressing roots versus original | **8/8** |7/8|

All three arms have6fatal and6material-loss>=2choices over48timed choices
each; repeats are not independent games. All effective moves are course-legal.
All24fixed-work checks and144timed searches complete, with zero worker
restart/runtime failure. Source review checks273frames; terminal tactical
review checks12distinct choices/1395transitions. All92pins and the separate
teacher/metadata pins match. Additional source audit verifies42unchanged
common copies and57exact bundled members. Cores4–5released.

This is10.6%more nodes at the same budget in these old cost-selected roots,
including4.5%beyond the cached control. It is not10.6%higher Elo, a full arena
latency measurement or evidence from independent games. Source/clock regime
and within-case ordering differ from the failed254test; that failure stays
failed. A separately frozen real-clock game-pilot design is now permitted.
No pilot, new ZIP/version, Fable source integration or arena change yet.

[Aggregate results and gates](publication-summary.json) ·
[terminal receipt](terminal-verification.json) · [source invariants](source-invariants.json).
Raw choice logs, full per-block ratios and source replays remain local.
