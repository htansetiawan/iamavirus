# Reviewed field data restored to the shared replay archive

November 11, 2026 UTC. This offline import is complete and checked. It
reuses the already reviewed 6,000-game cache; it makes no API requests and
changes no bot weights, history table, training split or arena submission.

| Checkpoint | Result |
| --- | ---: |
| Reviewed source games / frames | 6,000 / 459,622 |
| Newly accepted games | 4,341 |
| Already accepted games, original replay bytes preserved | 1,659 |
| Shared archive unique IDs before / after | 229,141 / 233,482 |
| Pre-existing duplicate journal lines before / after | 31 / 31 |
| Source conflicts or import errors | 0 |
| Games with different or missing destination clocks | 0 |

The original import exited successfully in **1,328.43 seconds**, within its
original 1,800-second cap. A separate read-only reconciliation then exited
successfully in **44.49 seconds**. It checked all source/destination hashes,
every board, both views, moves, result and frame index, and confirmed all
6,000 IDs in the accepted journal. New replay contents match the source in
full, including clocks and optional metadata. Both core leases are released.

The destination remains the original symlink target:
`/media/henrytan/seagate/git/iamavirus-data/raw`. No remount, symlink change,
service restart or disk repair was performed. The existing RawStore supplies
per-game locks, incremental journal reads and duplicate-safe acceptance;
this import reuses that machinery rather than introducing a second writer.
It wrote 112,819,588 bytes through 13,023 bounded atomic file writes.

The accepted feed now reaches November 11, **05:27 UTC** for our games and
**01:51 UTC** for other teams. These are maximum recorded completion times,
not journal-tail order. The source snapshot ends at the latter timestamp;
this import is not a new live-arena reading.

For 5,471 destinations, existing fetch metadata also records the matching
replay hash. The other 529 have legacy or missing fetch-hash metadata;
their actual replay bytes were still independently hashed and reconciled.
Existing records were preserved rather than rewritten to normalize metadata.

## What this does and does not repair

The shared raw archive is readable and this bounded write succeeded after
the prior I/O failure. That does **not** certify the disk or the next daily
job. The scheduled service, derived exports and old reports were not run or
changed here. Importing new files does not retrain the opponent model or
rebuild the empirical history binary shipped in v38.

The local cache's duplicates and overlap with earlier research remain
disclosed in the [source review](../field-snapshot-20261111/README.md).
Moving these games into the shared store does not make them an untouched
holdout. Website publishing remains disabled; no commit or push accompanies
this work.

[Frozen plan](plan.json) · [Preservation preflight](preflight.json) ·
[Original execution](execution.json) · [Import result](result.json) ·
[Read-only review](review.json) · [Review execution](review-execution.json) ·
[Importer](../../tools/merge_reviewed_field.py) ·
[Verifier](../../tools/verify_reviewed_field_merge.py).
