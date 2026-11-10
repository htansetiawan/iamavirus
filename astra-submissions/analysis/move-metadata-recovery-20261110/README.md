# Cached move metadata recovery — November 10

Status: original75325launched19:52UTC and remains collecting; recovery and
independent terminal audit are incomplete. Arena v38 is already uploaded.

The existing SSD move cache contains 96,210 game IDs / 91,796 whole trajectories
and 7,170,888 plies. A read-only consistent backup passes SQLite integrity,
syntax, hash and uniqueness checks. Six offline join/source-review tests pass.

The bounded pass will join public listing metadata to cached IDs and exact ply
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
mirrors before launch at19:52:28UTC. Original tool session75325is live,
collecting at six-second pace, with no stderr so far. This is not completed
recovery. All12metadata and62teacher dependency pins remain unchanged.
[Launch verification](launch-verification.json).
