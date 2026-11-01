# Evening arena data and intelligence refresh

Completed 2026-11-01T23:42:49.218401+00:00. The bounded newest-600 all-team query fetched and validated **455 new replays**, reused 145 cached games, and recorded no errors or quarantines. The accepted archive grew from 191,335 to **191,790** games. This is a bounded refresh, not proof that the whole archive is synchronized.

All 455 new games involve other teams: our recent games were already cached. Their completion times span 2026-11-01T20:36:18.129109613+00:00 through 2026-11-01T23:33:02.761184259+00:00. The compressed JSONL retains 33,334 per-move annotations, both sides' raw tag counts, played versions and replay hashes. Every replay hash and per-side move denominator was checked. `archive.json` pins compressed and uncompressed bytes; decompress with Python gzip or gzip -dc.

The saved public leaderboard at 2026-11-01T23:33:07.460373+00:00 lists IAmAVirus at rank 12 among rated visible teams, **1896.73 Elo**, active arena **v37**, with active-version record 68W–6D–62L. These are snapshot values, not a live claim or causal estimate of the version's effect.

The data are annotated for offline investigation. No model fit, history-table rebuild, threshold change, regression-suite replacement or deployed update occurred. New queen diagnostics use the complete cached time window, including already-cached games; selecting only newly downloaded games would accidentally omit our team.

`refresh.json` and `refresh.log` preserve the acquisition receipt. Original process handle 8879 exited successfully. An earlier empty-log interpretation was corrected: redirected stderr was buffered, so an empty log did not imply the API was stalled.
