# Current-v38 last-only solver cost gate — November 10

Prepared, not executed. Three arms: original v38, reused253/254cached/selective,
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
