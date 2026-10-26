# Today's priorities — 26 October 2026

**Astra · Implementation and coordination checkpoint**

Henry asked us to fix the reporting bug and work upward through the practical
priorities. Fable published the main reporting/cohort/spec corrections; Astra
reviewed them, added timestamp boundary coverage, and found a more urgent data
integrity problem. The active arena engine remains v35.

## Work in order

| Order | Work | Owner and status | Completion criterion |
|---|---|---|---|
| 1 | Correct historical rating lookup and label cohorts | Fable's fix published; Astra's UTC-offset/fraction/invalid-date follow-up passes | Recomputed report uses strictly earlier snapshots and discloses missing/stale ratings |
| 2 | Prevent interrupted exports from corrupting training data | Astra implemented immutable generations and atomic manifest publication | Failure-injection tests preserve the previous manifest and shards; all new gzip files validate |
| 3 | Restore fresh, usable data | Astra's fresh move export and chronological curation complete; full episode rebuild running with a 90-minute cap | Verified counts/hashes and explicit split provenance, not merely repaired disk links |
| 4 | Restore unattended publishing | Astra's process-scoped GitHub credential selection passes stubbed tests | Actual push succeeds without switching the shared active account |
| 5 | Close existing experimental work | Astra audited the completed EP gate: 18W–3D–19L | No promotion claim; stale core reservation released; no further matches added |
| 6 | Choose one engine-facing learning experiment | Astra proposed a history-conditioned opponent prior combining class modelling with reusable hidden-threat motifs; Fable acknowledgement pending | One interface, frozen data, baseline, compute cap and rejection rule agreed |

The first five are fixes and completion work. They are not claims of increased
playing strength. The broad rebuild may still include historical undated games;
its manifest now identifies that split mode. Use the separately curated dated
move data for chronological model comparisons.

## What changed our assessment

All three old training shards were truncated gzip streams. The old manifest
claimed 299,662 episodes, but reading the files failed after 18,536 complete
episodes. The dataset builder had overwritten the live shards before publishing
the new manifest. Restoring the mount could not repair that. A failed rebuild
now leaves the published generation intact; hashes and record counts are
verified before replacing the manifest.

The new move export contains **85,435 games**, through October 26 10:12 UTC.
Its original game-ID split had **141 identical move sequences crossing
train/test**. Curation groups identical sequences and orders groups by their
latest completion: **67,853 train / 8,575 validation / 9,007 test**, with zero
cross-split duplicate sequences. Both colours of a game stay together, and
opponent-version coverage is recorded. This does not prevent every form of
opening similarity or replace a held-out-version evaluation.

The updated rating-flow report remains approximate: snapshots are around
12 hours old at the median. Raw opponent/version scores are more dependable
for choosing targets than small differences in estimated rating flow.
[Report and audit receipts](https://github.com/htansetiawan/iamavirus/tree/main/astra-submissions/analysis/p0-repairs-20261026).

## Recommendation for the first modelling experiment

**Improve the opponent prior first, without adding a new material guard.**
This is a proposed reconciliation of Fable's week-2 class model and Astra's
concealed-threat direction. Predict reusable behaviours from available history,
not a player-name lookup. Keep the existing search, evaluation and guard settings
fixed so a result is attributable to the modelling change.

Duck and Strongly Invisible are practical recurring targets; Crimson Fog tests
adaptation to an emerging opponent. Greek Gift remains a mandatory leader-facing
challenge, and Instructors/Mist plus ordinary positions provide controls. The
ranking is provisional: descriptive losses do not identify recoverable wins.

Previous global-prior refits improved held-out likelihood without passing the
playing gate. Therefore the new model must improve **decision-relevant threat
probabilities and action choices**, not just average prediction accuracy.
Preserve baseline offsets when fitting incremental features, exclude challenge
games from fitting, and evaluate full histories on both colours.

Proposed first cap: two CPU hours for data/fit diagnostics, then at most one
90-minute replay comparison if those pass. Report at the 24-hour committee
checkpoint. Full-clock matches require a separately pinned candidate and fixed
gate; the completed guard and EP runs are not extended. GPU training is not
needed for this first conditional-model pilot. A later compact policy/value
learner remains a separate challenger with an explicit deployment interface.

**Agreement status:** Fable's reporting corrections are delivered. Astra has
sent the combined model proposal and ownership request in chatroom 154; a
joint decision on that next experiment has not yet been recorded. Data repairs
and verification proceed independently while that reply is pending.
