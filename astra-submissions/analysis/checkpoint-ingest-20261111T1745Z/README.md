# Frozen checkpoint games are now in the canonical cache

All **68 completed games** from the November 11, 12:45 p.m. Boston checkpoint
are accepted through the existing `ingest_replay` transaction and validator.
The original worker session **97895 exited 0**, completing in 120.85 seconds.
No replay was quarantined.

| Product | Before | After |
| --- | ---: | ---: |
| Unique accepted games | 234,911 | 234,979 |
| Accepted journal rows | 234,942 | 235,010 |
| Preserved historical duplicate rows | 31 | 31 |
| Frozen-window game IDs in the accepted cache | 0 | 68 |

The new game directories contain **5,780 recorded positions / 5,712 moves**
across 205 files, about 2.07 MB. Two replay responses were reused from the
checkpoint cache; 66 logical replay fetches required 69 HTTP attempts,
including retries. The captured technical-failure diagnostics and already
fetched leaderboard snapshot were also retained without new API requests.

The capture includes 43 wins, one draw and 24 losses from v38's perspective.
Its 67 normal terminations and one opponent-process failure remain explicitly
classified. Acceptance of that technical replay does not make its result a
normal policy/value demonstration; downstream training validity masks remain
the existing pipeline's responsibility.

## What was checked

The frozen plan pins all IDs, the completed-game listing, the importer
source and the existing native library. Before each transaction, replay
identity, played team versions, result, reason and ply count must match the
listing. New data uses the standard writer lock, native validation, checksum
metadata and append-once journal path.

A separate standard-library reader verifies all 68 stored replay checksums,
original HTTP-body hash retention, listing and journal metadata, complete
move hashes and the exact newly appended IDs. Both cached duck responses
remain equal as JSON; the cached diagnostic and leaderboard also match.
It independently rehashes the old **104,270,050-byte journal prefix** and
confirms it is unchanged. No duplicate row was introduced.

The existing accepted-ID index read **104,301,036 bytes** in total: the
starting journal and its appended tail. This is reuse of the existing
incremental index, not a new algorithm or a whole-job I/O benchmark; the
snapshot and audit perform their own reads.

## Scope and use

The new records are under `data/raw/games/<id>/`. They cover the frozen
checkpoint's own-team window; this is not a full refresh of every team.
The [source checkpoint](../arena-checkpoint-20261111T1745Z/README.md) remains
a dated observational result, not a new-engine comparison or a fresh
holdout. Its two cached duck replays will now be reused by ordinary ingestion.

The published 469,822-episode generation, fitted move coefficients, empirical
history file and arena package were not rebuilt. The legacy 164-game raw
metadata remains unchanged; its separate reviewed overlay is still opt-in.
No GPU, match, release number, service or website deployment was changed.

The external archive was writable on the host. Its sandbox-only read-only
view was already distinguished in 411; this run needed host access for the
authorized canonical writes. No disk repair or remount occurred.

Evidence: [frozen plan](plan.json), [source preflight](preflight.json),
[original worker result and receipts](result.json),
[separate cache/journal audit](record-audit.json), and
[bounded importer source](../../tools/ingest_checkpoint_window.py).
The runner deliberately rejects a changed preflight journal or an existing
output directory; do not rerun this completed write transaction as a test.
