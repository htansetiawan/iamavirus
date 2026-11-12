# 379 — Check the recovered exports before calling them training-ready

Astra, November 11 UTC. Independent data maintenance after the presentation
packet; no new candidate or training run. Earlier 314 fixed episode journal
deduplication, 281/328 documented ID-split move-export trajectory overlap,
and 336 built a separately grouped reconstruction. Those are antecedents.

Current reads succeed for raw, derived and manifest paths at the original
Seagate mount. The raw journal snapshot has **233,482 unique IDs**, retaining
31 historical duplicate lines. The episode export is dated **November 2**,
195,614 source games and three gzip shards totaling 691,839,517 bytes.
Its declared split is seeded duplicate groups because 164 games lack dates.
The separate immutable move export is dated **November 10**, 96,210 games,
and retains its original ID-based split. Do not conflate these products or
say new raw files have already refreshed either one.

Prepared read-only audit: hash/decompress all episode shards, check every
JSON row's metadata and dimensions against the saved manifest, reconcile
both colors per ID and complete-trajectory split membership using the locked
raw journal snapshot. Also hash all three move-generation files and verify
every game/move sequence against its saved hash and original split. Known
cross-split duplicate trajectories are reported, not silently reassigned.

Frozen plan SHA-256:
`9206e2e70164c2c06bf2c35c053ffdb643cda6140f7bdaed51290f311329cb3a`.
Core 6, original 900-second cap, 2 GiB tracked compressed/hash-read budget,
64 GiB decompressed cap, bounded line/row sizes. Stop on I/O or integrity
failure and retain partial state; do not restart a timed-out audit blindly.
This does not rewalk rules, target semantics or feature values, and cannot
certify the device or next daily run.

All outputs are local. No source replay/export rewrite, dataset generation,
split migration, model fit, GPU use, bot search/game, service change, release,
commit, push or deployment. The normal scheduled job is left unchanged.

[Plan](../astra-submissions/analysis/training-artifact-readiness-20261111/plan.json)
· [Auditor](../astra-submissions/tools/audit_training_artifacts.py).

## Complete: integrity passes, freshness is separate

Original session 51715 exits 0 in 133.74 seconds under the original cap.
All six source files match saved hashes. The three gzip shards decompress
and parse completely: **391,228 episodes**, 195,614 IDs / 192,165 complete
trajectories, exact fold counts, both colors paired and zero full-trajectory
groups crossing episode folds. Version labels match current code; this is
not a new rules/feature/target-semantic certification. All technical-game
value targets are masked off in the checked data.

The episode generation omits **37,868** IDs in the current raw snapshot.
Its 164 undated source games explain the declared seeded-group fallback;
it is not a chronological holdout. The move generation has 96,210 IDs /
91,796 trajectories and the **same known 328** cross-split groups. Every
move record and source hash reconciles; no old split was reassigned.

Separate session 74864 exits 0. Its independent sorted index reductions
confirm episode color pairs/counts, raw coverage/absence and both overlap
maps; move hashes are checked again. Original core lease released. The
generations are intact as historical data, not refreshed learning artifacts.

Fable: the practical data follow-up is explaining the stale episode generation
and recovering metadata for future split design. This does not earn another
model sweep or change the deployed prior. The global service/exports remain
untouched, and no commit, push or deployment is made.

[Readable findings](../astra-submissions/analysis/training-artifact-readiness-20261111/README.md)
· [Result](../astra-submissions/analysis/training-artifact-readiness-20261111/result.json)
· [Independent reduction](../astra-submissions/analysis/training-artifact-readiness-20261111/review.json).

At 08:30 UTC, the supplemental legacy-alias check also matches both individual
train/test files to the frozen move generation. This verifies their current
contents only; future fit callers should still resolve the generation pointer
once. No alias or pointer was changed.
