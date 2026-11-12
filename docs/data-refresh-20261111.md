# November 11: the data refresh is complete and checked

The scheduled refresh completed at **15:04 UTC**. Independent checks now
confirm its new episode files and incremental replay archive. The source is
the morning ingest's journal snapshot; this is not a live count of all games
in the arena.

| Product | Verified snapshot | Use |
| --- | --- | --- |
| Accepted raw sources | 234,911 unique games; 31 historical duplicate journal rows | Replay evidence and intelligence |
| Episode generation | 469,822 player episodes; 16,475,155 demonstrated decisions | Offline observation-policy and auxiliary-label training |
| Episode game folds | 187,250 train / 23,585 validation / 24,076 test | Identified partitions, with the lineage limits below |
| New replay archive | 39,297 unique replays; 164 MB compressed | Incremental backup through journal row 234,942 |

The episode scan checks all three shard-file hashes and gzip streams, every
JSON record's outer alignment, both colors, counts and technical loss masks.
Every game's demonstrated move history matches its raw-source move hash.
Independent index reductions confirm 228,748 complete trajectories, with no
trajectory crossing folds within this generation.

The archive scan validates the full gzip stream, every expected replay hash
and occurrence, the exact journal prefix and snapshot frontier. The 31 repeated
replay members correspond to preserved duplicate journal rows. Older archive
files and device health were not recertified.

## What a future learning comparison must preserve

There are still **164 undated original imports**. Their verified replacement
metadata corrects 136 games falsely attributed to IAmAVirus, but was not
applied to this generation. These files retain the original metadata and
seeded group split; they are not a chronological holdout.

Fold membership also changes across generations: **795 November 2 test games
are now in training, and 813 old training games are now in test**. This is
confirmed in the actual new shards. A future model comparison needs a fixed
holdout or explicit trajectory exclusions accounting for what each model saw.
These transitions do not establish that a particular trained model consumed
those earlier examples.

## Source fixes prepared after this snapshot

Three source reviews address distinct problems. Their options are present in
the shared working copy; no production generation or submitted model has been
updated from them.

| Source review | Resulting behavior | Validation and operational state |
| --- | --- | --- |
| [PR 4: corpus attribution](https://github.com/htansetiawan/iamavirus/pull/4) | New move-list imports preserve an unknown selected seat instead of inventing IAmAVirus and synthetic team IDs | Four real-path cases pass; cached historical raw files are preserved |
| [PR 5: stable trajectory folds](https://github.com/htansetiawan/iamavirus/pull/5) | Explicit `trajectory-hash-v1` assigns complete move sequences to stable folds for fixed seed/fractions | Twenty cases pass; adaptive remains the default; no daily-service argument changed |
| [PR 6: verified metadata overlay](https://github.com/htansetiawan/iamavirus/pull/6) | Explicit `--metadata-overlay` applies seven verified date/team/played-version fields to a future export, binding raw and move hashes | Forty-four cases pass, including PR 5's existing cases; default off; exact overlay bytes retained in each new generation |

These case counts overlap and must not be added as independent tests.
PR 6 is stacked on PR 5. Its 164-record asset reconciles the saved recovery
receipts; the integration tests use two real games, not a full production
export or a new all-corpus rules audit.

Restoring dates can switch adaptive exports to chronological splitting and
repartition games. Hash folds instead provide stable, nonchronological
membership with expected proportions. Neither operation erases an earlier
model's exposure to a game. The currently published generation and every
older result retain their original metadata and partition provenance.

## How this reaches the bot

Arena v38 reads its packaged move coefficients and history table. This refresh
supplies offline learning inputs. A new fit, its calibration/playing evidence,
a validated package and human arena activation are the steps that change the
deployed model. The retired CNN–GRU/PPO episode pipeline is separate from the
native engine's move-prior export.

The [cache prototype review](https://github.com/htansetiawan/iamavirus/pull/3)
records a fast warm path and a failed cold-fill gate. It has not been
integrated. The data checks themselves are not playing-strength evidence.

Sources: [episode scan and index review](https://github.com/htansetiawan/iamavirus/blob/astra/presentation-review-20261111/astra-submissions/analysis/daily-episode-generation-20261111/README.md),
[archive scan and receipt review](https://github.com/htansetiawan/iamavirus/blob/astra/presentation-review-20261111/astra-submissions/analysis/daily-raw-archive-20261111/README.md).
The original plans, executions and earlier negative results remain preserved.
