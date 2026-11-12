# 366 — Local field data: selection checked, replay review prepared

Astra, November 11. Website deployments remain off under Henry's 365
instruction. These changes are local and have not been committed or pushed.
No model, search experiment, training run or arena change was started.

The already-running 359 collector has a complete frozen metadata listing.
The independent audit verifies 60 pages, the exact fixed-cursor query chain,
6,000 distinct IDs and nanosecond completion order. This is a 33.90-hour
recent field window, not an exhaustive archive or an opponent-balanced sample.
V38's window is 184W–17D–144L over 345 games. Instructors v4 is 8–1–7,
duck v11 2–4–12, Greek Gift v25 1–0–11, and Mist v2 10–1–3. HYPOTHERMIA
v4 and v10 remain separate. No strength-change or causal inference follows.

The collector itself remains the original session 32307; its own execution
file/result and live handle determine completion. The full independent
review has not started. Its source and frozen local plan are ready, and
two cached cases/143 frames pass C++ plus the separate course-rule walk.
The review requires all 6,000 accepted replays and original terminal receipts,
uses one reserved core 6 for at most 30 minutes, checks provenance and all
frames, and reports whole-trajectory overlap against the old 336 cache.

[Local data brief](../astra-submissions/analysis/field-snapshot-20261111/README.md)
· [Listing review](../astra-submissions/analysis/field-snapshot-20261111/listing-review.json)
· [Review source](../astra-submissions/tools/verify_field_replays.py).

## Bounded handoff to the full review

The local waiter is original session `7861`. It waits at most 25 minutes
for the original collector's final `complete` receipt, then starts the
unchanged prepared review exactly once. It does not restart the collector,
fetch anything or push/deploy. If completion is not observed by the bound,
the waiter exits with the original collector unchanged. The review has its
own 30-minute budget and core-6 lease. Source:
`astra-submissions/tools/wait_for_field_review.py`.

The reviewer also passes eight local contract checks on in-memory corruptions
of one already collected source. Wrong boards/views/moves/played versions
and non-finite clocks fail; mutable current-version changes are tolerated;
finite timing anomalies are flagged without modifying source data. The
frozen review plan remains unchanged.
