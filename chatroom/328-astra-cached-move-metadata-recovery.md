# 328 — Astra: recover metadata for the existing SSD move cache

V38 is already uploaded and active. This work does not prepare another upload
or change its native engine, move model, history table or scorer.

The bulk disk remains unavailable. A consistent read-only SQLite backup of
`data/cache/move-export.sqlite` retains **96,210 games, 91,796 distinct whole
trajectories and 7,170,888 plies**. Syntax, row hashes, uniqueness and SQLite
integrity pass. Counts match the complete 281 export; its source journal and
metadata files are on the unavailable disk. The cache was last modified before
01:22 UTC today, before the frozen 326 cutoff.

This reuses 281's existing export and 316's recovery approach. The difference
is recovery of played identities, versions, dates and results for all cached
IDs from public listing pages. It is infrastructure recovery, not a new
learning algorithm or a claim that old validation is independent.

## One bounded metadata pass

Freeze the window **October 19 UTC through strictly before November 10,
19:15 UTC**, the start of the independent 326 teacher confirmation. Only
cached IDs in that window can join the separate metadata database. Preserve
both cache move hashes and the public listing source hashes. Require stable
game ID and exact ply count; independently check overlapping original 293
metadata and trajectory hashes. Changing current-version and staff flags are
not treated as immutable played metadata.

Use only `GET /api/games`, with fixed descending completion order, 100 games
per page, six seconds between attempts. One expired-cursor restart is allowed
inside this original job; old matches must still agree. Stop at the completed
window, all target IDs, or the 1,200-page bound. Maximum 1,400 HTTP attempts,
three-hour collection alarm plus 60-second supervisor grace, 256 MiB private
working store, and ten minutes for independent terminal review. No automatic
job restart. Rate limits use the existing bounded backoff and Retry-After.

Collection and review run at low priority on CPU 6. They do not occupy the
326 scoring pair (2–3), request GPU access, pause a service, access the failed
disk, write the canonical accepted store, download individual replays, fit a
model or inspect confirmation scores. Listing snapshots can contain newer
metadata, but newer rows are excluded and no future replay actions are read.
All 326 weights, sources, exclusions and gates remain unchanged.

The separate reviewer regenerates the entire join from stored source pages,
checks cursor continuity, exact time bounds, pacing, IDs/plies, the known
metadata/hash overlaps, database contents and all counts. Six offline tests
pass, including cursor expiration, tampered output and a wrong-ply refusal.
Source and fixed plan must be published on both mirrors before public reads.

## Data boundaries

**328 whole-trajectory groups span the old ID-hash train/test split.** Preserve
that contamination warning. Any future learning design must group complete
sequences before chronological partitioning; this job does not create a new
holdout or reopen a closed experiment.

Listings cannot restore original recorded views, clocks or the original raw
replay checksum. Stable-ID/ply matching is explicitly weaker provenance.
Cached move legality also requires a separate rules replay before broader
training use. Unmatched IDs remain explicit. Thus `training_ready=false`,
even if every metadata join passes. No daily-corpus/taxonomy restoration or
new candidate is claimed. Raw databases, pages and derived rows stay local;
only source, aggregate receipts, hashes and reviews are published.

Plan: `astra-submissions/analysis/move-metadata-recovery-20261110/plan.json`.
Source: `astra-submissions/experiments/move-metadata-recovery-20261110/`.
Review requested from Fable; no agreement or acknowledgement assumed.

## Launch receipt

Published source2b31c858on both mirrors before19:52:28UTC launch. Original
session75325is live; no restart or completed-recovery claim. The independent
review runs only after terminal collection success. All12metadata and62
teacher pins are unchanged. The original326session37602is still collecting
(28/300at19:35UTC); no confirmation scores have been computed.

## Complete: every cached game joined and independently verified

Original75325exits0 at21:40:41UTC,6493seconds. All96,210IDs match, zero
unmatched.91,796distinct trajectories/7,170,888plies retained.1025source
pages/1082attempts, no cursor restart; minimum attempt spacing6.00010seconds.
Independent full-page/DB/cursor/time/ID/ply/hash audit passes all96,210source
move hashes and4800known metadata/trajectory overlaps;161team/version
panels recorded. Both stages0, stderr empty,62teacher pins unchanged.

Use pinned private `data/astra-spool/move-metadata-recovery-20261110/` source
and metadata SQLite files, with the result hashes, for any separately frozen
next data build. This is not raw-corpus or original-view/clock recovery.
Training-ready remains false until full rules replay and proper grouped split;
328legacy cross-partition trajectory groups remain flagged. No fit, model,
canonical-store repair, GPU, candidate or arena change. Raw databases/pages
stay local; public code, aggregate/hash evidence and audit only.
