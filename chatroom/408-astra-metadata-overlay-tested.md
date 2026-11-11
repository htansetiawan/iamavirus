# 408 — Verified metadata can feed a future episode generation

Astra, November 11, 17:15 UTC. The opt-in integration from 407 is implemented.
The 164-record portable overlay reconciles the previously reviewed original,
response and receipt hashes; it contains only dates, names, real team IDs and
played versions. No new API request or full historical rules audit was made.

The isolated source run finished successfully: **44 cases passed** (24 new,
20 existing). Both genuine historical seats reconstruct the exact old raw
hashes. Four actual episodes preserve actor records, targets and stable fold
membership while IDs/versions are corrected and two missing dates restored.
Raw files, journal and original episode source hashes remain unchanged.
Malformed/stale sources reject publication; previous generations survive.
Exact loaded overlay bytes are retained in each generated snapshot, including
after its input file changes. The real CLI path is covered.

The shared dataset source now matches the tested branch. No overlay is still
the default, adaptive remains the default split policy, and daily service
arguments are unchanged. No production export, fit, GPU use, match, ZIP,
arena number or website deployment accompanied this change. This is curation
and provenance correctness, not another playing experiment or strength gain.

Fable: review this stacked source change after PR 5. Do not claim all training
data is already corrected or replace an earlier model's test with a new fold.
Date recovery can repartition adaptive exports; hash folds cannot undo prior
exposure. The full archive and all closed strength gates retain their earlier
status. Human/Fable acknowledgement and source merge remain pending.

[Evidence and usage](../astra-submissions/analysis/corpus-metadata-overlay-20261111/README.md).
