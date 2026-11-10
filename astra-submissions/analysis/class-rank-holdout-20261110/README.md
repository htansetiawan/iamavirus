# Observation-class ranking: independent holdout rejects the frozen configuration

The fixed quadratic rank operator does not pass its declared predictive gate.
No runtime patch, playing test, model fit or ZIP follows.

| Primary metric | Result | Required |
|---|---:|---:|
| Reference decisions after eight own moves | 3,704 in 80 games | ≥1,500 |
| Changed contexts / games | 1,729 / 79 | ≥200 / ≥30 |
| Conditional temperature-two gain over native | 0.009309 nats | ≥0.020000 |
| Gain over fixed linear ranking | 0.005978 nats | ≥0.010000 |
| Whole-game bootstrap 95% interval | [−0.005571, 0.023496] | lower bound >0 |
| Priority coverage / nonregression | all three pass | all three pass |
| Course, scalar, capture, mask and multiset checks | pass | pass |

Instructors has 37 primary games (+0.015451 nats), Duck 17 (+0.005336), and
HYPOTHERMIA 28 (+0.020174). These slices do not override the failed aggregate
conditions. Quadratic also trails linear on Duck. The earlier training signal
was +0.041416 on 94 selected examples; this independent panel uses all specified
reference decisions. The difference is not a controlled estimate of overfitting.

The frozen source/plan commit `c2072ab4f11baad421a06042db4a67d67187d3d0` was
verified on both repository mirrors before collection. The one collector
(session 23146, host PID 884478 / start 19527011) completed 80 trajectories in
88 public requests, using 2,311,699 bytes of bounded private SSD space. The
population is the first 80 eligible chronological unique trajectories in the
predeclared November 10 00:00–07:00 UTC window. All 4,996 earlier trajectories
are excluded. This is retrospective holdout evidence from fitting/rank
selection, not a prospective or globally never-seen-data claim.

Before inference, an independent source audit reconstructs the exact cursor
window, ten duplicate listing rows and the earliest eligible selection. All
6,771 replay frames / 6,691 moves match the course implementation. Then the
one native score (session 67520) checks every one of 210,216 alternate-action
class flags against the course rules, 1,471 capture-observation identities,
53,528 powered-mass comparisons and independent stable-sort assignments.
Maximum model scalar discrepancy is 1.02e-6; active-history discrepancy is
5.67e-7. A separate pass reconstructs all primary membership, cluster bootstrap,
metrics and gate decisions from the saved per-decision rows.

The complete source-audit → score → verify pipeline exits zero in about
20 seconds. Correct implementation does not make the predictive gate pass.
Cores 2–3 are released. Captures/masked values and class likelihood spectra
remain exact in this component; post-merge nonlinear guards, future caps,
history, time allocation, sequential posterior and playing strength were not
tested. The 307 prospective source/cohort/models/gates are unchanged and unscored.

`cases.json.gz` and `listing.json.gz` preserve exact original JSON bytes;
checksums are recorded in `artifact-manifest.json`. Raw immutable replays and
source pages remain in the bounded private working directory recorded in
`plan.json`; they can be verified by their cohort/fetch hashes. No external-disk
repair or shared-store write occurred. The initial sandbox-only PID lookup
failed to see host processes; a read-only host lookup recorded the same running
collector, with no restart or effect on the study.

See `result.json`, `independent-review.json`, `source-audit.json`, `pipeline.json`
and the [frozen protocol](plan.json). **Close these fixed ranking scores.** Do
not retune, extend the cohort, promote a favorable opponent slice or convert a
component result into an Elo claim. Wait for the separately frozen 307 result
before choosing another runtime change.
