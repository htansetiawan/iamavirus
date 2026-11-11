# Historical replay metadata overlay

The exporter can now consume the verified 164-game recovery without replacing
raw replay files or their accepted journal. The old importer had named 136
other teams' selected seats IAmAVirus; all 164 games also lacked dates and
played versions. This is data curation, with no strength claim.

The portable [overlay](overlay.json) is 96,051 bytes, SHA-256
`cf894da62d06b1da39dccae2cfe635b08301fe4efaf21ee93bbd7c0d3701ae5b`.
Its provenance pins the earlier recovery's review and receipts. The offline
[converter](../../tools/export_corpus_metadata_overlay.py) reconciled all 164
saved originals, responses, move identities and metadata receipts. It made
no API request and did not repeat the earlier board/view or rules audit.

The option applies exactly seven metadata fields: completion date, White and
Black names, real team IDs, and played versions. It binds each record to the
game ID, original raw-byte SHA-256 and complete move-sequence hash. Frames,
clocks, rules, results and training labels cannot be overlaid. Dates retain
their original nine fractional digits.

After merging this source change on top of
[PR 5](https://github.com/htansetiawan/iamavirus/pull/5), an explicitly selected
future export can use:

```sh
python -m learning.dataset --raw data/raw \
  --manifest data/manifests/reviewed-metadata.json \
  --version reviewed-metadata \
  --metadata-overlay astra-submissions/analysis/corpus-metadata-overlay-20261111/overlay.json \
  --split-policy trajectory-hash-v1
```

This command was **not run on production data**. No overlay remains the
default; the scheduled exporter still uses its existing arguments.
Each new generation stores the exact loaded overlay bytes and records their
hash, total/used/unused counts and original input path. Episode source hashes
continue to identify the untouched raw replay. Bad or stale input rejects
publication while preserving the previous generation.

All **44 functional cases passed**: 24 overlay cases and the 20 existing
split/publication/journal cases. Two genuine committed corpus games,
`13r3tgga` and `1b8luqb3` (197 frames, four episodes per export), reconstruct
the exact legacy source hashes. Tests compare actual shards before and after
correction: observations, actions, targets, raw files, journal bytes and
stable folds are identical; IDs and played versions are corrected, and the
undated count falls from two to zero. Parser rejection, stale-byte/move
rollback, CLI wiring and retained snapshots are also checked. The existing
pinned native library was reused without rebuilding it.

Restored dates can switch adaptive splitting to chronological splitting and
change assignments. Stable hash folds preserve membership for fixed seed and
fractions, but neither option undoes previous model exposure. No existing
holdout is declared untouched. These small functional exports are not a
production-scale I/O benchmark, model fit, game result or Elo estimate.

Evidence: [result](result.json), [test report](functional.xml),
[tests](../../tests/test_metadata_overlay.py),
[design](../../../chatroom/407-astra-source-bound-metadata-overlay.md), and
[handoff](../../../chatroom/408-astra-metadata-overlay-tested.md).

The later [full legacy-cohort application](../legacy-metadata-cohort-20261111/README.md)
materializes all 164 games as a separate review dataset: 328 episodes and
14,064 decisions, with zero candidate mismatches. A before/after comparison
and separate emitted-record audit pass. The published production generation,
models and old holdout claims remain unchanged.
