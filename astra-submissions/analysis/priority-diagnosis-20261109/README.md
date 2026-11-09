# V38 priority-decision diagnosis

Frozen development cohort:26 losses to duck/Greek Gift from v38's first318
games, plus the preceding own decision for the10 final positions that were
already immediately lost.36 decisions, two seeds, at most30minutes on cores0–1.
This studies causes of failure; it is not a playing-strength experiment.

The source is the exact uploaded ZIP ba6610f299c1, with unchanged C/model,
history table and modified Stockfish. The instrumented copy adds two read-only
exports: teacher targets after the solver selects, and full-belief king risk,
combined exclusions and placement support after the protocol move is emitted.
The truth placement is first read in that last block. Old pre-decision risk
and truth instrumentation is disabled. Output work adds runtime after the
choice; no claim of a zero-cost instrumented executable is made.

Both-color initial-position control/diagnostic preflight passes (White d4,
Black d5; no faults), as recorded in preflight.json. That checks integration,
not byte-identical wall-clock search trajectories. The old teacher exporter
and conditional-value calculation are reused from the tested prior audit.

Readouts distinguish:

- Full-placement support and weight versus presence among32 sampled worlds.
- True-safe actions absent from the observation-derived move set versus
  present actions removed by guard/repetition exclusions.
- True-safe retained actions versus the selected action and its root policy
  probability/conditional continuation value.

Truth labels use the course referee outside the actor. Placement agreement
does not verify castling/en-passant rights; it overestimates full-state
support. Prior own moves are forced and do not warm Stockfish as the arena
did; the original clocks are supplied, but clock-sensitive belief thinning
can differ from the actual game. Findings are conditional on the reconstructed
belief. They cannot prove that the exact same arena decision had that belief.

plan.json pins the36cases,72attempts,seeds,code and dependencies. A review-logic
correction before any actor run is preserved in preflight-plan-initial.json:
missing safe moves and excluded safe moves must not be conflated. Each case
has a120-second timeout; the batch stops on a technical failure or global
wall bound, retaining missing cells explicitly. No replay is restarted to
replace a failed first attempt. Runtime outliers include post-choice readout.

Sources: [prepare](../../experiments/priority-diagnosis-20261109/prepare.py),
[runner](../../experiments/priority-diagnosis-20261109/run.py),
[review](../../experiments/priority-diagnosis-20261109/review.py).
No GPU, network ingest, model fit or new release is launched by this study.
