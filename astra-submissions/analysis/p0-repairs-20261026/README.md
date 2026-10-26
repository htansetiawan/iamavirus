# P0 repairs and fresh modelling data — 26 October 2026

Fable delivered the main reporting correction in `2be37ce`; Astra reviewed and
hardened it, fixed interrupted dataset publication and unattended publishing,
and curated fresh move data in `e977638`. These are data/engineering repairs,
not playing-strength improvements. See [today's priorities](../../../docs/priorities-20261026.md).

## Delivered and verified

- **Reporting:** parsed UTC instants, including offsets and microseconds;
  strictly earlier snapshots; malformed/missing data handled; latest snapshot
  selected by time. Fable's explicit historical/current cohort labels retained.
  The recomputed report is in `recomputed-report/` and the shared daily reports.
  Rating expectations are approximate: median snapshot age is about 12 hours.
- **Dataset publication:** unique generations, closed gzip streams read to EOF,
  count checks, compressed SHA256 hashes, fsync and atomic manifest replacement.
  An existing manifest symlink stays a symlink. Tests inject an episode failure,
  truncated gzip trailer and manifest replacement failure; prior published
  files remain unchanged.
- **Unattended push:** origin-owner token scoped to the script process when no
  explicit GH_TOKEN is supplied. The shared active account is never switched.
  Tested fake git/gh normal, divergent and explicit-token cases; actual push
  published `e977638` successfully through the updated script.
- **Tests:** 19 targeted tests pass; shell syntax passes; 14 docs pages render.
  `verification.json` records the commands and result.

## Data integrity and recovery

`corrupt-shards-before.json` records the old manifest and shard hashes.
All three gzip streams failed at EOF: train 14,323/239,504 complete episodes,
validation 2,106/30,300, test 2,107/29,858. The Oct24 interrupted in-place build
had replaced the files while leaving the older manifest. The corrupted files
are retained as evidence; a successful new generation supersedes their use.

`data-preflight.json` records 32 recent games producing 64 episodes through the
new publisher in 0.65 seconds. It is a small throughput pilot, not a reliable
full-build runtime estimate.

`full-rebuild-run.json` and `full-rebuild-complete.json` record successful
completion at 15:27:46 UTC, exit code 0, after about 31 minutes. The publisher
read every gzip to EOF, verified counts and hashes, then replaced the manifest.
The repository symlink is preserved. Cores 0–1 are released; no GPU was used.

| Split | Games | Episodes | Decisions |
|---|---:|---:|---:|
| Train | 130,220 | 260,440 | 8,958,883 |
| Validation | 16,479 | 32,958 | 1,124,136 |
| Test | 16,228 | 32,456 | 1,123,865 |
| Total | 162,927 | 325,854 | 11,206,884 |

The immutable generation occupies about 571 MB compressed. The completion
receipt pins its manifest and shard hashes; `full-rebuild.log` is the terminal
run log. No further full scan is needed to establish successful publication.

The broad historical corpus has 164 accepted records without dates, so its
existing splitter falls back to seeded whole-sequence groups. That behaviour
is now disclosed in the manifest. Do not use that corpus as evidence of a
chronologically held-out result; the separate modelling export below supplies
the dated comparison.

## Fresh conditional-move data

`move-export.json` pins the existing exporter and its fresh 85,435-game output.
It includes the latest cached games through Oct26 10:12 UTC, retaining the
exporter's `fow-v1`, minimum-length and baseline filters. This is not the entire
162,927-record episode corpus.

`curated-move-export.json` pins a separate immutable curation. Identical complete
move sequences are grouped, assigned by their latest date, and kept entirely
in one split. The original game-ID partition had 141 duplicate sequences across
train/test; the curated data has zero. Both colours stay in the same game split.

| Split | Games | Current duck v6 seats | Greek Gift v25 seats | Crimson Fog seats |
|---|---:|---:|---:|---:|
| Train | 67,853 | 4,647 | 2,008 | 0 |
| Validation | 8,575 | 887 | 681 | 164 (v1) |
| Test | 9,007 | 936 | 621 | 976 (v1/v2/v3) |

Training groups end at Oct22 08:50 UTC. Older copies of repeated games follow
their latest copy into validation/test, so their earliest dates can precede
the training cutoff. Do not inspect test outcomes to tune candidate parameters.
Crimson is absent from training; validation contains its v1, while v3 is only
in test. Decent v7 is also absent from training, present in validation/test.
These provide explicit generalisation slices without pretending the opponents
are identifiable in the live bot protocol.

Generated bulk files remain on the configured storage drive; the receipt gives
their exact paths and hashes. No model was fitted and no arena release changed.

## Existing EP experiment closed

The prior 40-game run is audited and published:
[18W–3D–19L, no promotion evidence](../ep-target-inference-20261025/completed-gate-report.md).
All 3,374 frames verify; one actionable legal EP opportunity, zero EP choices.
Cores 4–5 were released. No new games were added.

## Coordination

Fable's note153 acknowledges the core reporting/spec corrections. Astra's
notes154–155 propose the next single model interface and ownership split;
explicit agreement on that next experiment remains pending. Infrastructure
fixes do not silently authorise a GPU run or a new tournament. The human
24-hour checkpoint remains the decision boundary for extending the next pilot.
