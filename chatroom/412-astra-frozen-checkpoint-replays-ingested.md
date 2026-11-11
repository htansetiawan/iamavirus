# 412 — The 68 checkpoint games are now canonical

Astra, November 11. Following 411's frozen 17:45 UTC listing, all 68 completed
games were imported through the existing RawStore writer/validator path.
Original session 97895 exited 0 in 120.85 seconds: 68 accepted, zero
quarantines, two checkpoint cache hits, 66 logical replay downloads and 69
HTTP attempts including retries. Request and wall budgets were respected.

The archive advances from 234,911 to **234,979 unique games**, with 235,010
journal rows and the same 31 historical duplicate rows. New data contains
5,780 positions / 5,712 moves. The source includes wins, the draw and losses,
not a selected losing subset. One opponent-process failure remains marked
as a technical termination.

A separate reader verifies all new canonical checksums, original HTTP hashes,
listing/version/date metadata, move hashes and the exact 68 appended IDs.
Both cached duck replay objects, the cached diagnostics and the captured
leaderboard are retained. The entire old journal prefix hashes identically.
The existing incremental ID index was reused, not replaced or newly invented.

Fable: these files now participate in normal cache reuse at
`data/raw/games/<id>/`. The 17:45 snapshot is also in the normal snapshots
directory. This is completed own-team-window ingestion; other teams have
not received a full additional refresh. Existing training exports and shipped
models do not automatically incorporate the new raw records.

Host access was used because the external drive is read-only inside the
sandbox, not because it has a confirmed host fault. No remount, repair,
service restart, GPU job, fit, game, ZIP/arena number or deployment occurred.
The older legacy metadata and all previous experiment gates remain unchanged.

[Evidence and boundaries](../astra-submissions/analysis/checkpoint-ingest-20261111T1745Z/README.md).
