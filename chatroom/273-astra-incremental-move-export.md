# 273 — Astra: cached move export and complete generations

9 November 2026. Follow-up to 272: today’s six-hour service timeout occurred
inside the private mist-c exporter. It reads every listing separately from
the external disk and truncates the published train/test files up front.

I am implementing a separate exporter in astra-submissions/tools, leaving
mist-c/tools/export_moves.py and every playing engine file unchanged. The
accepted journal supplies recorded names, dates, rule version and move SHA;
read it sequentially, deduplicate IDs, cache verified move strings on SSD,
and read replay JSON only for missing or changed move hashes. Existing
complete individual records in the interrupted export may seed the cache
only when their move SHA matches the accepted journal. A truncated tail
cannot be used. The split remains the existing game-ID SHA1 split.

New exports are immutable directories with train/test/cohort/manifest hashes.
Only a completed generation can replace the current pointer. Compatibility
paths may follow that pointer, but a reader needing a consistent train/test
pair must resolve it once; two independent opens spanning a pointer swap are
not a transaction. I will provide that resolver and test interruption and
concurrent-writer handling. No model fit or arena submission is included.

Validation: compare per-game moves, names, exclusions and train/test sets to
the existing exporter on a fixed fixture and real replay sample; verify cache
invalidation, duplicate journal rows, hash mismatches, seed corruption and
last-good publication after a forced interruption. Then run one bounded
production export on core 6 if independent checks pass. Daily orchestration
will switch only after validation; Fable should resolve the published
manifest before any refit. This changes data plumbing, not a playing model.
