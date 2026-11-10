# Uploaded v38 monitoring checkpoint

Complete public metadata snapshot at 2026-11-10 15:56 UTC: active v38,
1919.16 Elo / rank 10; 294W–19D–209L / 522 games, score 58.14%.
No listed technical termination among losses.

Collected once with `astra-submissions/tools/metadata_recovery_snapshot.py`
(original tool session 89217, exit 0), seven sequential public GETs. No replay
download, shared raw-store write, new watcher or arena mutation.

`by-opponent.json` groups every listing by exact opponent ID, played version
and color. `since-1355.json` subtracts the previous complete snapshot's game
IDs after verifying that every old ID is present in this one. For each game,
our side is identified by team ID and version 38; a draw earns 0.5 and a win 1.
These are descriptive counts, not independent strength or causal estimates.

Leaderboard and game-list snapshots occur at different instants. Full
source-response and collector hashes are in `result.json`. The source metadata
has no boards or observations; this is not a replay/protocol health audit.
