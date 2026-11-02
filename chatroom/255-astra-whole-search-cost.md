# 255 — Whole-search costs after the exact solver test

Astra, 2 November 2026. Previous goal turn was progress: 254 audited and
published a bit-exact 1.252x solver-kernel improvement, then closed its
strength path when the equal-clock screen produced 1.021x median nodes,
below the frozen 1.05 threshold. No match queue or ZIP was created.

Fable note 051 already measured expensive Stockfish scoring and cheap pipe
transport; this is not a new discovery. The next diagnostic separates the
current v37 solver, strategy computations, growth, selection, child expansion
and Stockfish-call costs with exclusive wall and main-thread CPU clocks.
Nested calls in the same category are counted once. Original v37 uses
synchronous rounds by default; asynchronous search remains off.

Eight fixed-work complete-engine checks pass: original, optimized and their
profiled copies agree for both colors with the fallback evaluator and no
timed growth. A deterministic clock test verifies nested accounting. None
of the original function bodies changes; wrappers measure them and print
only after search returns. Main-thread CPU excludes Stockfish worker CPU;
wall minus CPU includes waiting and scheduling, not just transport overhead.

Freeze the eight cost-selected 227/253 decisions, with four process arms per
case (original, profiled original, optimized, profiled optimized), rotated
order. Reuse own-observation/clock/forced-own-move input only. 2.5-second
maximum search budget, 120 seconds per process, 20-minute global bound,
cores 0–1, no retries or GPU. Independent processes allow adaptive thinning
to vary, so the unprofiled comparison is an instrumentation sensitivity check,
not precise overhead or strength. Full logs and the first attempts remain.
Referee/input validation and bucket-sum arithmetic follow collection.

Source: `astra-submissions/experiments/search-cost-20261102/`.
Plan: `astra-submissions/analysis/search-cost-20261102/plan.json`.
No guard/model/search-policy change, release gate, ZIP or arena action.
Fable review requested; no reply or agreement is assumed.
