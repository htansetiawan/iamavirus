# Refresh yielded to the active daily pipeline

2 November 2026. Closed before ingestion. Original tool handle 63185 exited 1
while acquiring the shared daily lock. It spawned no ingestion child and
downloaded no games. The original exception is `BlockingIOError: [Errno 11]
Resource temporarily unavailable`. The lock was not bypassed and no retry ran.

A host check confirms `iamavirus-daily.service` is active in its oneshot start
phase: live parent 468042 runs `daily_refresh.sh`, with child 478939. The log
reported dataset construction at 182,000 of 195,614 source games at 11:38 UTC.
This is evidence that the shared pipeline is working, not evidence that its
whole refresh/export/archive/report run is complete. Its processes remain
untouched.

The isolated planned latest-400 refresh sources and hashes are retained here.
They make no changes to the current model, history table, guards, experiment
244, or arena. Core 6 is released. The brief bookkeeping failure before polling
the original handle is recorded in `closure.json`; no publication happened in
that failed bookkeeping attempt.

## Daily pipeline completion and active-archive mapping

The shared service subsequently finished at 11:49:59 UTC with exit 0 and no
logged failed step. The rebuilt manifest records 195,614 source games, and the
archive step reports 9,338 games in its daily increment. This is pipeline
completion evidence; the archive has not received a second full content audit.
The earlier Astra lock refusal remains closed without any retry.

The intelligence status now resolves the snapshot's active arena version
through the shared release map and checks the mapped local ZIP hash. It keeps
v35 as a separate comparison archive. For snapshot v37 it verifies ZIP
`41e02e280b61`, its model member, and the 359,889-record history table. Unknown,
ambiguous or hash-mismatched mappings stay unresolved. The public API does not
expose the uploaded bytes' checksum, so this is repository provenance rather
than independent verification of the server's ZIP. Eight relevant tests pass.
`daily-completion.json` records the service, manifest, tests and artifact hashes.

The previous analysis publication, commit `cb7b608`, is confirmed in both
repository mirrors at `bc54cd2`; no publisher restart was needed.
