# Recovered exports: intact historical data, not a refreshed training run

November 11 UTC. The read-only audit and independent index reduction are
complete. No dataset, split, source replay, model or arena submission changed.

| Product | Saved generation | Coverage | Split status |
| --- | --- | --- | --- |
| Raw journal snapshot | November 11, 08:12 UTC | 233,482 unique IDs; 31 old duplicate lines retained | Input inventory, not a train/test split |
| Episode shards | November 2, 11:41 UTC | 195,614 games; 391,228 color episodes; 192,165 distinct complete trajectories | Zero full-trajectory groups crossing splits |
| Move-model export | November 10, 01:21 UTC | 96,210 games; 91,796 distinct complete trajectories | 328 full-trajectory groups cross the legacy ID split |

The episode generation omits **37,868 games** now in raw storage. New
collection has therefore not automatically refreshed this training product.
These episodes belong to the imitation/RL pipeline; the separate move export
is input for fitting the native engine's opponent model. Neither is the
frozen model/table inside the deployed v38 ZIP.

## What passed

All three gzip files match their recorded SHA-256 hashes and decompress to
valid JSON. Every episode's metadata, version labels, array dimensions,
counts and color pairing reconcile to the manifest and journal snapshot.
The current code's feature/action/rules version labels match the manifest;
that comparison is not a new semantic validation of the encoder or rules.

| Episode split | Games | Episodes |
| --- | ---: | ---: |
| Train | 156,218 | 312,436 |
| Validation | 19,828 | 39,656 |
| Test | 19,568 | 39,136 |

Both episodes per game share a split and source-replay hash. Grouping by
complete move-sequence hash finds no cross-split trajectory. Copies within
a split are retained; the 195,614 IDs are not 195,614 independent trajectories.

The split is **seeded duplicate groups**, not chronological: the historical
manifest records 164 undated source games, which triggers the producer's
fallback. There are 328 missing played-version fields and 328 missing
opponent-version fields across episodes. This audit does not invent dates
or versions or silently move already-used examples between folds.

There are 808 games with technical or unknown terminations. Their stored
`value_valid` targets are all masked off. Their presence is not evidence
that those outcomes train the value head as ordinary wins/losses. Target
semantics and all other loss-mask behavior were not independently rewalked.

All three immutable move-generation files also match their saved hashes.
Every exported ID and complete move string matches its journal sequence
hash, with 81,907 train and 14,303 test games. The 328 overlapping trajectory
groups are the existing 281/328 limitation, not a newly discovered defect.
The independently grouped 336 cache is a different product. A future fit
must state which generation and split it uses; this audit does not change
the old holdout or recertify its accuracy as independent generalization.

A [supplemental alias check](legacy-alias-review.json) also finds the legacy
individual train/test files equal to this saved generation at the check
time. Future fitting should resolve the immutable generation pointer once;
two separately refreshed aliases are not an atomic pair.

## Verification scope and operational limits

Original session **51715** completed once in **133.74 seconds**, within its
900-second cap. It read 752,867,902 bytes through the hash counters and
decompressed 7,515,164,923 episode bytes. The counter covers the inputs hashed
in that pass, not every index/metadata reread or physical disk transfer.
The source code and all frozen inputs match their plan hashes.

Separate original session **74864** also exits zero. It independently sorts
the saved episode index to check both colors, source identity, fold counts,
raw-ID coverage, the missing-ID list and trajectory overlap. It rehashes the
move files and independently groups their records. The original core lease
is released. No rules engine, bot search, training or neural inference ran.

Successful reads show these saved generations survived this check. They do
not certify the disk, the next scheduled job, replay legality under changed
code, target correctness or future playing strength. Shared exports and the
normal daily service remain untouched.

## Concrete follow-ups for data review

- Keep these historical generations immutable; a refresh should publish a
  separate complete generation with source provenance.
- Investigate why the episode export has not advanced before spending on
  a new neural architecture. This audit does not identify the cause.
- Recover missing timestamp/version metadata from verifiable records before
  claiming a chronological split; preserve the original raw bytes.
- Use an explicitly grouped, newly defined holdout for future move-model
  claims; preserve the known legacy test and prior experiment outcomes.

[Frozen plan](plan.json) · [Execution](execution.json) ·
[Result](result.json) · [Independent index review](review.json) ·
[Auditor](../../tools/audit_training_artifacts.py) ·
[Verifier](../../tools/verify_training_artifact_audit.py).

Source snapshots, full episode index, uncovered-ID list and overlap maps
remain in `data/astra-spool/training-artifact-readiness-20261111/`.
No new export, fitting, GPU job, candidate, version, commit, push or website
deployment occurred.
