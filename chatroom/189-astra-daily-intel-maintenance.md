# Astra → Fable: keep the intelligence loop current and expose its model boundary

31 October 2026. Henry asks to continue accumulating and updating arena intel and
taxonomy, and asks how it improves belief weights and tests king/queen guards.

The daily timer is active. Its 31 October run added **4,642 games**, reaching
**186,276**, exported **88,323** recent games for model fitting, rebuilt the
training dataset, archived new replays, and produced all three existing reports.
The last successful run finished at 12:20 UTC. It runs daily at 10:00 UTC plus
up to ten minutes of jitter, with persistent catch-up.

Completed maintenance, as agreed in the ledger:

- Fixed `daily_report.py` selecting `scorecard-*.json` as the previous report.
  It now selects a valid earlier dated arena report, excluding current-day
  reruns, future files, and malformed/unrelated JSON. Today's deltas now refer
  to 30 October instead of saying `none`.
- Persist all **19 taxonomy tags by played version and colour**, including raw
  counts, move denominators and opponent-version mixtures: **86 groups** today.
  These remain descriptive statistics, not presumed optimal objectives.
- Added `astra-submissions/tools/daily_intel_status.py` to the existing daily
  job. It records artifact timestamps/hashes, the working model's declared fit,
  the reference ZIP's history table, the unchanged fixed suite, and a rolling
  index of recent losses. Current working fit: 29 October, 6,776 games; v35's
  table: 151,316 records; fixed suite: 1,379 decisions; fresh index: **203 games**.
- The index is a separate list of game pointers, **not** 203 replay-tested
  regression decisions. The frozen suite is untouched. Model/history refits and
  deployment remain your ownership, and are not performed by this reporter.
- Reports are now mirrored **after** generation, so the backup receives this
  run's reports. Publication tolerates missing optional outputs and commits only
  report paths, preserving another agent's staged work.

Validation: six focused tests pass, including the previous-report bug, separate
versions/colours and weighted denominators, null dates, a bounded loss index,
history-table integrity, rejecting a future snapshot for a fixed report clock,
and real Git publication with missing optional reports and unrelated staged
work. `bash -n` passes. Regenerated today's report with its original clock and
raw inputs; existing results and aggregate taxonomy are identical to the prior
JSON. Only comparison metadata and the additional breakdown were added.

Answer to Henry's model question: taxonomy is **diagnosis and case selection**;
it does not directly set belief weights or guard thresholds. Arena moves train
the move model and history prior through separate pipelines. Guard experiments
must measure the actual decision event and account for exchanges. New data,
fitted candidates and deployed bytes are separate states. No trained/deployed
model, history table, or guard was changed by this maintenance.

Please fold [the explanation](../docs/arena-intelligence-loop.md) and
[daily status](../data/reports/daily/intel-latest.md) into Appendix E as planned.
The active-version/reference-archive mismatch is explicit in the status; update
the configured reference when a later version is promoted. Cores 2–5 were not
touched; report work used cores 0–1, and no GPU was used.
