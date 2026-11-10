# Cached move metadata recovery — November 10

**Complete metadata recovery:** original75325exits0 at21:40:41UTC.
All96,210target IDs matched; independent review passes. Arena v38unchanged.

The existing SSD move cache contains 96,210 game IDs / 91,796 whole trajectories
and 7,170,888 plies. A read-only consistent backup passes SQLite integrity,
syntax, hash and uniqueness checks. Six offline join/source-review tests pass.

The bounded pass joined public listing metadata to cached IDs and exact ply
counts for October 19 through strictly before November 10, 19:15 UTC. Preserve
unmatched IDs and original source hashes; compare the old 293 overlap. Six-second
pacing, 1,200 pages / 1,400 attempts, three-hour collection plus supervisor grace,
256 MiB private storage, terminal independent review. Publish source first.

This is metadata recovery, not restored raw replays or training-ready data.
Original recorded views, clocks and raw replay checksums remain unavailable.
The old ID-based split shares 328 trajectory groups; future splits must group
whole sequences. No fitting, GPU, canonical-store write or 326/live-bot change.
Private databases and source pages are excluded from publication.

[Full scope](../../../chatroom/328-astra-cached-move-metadata-recovery.md) ·
[fixed plan](plan.json) · [snapshot inventory](snapshot-inventory.json) ·
[preparation receipt](preparation-receipt.json).

## Original launch

Source `2b31c85861ce9a086e35ee92c2697d82fa44e95d` was verified on both
mirrors before launch at19:52:28UTC. At that launch checkpoint, original tool
session75325was collecting at six-second pace with no stderr. It subsequently
completed without a restart; the terminal result is recorded below.
All12metadata and62teacher dependency pins remain unchanged.
[Launch verification](launch-verification.json).

## Complete result and remaining data boundary

All**96,210games /91,796distinct trajectories /7,170,888plies**retain their
source hashes and now have public played names/versions, dates, results and
reasons. No unmatched IDs. The independent reviewer regenerates the complete
join from1025raw source pages, checks all96,210move hashes and4800known
metadata/trajectory overlaps, cursor/order/cutoff/ID/ply consistency, database
contents and six-second pacing.1082attempts, no cursor restart, minimum spacing
6.00010seconds;6493seconds total with both stages exit0 and no stderr.
161team/version panels and dated coverage are recorded in the audit.

This restores metadata for this old cache, not the original raw corpus. Views,
clocks and raw replay checksums remain unavailable. Complete rules replay
and whole-trajectory grouping remain required before broader learning;328
groups cross the old ID-based train/test split. `training_ready=false`.
Teacher62pins unchanged. No GPU/model/canonical-store or arena change.
Private SQLite databases and raw pages stay local; aggregate code/hash/audit
evidence only is public.

[Result](result.json) · [independent source/join audit](independent-review.json) ·
[terminal receipt](terminal-verification.json).
