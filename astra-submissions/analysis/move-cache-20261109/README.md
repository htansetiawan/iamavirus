# Move export: parity verified; full recent export prepared

The cache exporter matches the unchanged mist-c exporter on128actual games:
110train/18test, exact per-game moves and tags. A second pass after removing
only the disposable fixture's replay files completed from the cache with
zero replay reads. Local fixture timing is not an external-drive throughput
claim. Source IDs, hashes and the finite accepted-index prefix are in
real-parity.json.

Eight contract tests pass: filtering/split parity, warm cache without replays,
changed hashes and duplicate rows, an incomplete journal tail, corrupted and
truncated seed records, bad-replay rollback, malformed/empty input, a writer
lock, forced process death before publication, and stable previously resolved
paths after a later publication. Unit fixture construction initially needed
a correction for duplicate keyword arguments; the final eight-test run passed.

production-plan.json freezes one40minute export on core6 into the existing
arena-latest prefix, using complete individually SHA-verified records in the
interrupted legacy export to seed the SSD cache. The external replay archive
is read-only. Complete generations and compatibility links are the only
external-drive writes. No model refit, rollout data rebuild or arena release
is included. The plan/source will be published before launch. Results and a
separate full-generation audit remain pending.

For a consistent input pair, run:

```sh
python3 astra-submissions/tools/export_move_cache.py \
  --out-prefix data/derived/moves/arena-latest --resolve
```

Open the returned immutable train/test paths. Legacy aliases can cross a
publication between two independent opens; resolving once avoids that race.
The first read remains O(N)sequential journal bytes, and output is O(M)games;
SQLite uses indexed move-hash lookups and avoids repeated random file reads.
This is an I/O and publication fix, not an Elo or learned-weight claim.
