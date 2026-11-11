# All 164 legacy games: corrected review cohort

The metadata overlay now has a complete application check beyond its
two-game regressions. All **164 original games / 14,228 frames** exported to
**328 player episodes / 14,064 decisions / 28,128 observation events**.
The original run, session 87941, exited successfully in 5.24 seconds using
the existing pinned native library. No native code was rebuilt.

The private, isolated manifests are:

```text
data/astra-spool/legacy-metadata-cohort-20261111/before.json
data/astra-spool/legacy-metadata-cohort-20261111/corrected.json
```

The whole artifact is 5,641,073 bytes, including copied originals, both
exports and the retained overlay. It is kept on the SSD and excluded from
Git; the source, checks and summary are published here. No production
manifest or scheduled exporter argument was changed.

Every corrected episode has the real player/opponent IDs and played versions
from the saved API response. All 328 player IDs changed and all 328 played
versions were restored. Missing source dates fall from 164 to zero. Only 28
selected seats were actually IAmAVirus; the remaining 136 were other teams.

The baseline and corrected exports have identical actor records, targets,
stable folds, original source hashes and all metadata outside the four
identity/version fields. Both have zero candidate-move mismatches. The
shared actor/target digest in sorted game/color order is
`4603e2b30b8be92b173f6e3be0310012bd8a359529b8822ee7df98848f3a1a87`.
Raw files and the derived cohort journal remain byte-identical.

A separate standard-library reader checks emitted observations against
the recorded private views, decision indices and actions against the move
sequence, target boards against recorded truth, and metadata against saved
API responses. It also confirms all 164 canonical raw replay hashes still
match the original recovery. This reader does not reconstruct legality or
danger labels independently. The exporter itself uses the existing native
rules validator; no new independent referee certification is claimed.

With hash policy v1 and seed zero, the cohort has 125 train / 25 validation /
14 test games. These are stable group labels, **not an untouched holdout**.
All 164 selected seats lost, and these games were already in the historical
corpus. Use this as an auditable regression/inspection cohort; it is not a
representative sample for estimating our win rate or fitting an unweighted
opponent population. No model or playing-strength claim follows.

Source: [producer and shard comparator](../../tools/build_legacy_metadata_cohort.py).
Evidence: [plan](plan.json), [preflight source hashes](preflight.json),
[full-cohort result](result.json), [emitted-record audit](record-audit.json).
The [overlay integration](../corpus-metadata-overlay-20261111/README.md)
retains its original 44-case report. This run adds full historical coverage;
it does not reclassify any earlier experiment or update the daily dataset.
