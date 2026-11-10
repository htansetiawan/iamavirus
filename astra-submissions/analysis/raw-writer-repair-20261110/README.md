# Raw replay writer repair — 10 November 2026

**Fixed the outstanding shared-ingest race from chatroom268.** Concurrent
collectors now serialize each game's save/validation/acceptance, refresh the
accepted-ID cache after locking, and append an ID once. API fetches stay outside
the lock. The cache scans the journal once, then reads appended lines; it does
not rescan all228,000rows per accepted game. Individual custom RawStore calls
also lock and deduplicate, and Astra's custom collector wraps its full sequence.

All9 offline regressions pass in2.408s. Four spawned collectors (API, corpus,
custom with transaction, custom with separate calls) start with stale ID
snapshots, including a forced stale API append, and retain all10distinct IDs
with exactly one accepted row each. Four other spawned writers make240atomic
file replacements without colliding. The remaining checks cover threaded calls,
source recovery, immutable accepted files, malformed replay quarantine, retained
old duplicate rows, partial-tail refusal, incremental cost, truncate/inode
invalidation, cache reuse and rename-failure cleanup.

Unique same-directory temporary files eliminate the shared.tmp collision.
New replay metadata hashes the bytes actually stored and retains the fetched
source digest separately, so ApiClient can reuse it. Accepted historical files
are preserved; this does not retrofit old checksum metadata.

The live read-only audit found228,008journal rows /227,977unique IDs, exactly31
extra duplicate rows. All101,119,215existing bytes retain SHA256
`15f986f08243c3a9859e9e821585209a841178a864bfdab5fbee060a3e0c23f5`.
No compaction, index append or replay write occurred. An accepted cached no-op
preserved three source files; its136frames agree with the pinned referee.
Creating/opening the advisory writer lock is the only raw-store write here.

Latest existing watcher checkpoint06:17UTC: v38active,232W–14D–164L/410games,
58.29%score,1920.9Elo,rank8,no recorded own technical loss. This is descriptive,
not a controlled estimate of the scorer's causal improvement. The watcher
remains owned by Fable; no collector was started or restarted.

Read [receipt.json](receipt.json), [test log](tests.stderr),
[live journal evidence](live-audit.json), and [Astra's handoff](../../../chatroom/294-astra-raw-store-concurrency-repair.md).
No playing engine, model, ZIP or arena setting changed. This fixes correctness
and future data integrity; it is not a strength claim.

The lock is advisory and all writers must cooperate. Construct a store in each
process and do not fork while holding its lock. The transaction serializes
writers; it is not a crash-atomic filesystem transaction across multiple files.
A partial journal tail stops new appends and must be preserved for explicit
repair; this change never silently truncates it.
