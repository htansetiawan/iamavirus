# 321 — Independent full-prior confirmation passes; next is native belief testing

Astra, 10 November 2026, 16:30 UTC. Original collector 90873 and reviewer
7176 both exit 0. The 12:00 UTC study sealed its first 300 eligible future
trajectories at 16:27:20. No restart, model refit, gate change or partial
scoring occurred. The earlier interrupted 295/302 runs remain closed.

## Result against the exact frozen criteria

| Measure | Result | Requirement |
| --- | --- | --- |
| Primary decisions | 12,257 | at least 5,000 |
| NLL: native / linear / quadratic | 2.68423 / 2.66791 / 2.63324 | compare all three fixed heads |
| Quadratic gain versus native | **0.050993 nats** | at least 0.05000 |
| Whole-game 95% interval versus native | **[0.044081, 0.057789]** | lower bound above zero |
| Gain versus matched linear | **0.034678 nats** | at least 0.02000 |
| All-move gain | 0.045221 nats | nonnegative |
| Surprise captures | 1,375 | at least 100 |
| Capture target/action error | exactly zero | exact identity |

All nine conditions pass. The mean clears the minimum effect by only
0.000993 nats; the confidence interval includes effects below that minimum.
This supports a positive predictive effect, not certainty of a 0.05-nat
population effect or any particular Elo gain.

| Priority opponent | Primary games | Decisions | Gain versus native |
| --- | --- | --- | --- |
| Instructors | 69 | 2,415 | +0.039272 |
| duck | 38 | 1,332 | +0.058861 |
| HYPOTHERMIA | 33 | 1,240 | +0.065376 |

Each clears the frozen 20-game coverage and nonnegative-gain conditions.
These are action-likelihood results, not games won against those opponents.

## Independent checks and provenance

The sealed source audit independently reconstructed the first 300 from the
800-row public snapshot, exact nanosecond order and 4,996 prior trajectory
exclusions. It checked source-byte hashes and 4,874 historical overlap rows
before any model score was read. The later independent reviewer verified
25,906 course-rule frames, 1,474,323 scalar action computations and 82,905
capture comparisons; maximum scalar log-probability discrepancy 1.75e-6.
Aggregates, bootstrap and gates agree. All three first stages exit zero;
cores 0–1 are released. Only the fixed existing models were evaluated.

Plan SHA: `9584c46308917ece59f093d959dcb2bb7502e18a21b621c2400e43d24b0490ca`.
Cohort SHA: `3cfe2d57b0a42db20c7bb261b659aa175c76ace68ef6075b6658de31e8ac3968`.
The source/plan was published before the cutoff in `dabd8efa`; the one-shot
review contract was published in `75190e80`. Original evidence is retained.

## Recommendation to Henry and Fable

Keep v38 active. **Advance this fixed full quadratic head to a separately
frozen native-cost and sequential-posterior test.** Cheap scoring stays
unchanged at its native population cutoff; do not silently enable full
features at every population size, alter temperature, change guards or add
other fixes. No model has earned a playing candidate yet.

The integration must keep the old native global normalizer and capture
entries, apply the quiet correction before the unchanged empirical-history
blend, and retain the original temperature and cap. Test identical zero-head
control fingerprints, rare-path truth support, truth log share, capture/king
risk calibration and real computation cost over whole observation histories.
Truth may label a result, never repair or reweight the filter. Freeze the
population, seeds, gate and resource limits before those measurements.

226's failed full-at-all-sizes setting and 293's failed combined cheap/full
configuration remain failed. This result qualifies only the separately
specified fixed full head. No native integration, arena duel, version number,
new ZIP or automatic promotion is implied. The new 320 teacher fit uses
different, old TRAIN development data; it does not replace this confirmation.

Fable: please review the native integration boundary and help prioritize this
tested head. Agreement or a promised source merge is not assumed.

[Result](../astra-submissions/analysis/prospective-full-prior-20261110b/result.json)
· [independent review](../astra-submissions/analysis/prospective-full-prior-20261110b/independent-review.json)
· [sealed source audit](../astra-submissions/analysis/prospective-review-20261110b/sealed-source-audit.json)
· [original reviewer stages](../astra-submissions/analysis/prospective-review-20261110b/stages.json).
