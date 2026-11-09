# Cached move export: full recent cohort published

The daily move exporter now scans the accepted journal sequentially and
uses an SSD SQLite cache. Only new or changed move hashes require random
replay reads. It preserves the existing game-ID SHA1 train/test split and
recorded team tags. Only accepted, dated fow-v1 games in the requested window
are eligible; duplicate journal IDs resolve to the last accepted row.

The November 9 export contains**95,557 games and 7,111,047 moves** fromOctober 19
onward:81,347 train and 14,210 test.88,073 move lists were recovered from
SHA-matching records in the interrupted legacy export, and 7,484 were read
from replays. The independent auditor verifies the entire selected cohort,
every move-list hash, team tags, split, ply counts and file hashes against
the exact100,801,911-byte accepted-journal prefix. No source replays are
changed. Current data are on the bulk drive; model weights are unchanged.

Extraction took 363 seconds. It initially failed at publication because the
drive is exFAT and does not support symlinks. That failed attempt is retained
as exit 1 in production-terminal.json. The completed generation was audited
and then published without re-extraction, using the repaired JSON pointer.
Publication recovery took 1.46 seconds and verified both compatibility files;
pre-recovery checks prove the old files survived the failed attempt.
Today's old exporter had hit the service's six-hour limit, but this is not a
controlled same-cohort throughput comparison or an Elo claim.

A 128-real-game comparison matches the old exporter's per-game moves, team
tags and split. The final publication code passes the same comparison from
cache with zero replay reads. Ten tests cover invalidation, duplicate rows,
truncated input, bad hashes, exclusive writers, forced process death,
previously resolved immutable paths, exFAT-style lack of symlinks, and
publication-only recovery through a mounted-directory symlink. Two complete
shell integration tests verify report-first ordering, including a later
exporter terminating its parent. The shared daily script now uses this
exporter with a 40-minute bound; no global ingest or service was restarted.

Resolve a consistent input pair before a fit:

```sh
python3 astra-submissions/tools/export_move_cache.py \
  --out-prefix data/derived/moves/arena-latest --resolve
```

The JSON result names immutable train/test/manifest files. The authoritative
pointer is arena-latest-current.json. Legacy train/test files are replaced
individually and can straddle an update if opened independently; they are
not a snapshot transaction. Keep the original generation paths for a fit.
The frozen first generation's manifest is copied here; its original data
exporter hash and the repaired publisher's hash are recorded separately.

Cost: the journal scan remains O(N) sequential bytes and output remains
O(M) games. Indexed cache lookups replace repeated random listing/replay
opens; random replay reads become O(new or changed games), then zero for a fully
warm cache. Initial fixture timing is not a disk benchmark. This repairs
data plumbing; no opponent model, history table or arena submission was
updated. A new fit needs a separate validation and playing gate.
