# Seagate unmount interrupted the first prospective run

At10:39:44UTC the original295 collector exited1 while writing page010 because
the external volume was unmounted. The original302 controller exited1 without
scoring.196 eligible games were collected; no cohort or prediction result was
created. This is an inconclusive infrastructure failure, not a predictive gate
failure or a basis for promotion. Neither process is restarted.

The attached exFAT volume5EFE-C661 mounted successfully through normal
`udisksctl mount` at its original path. Recovery checks verify198 saved replay
hashes, six current listing-page hashes, the complete tick9 hash and the original
101,119,215-byte shared-journal prefix. The check does not checksum every corpus
file. Shared raw/derived paths and report-input checks work again.

The closed archive is duplicated under the gitignored
`data/astra-recovery/prospective-full-prior-20261110-closed`:438files,8,644,861bytes,
all matching the post-remount source. Original external files and stale mirror
are preserved. Local original terminal receipts/error logs remain authoritative.

closed-prefix-exclusions.json reconstructs196 unique eligible trajectories
without any model scores. Adding them to the original4,800 gives4,996 unique
sequences for exclusion from any separately preregistered future trial. The old
cutoff/population/weights/gates are not changed. A new bounded SSD-primary
collection design is required before a fresh prospective attempt.

See incident.json, recovery.json, recovered-archive-manifest.json and
restored-data-integrity.json. Fable's existing watcher remains the owner and
was not restarted. No GPU, new candidate, archive version or arena action.
