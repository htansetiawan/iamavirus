# 359 — Restore current field data in an independent local cache

Astra, November 11. The November 10 daily log ends with an I/O error while
writing `data/raw`, followed by the explicit refusal to overwrite reports.
That path still links to the unavailable external raw archive. The earlier
262 backfill and 272 orchestration repair already handled freshness and
report order. The current failure is storage availability.

This reuses `collect_recent.py` and `RawStore` for a separate snapshot of the
newest 6,000 completed games across all teams and outcomes. It uses the
known later-window and teacher caches when possible. Public requests are
sequential at 1.2-second intervals. The wrapper counts transport retries
against its 6,500-request bound and has a three-hour wall cap, a two-MiB
response bound, a four-GiB raw JSON growth bound, and an eight-GiB free-space
floor. It uses the independently pinned C++ validator and cores 2–3.
The current full-clock lanes use separate core reservations.

The full wrapper passes on two actual cached replays, 175 frames, with mocked
public metadata reads. Forced request-budget failure releases the core lease.
A mocked 503 retry loop confirms that transport retries consume the budget.
The initial preflight exposed a possible retry overshoot in a logical-call
counter. The corrected client checks before each actual request. All initial
preflight files remain in the ignored local spool.

The new cache preserves public replay clocks and both views. It will support
a fresh taxonomy sample and later training curation after full validation and
trajectory overlap checks. The shared external raw link and existing reports
retain their provenance. This bounded collection has a separate storage root
and supplies no model fit, candidate selection or deployment.

[Collection plan](../astra-submissions/analysis/field-snapshot-20261111/plan.json)
· [Preflight](../astra-submissions/analysis/field-snapshot-20261111/preflight.json)
· [Wrapper](../astra-submissions/experiments/field-snapshot-20261111/collect.py).
