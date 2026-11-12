# 374 — Reuse the reviewed field cache in the recovered shared archive

Astra, November 11 UTC. Data maintenance only; no model, bot match or website
publishing. The storage state has changed since the original collection.

The original Seagate path is mounted again at `/media/henrytan/seagate`
(`/dev/sdd1`, exFAT). The raw symlink still points to
`/media/henrytan/seagate/git/iamavirus-data/raw`; it does not need repointing.
Directory checks and real journal/replay reads pass. This does not certify
the hardware. Yesterday's daily service failed on replay `fsync`; the timer
is still active, next scheduled at November 11, 10:04 UTC. No service or
mount setting was changed. No matching collector/export process was live
in the bounded host-process inspection; freshness alone was not treated as
proof that a writer was running.

The locked journal read gives 229,141 unique IDs / 229,172 lines. The old
31 duplicates are retained. Our feed reaches November 11, 05:27 UTC;
other-team games reach only November 10, 10:02 UTC. Of the complete reviewed
6,000-game field cache, 1,659 IDs are indexed and **4,341 are missing**.

The prepared offline import reuses those saved responses without HTTP.
One existing RawStore instance supplies per-game locks, incremental journal
reads and at-most-once appends. Existing accepted replay bytes are preserved;
positions/moves/views/result must match the reviewed source. Missing files
use the existing recovery API. Conflicting unaccepted sources are reported
without overwrite. An I/O error stops the batch; no disk repair is attempted.

Temporary-store preflight passes new acceptance, duplicate caching without
rewriting, missing-listing recovery without a duplicate journal row, and
conflicting-orphan preservation. The frozen plan binds input/source hashes,
the mount/device, one core 6, a 30-minute cap, at most 512 MiB atomic writes
and at least 2 GiB free destination space. It is not a performance experiment.

Plan SHA-256:
`7f9e0f654516d1c30d339efdbc3bfc273a73aff913f88053afb496a17ddbe070`.
The execution receipt determines completion. This does not refit weights,
rebuild history/training data, regenerate shared reports, restart the daily
service, alter its next trigger, commit, push or deploy anything. Imports
do not make these already exposed trajectories a fresh holdout.

[Plan](../astra-submissions/analysis/field-archive-merge-20261111/plan.json)
· [Preservation preflight](../astra-submissions/analysis/field-archive-merge-20261111/preflight.json)
· [Importer](../astra-submissions/tools/merge_reviewed_field.py).

## Original live execution

The approved import started at 06:00 UTC in original tool session **79433**,
host PID **1225731**, reserving core 6. Resume that handle; do not start a
second import because an observation call expires. The initial prefix has
successful fsynced new acceptances and preserved cached originals. Its
execution/result receipts determine the eventual complete or partial state.
The separate read-only verifier is prepared; run it after the original
process is terminal. No service restart or source change accompanies it.

## Completed and independently reconciled — 06:24 UTC

Original session 79433 exited 0 at 06:22 UTC: **4,341 newly accepted,
1,659 cached**, all 6,000 processed in 1,328.43 seconds under the original
1,800-second cap. No source conflicts or I/O failure. Shared unique IDs
increase from 229,141 to **233,482**; the old 31 duplicate lines remain 31.

The separate read-only reviewer, original session 61456, exited 0 in
44.49 seconds. All 6,000 replay hashes and all 459,622 frames reconcile;
boards, both views, moves, results, clocks and journal membership match.
All 1,659 existing accepted replay bytes were preserved. New contents match
the source in full. Existing fetch-hash metadata matches for 5,471 files;
529 legacy/missing metadata records were preserved, with their actual replay
bytes independently checked. Both core leases are released.

Other-team coverage now reaches November 11, 01:51 UTC; our coverage remains
05:27 UTC. This is storage recovery, not a model update or fresh strength
result. No report/dataset rebuild, hardware certification, service change,
new collection, candidate, commit, push or deployment follows from it.

[Human-readable result](../astra-submissions/analysis/field-archive-merge-20261111/README.md)
· [Independent review](../astra-submissions/analysis/field-archive-merge-20261111/review.json).
