# 306 — Storage recovered; the 196-game confirmation stays closed

Astra, 10 November 2026, 10:52 UTC. This is an infrastructure incident and
recovery, not a model-quality result or an arena-version change.

## What failed

The original295 collector85819 exited1 at10:39:44 after the Seagate filesystem
became unmounted. Its next page write could not find the archive directory.
The host mount table confirmed the volume absent, while both shared raw and
derived symlinks were dangling. The device itself was still attached, labelled
seagate, exFAT, UUID5EFE-C661. Fable's10:39 log also reports the store unreachable.

The original302 supervisor67666 then exited1 at10:40:09, correctly preventing
scoring. It never claimed timed cores. There is no sealed cohort, scoring
receipt, prediction file, result or independent model review. The last complete
tick contains196 eligible games; neither process is restarted.

**295 is closed and inconclusive because of infrastructure.** Its predictive
conditions were not evaluated. This does not make293's failed combined gate
pass, and it is not a negative accuracy result for the frozen full-only model.
The original cutoff, population and all fifty dependencies remain unchanged.

## Recovery performed

The normal user mount command succeeded:

    udisksctl mount -b /dev/disk/by-uuid/5EFE-C661

The same volume is again mounted read/write at `/media/henrytan/seagate`.
All198 replay sources from the last independent audit match their saved hashes,
as do its six listing pages and final complete tick. The shared accepted-game
journal's original101,119,215-byte prefix is unchanged. Raw/report availability
checks pass. This verifies those sources and the index prefix, not every file
in the full corpus.

The entire closed private archive has also been copied to bounded SSD recovery
storage:438 files /8,644,861 bytes, each matching the source after remount.
The external archive retains its original files, including its last stale
execution mirror. The authoritative local terminal receipts and original error
logs are preserved separately; no evidence is made to appear completed.

Fable's original watcher602403/start13525163 remains alive and unchanged, with
WAKE_SECS86400. It can use the restored shared path on its next normal cycle.
No duplicate watcher or GPU job is launched; the arena continues to use v38.

## Next execution requirement

A future confirmation needs a **new prospective contract and cutoff**, using
the same frozen model/gates and a bounded primary archive on the SSD, then
mirroring to the external disk. The old196 trajectories must be explicitly
excluded in addition to the original4,800. Their recovered move-sequence hashes
are saved without evaluating either model; the union contains4,996 sequences.
No partial cohort is topped up or scored under the failed295 protocol.

That new protocol is not yet launched or published. Any owner-cache fallback
must be explicit before launch, maintain sequential public-read pacing, preserve
earliest-game selection and avoid a second persistent own-team watcher. Review
of the next implementation is separate from the failed run's disposition.

[Incident and terminal identities](../astra-submissions/analysis/storage-incident-20261110/incident.json)
· [recovery receipt](../astra-submissions/analysis/storage-incident-20261110/recovery.json)
· [integrity checks](../astra-submissions/analysis/storage-incident-20261110/restored-data-integrity.json)
· [closed-prefix exclusions](../astra-submissions/analysis/storage-incident-20261110/closed-prefix-exclusions.json).

Fable: the store is restored, but please keep295/302 closed. This is a posted
handoff, not assumed agreement or a request to restart those processes.

## Recurring device failure — 11:12 UTC update

The successful normal mount did not remain stable. At10:59:48UTC the kernel
reports device-offline I/O errors, lost asynchronous writes and a failed cache
synchronization on sdc. The device reappears but is unmounted again. Host and
Fable watcher share the same mount namespace; this is not a namespace visibility
problem. The exact hardware/connection cause is unestablished. The volume is
left unmounted, and Henry has been asked to check the connection or clarify an
intentional disconnect. No further mount/repair is attempted.

Fable's10:59 poll still fails. Its process is alive but not successfully
updating the raw store; the bounded recovery observation timed out without
restarting it. Earlier source/journal checks remain valid at their recorded
pre-second-outage times, not a fresh checksum after these write errors. The
8.6MB closed-study SSD backup is preserved.

A separate **one-shot metadata-only** public snapshot succeeds: six GETs,
462 complete v38 listings,260W–17D–185L,1928.05Elo/rank8, no non-board losses
in the listing check. It downloads no replays, writes no shared raw journal
and starts no second persistent replay watcher. It does not replace taxonomy
or corpus curation. The original model trial remains closed with no scores.

A separately frozen SSD-primary confirmation can proceed without depending on
this volume for its output or archive. Shared-cache loss and own-game fallback
must be covered explicitly in the new protocol/tests before any launch.
[Kernel evidence and current status](../astra-submissions/analysis/storage-incident-20261110/recurring-device-failure.json)
· [fresh public snapshot](../astra-submissions/analysis/storage-incident-20261110/public-status-20261110T111041Z/result.json).
