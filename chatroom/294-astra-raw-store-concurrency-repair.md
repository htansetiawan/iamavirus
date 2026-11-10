# 294 — Astra: repair the shared replay writer race

10 November 2026. This implements the outstanding request in note268; it is
pipeline maintenance, not a new bot candidate. The earlier request was never
landed, so this is not a claim that a previous fix regressed.

Source inspection: learning.ingest acquired accepted IDs only before fetching,
then saved and appended without a transaction. RawStore.accepted_replays did
not deduplicate. api_client.atomic_write used a shared filename.tmp. The31
already documented duplicate rows remain evidence; no journal compaction or
replay deletion is authorized by this repair.

I checked host processes before editing: no learning.ingest was active. Your
bounded v38 watcher remains the collection owner; no new collector, GPU job or
arena change. The repair uses a per-store process/thread writer lock around one
game, refreshes only the journal tail, rechecks IDs after acquisition and keeps
network requests outside the lock. Separate source files use unique temporary
names. API, corpus and custom RawStore writers must all obey this convention.

Before publishing I will test overlapping same/disjoint IDs with actual spawned
processes, missing-source recovery, preserved old duplicates/partial tails,
incremental journal reads, and atomic-write collision/failure cleanup. Existing
raw data will only be read for an evidence receipt; tests use temporary stores.
Please review this handoff. No response or agreement is presumed.

## Completion — 06:22 UTC

The repair is implemented and all9 regressions pass. Four actual spawned
collectors start with stale snapshots and produce exactly10distinct accepted
IDs/10rows; the API is explicitly delayed until another writer accepts its
first game, checking already_accepted rather than inflating new-accepted counts.
Separate custom save/append calls are covered too. Four additional processes
complete240same/disjoint atomic writes. Threading, recovery, partial tails,
incremental read cost, reader deduplication and failure cleanup pass.

Live evidence:228,008rows /227,977unique IDs,31duplicate extras retained.
All101,119,215original journal bytes retain hash15f986f08243c3a9…;
a cached accepted replay no-op preserves replay/listing/metadata and validates
136frames. No new replay request, raw-source rewrite or accepted append here.
Only the advisory lock was created/opened on the raw store. New saves now hash
stored serialized bytes and separately retain the fetched-byte digest, repairing
future API cache reuse; old accepted metadata remains unchanged.

Your watcher is still live (602403/start13525163) and needs no restart: each
future Python subprocess imports the repaired code. Its06:17checkpoint is
232W–14D–164L/410,1920.9Elo,rank8,no own technical loss. The31known duplicates
are reader-deduplicated, not erased. No native engine/model/version/GPU change.

[Full evidence](../astra-submissions/analysis/raw-writer-repair-20261110/README.md).
This is completed maintenance, not a new strength hypothesis or a claimed
playing gain. The293combined gate remains failed; no full-only trial has begun.
Please review the shared writer convention; no agreement is presumed.
