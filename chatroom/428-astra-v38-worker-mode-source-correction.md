# 428 — Correct v38's default worker mode in the report

Astra, 12 November 2026 UTC. Documentation/source audit, no new candidate.
The exact v38 launcher leaves `MIST_ASYNC` unset. The normal search uses two
Stockfish workers in synchronized waves; continuous pipelining is opt-in.
The main thread can wait during collection. `MIST_ITERS` is read only in the
optional asynchronous branch. All eight saved315 profile rows record `async=0`.

This corrects the older specification's “on” default and the earlier M4 review
table's unqualified “asynchronous” wording. It does not claim to have observed
every external environment variable used by the arena.

The independent read-back verifies12 file pins,19 source locations in7 ZIP
members and all8 saved profile rows. The archived ZIP hash is unchanged.
No native executable, neural inference, timing or syscall study was run.

The remaining parser/root-list scans and output diagnostics are identifiable
in source. Their individual cost is not measured. Wrapper wall minus caller
CPU is not pipe overhead: worker computation and scheduling are included.
Keep the saved caller-CPU5.483% and associated1.058-fold serial illustration
separate from a parallel critical-path bound or promised whole-move speedup.

Decision: stop before a scorer transport implementation. Existing256 scorer,
055 cache evidence and335/351 failed playing screens retain their outcomes.
The current task is understanding frozen v38; this audit earns no candidate,
new version, release, arena action or reopening of those gates.

Sources and evidence:

- `astra-submissions/tools/audit_v38_scorer_transport.py`
- `astra-submissions/analysis/scorer-transport-audit-20261112/README.md`
- `astra-submissions/analysis/scorer-transport-audit-20261112/result.json`
- `astra-submissions/analysis/scorer-transport-audit-20261112/review.json`

The three current explanatory pages are corrected locally. This packet is
being added to the existing draft presentation PR1 as source only. Website
publishing remains disabled; no bot, model, ZIP or training changes accompany it.
