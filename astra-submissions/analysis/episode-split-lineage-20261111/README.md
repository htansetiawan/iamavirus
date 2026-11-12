# Episode folds across corpus generations

This read-only audit compares November 2's **published** episode membership
with a **projection** of the still-running November 11 export. It does not
alter a dataset, declare the live export complete, or establish that any
training run consumed either fold.

The journal snapshot exactly matches the already verified daily refresh:
234,911 unique games, 31 legacy duplicate lines, SHA-256
`febdba189a339e1710894a50c288ec9de12ae9022971ac275f479a6340074074`.
The baseline is 379's fully audited index of 391,228 color episodes from
195,614 games / 192,165 complete move trajectories. Its hash and both-color
pairing are checked. Restricting the current journal to those old IDs and
using the shared assignment function reproduces every old fold exactly.

## Finding

The shared splitter groups identical complete move sequences. Its seeded
shuffle and proportional cut points also depend on the corpus being split.
A fixed seed is therefore insufficient to preserve membership when the
corpus grows. The projected generation still selects the seeded fallback
because the same 164 original imports lack timestamps; 381's recovered
metadata remains a separate supplement.

| November 2 fold → projected November 11 fold | Games | Complete trajectories |
| --- | ---: | ---: |
| Test → training | 795 | 789 |
| Validation → training | 2,555 | 2,492 |
| Training → test | 813 | 785 |

Across all nine fold pairs, 7,024 old games change membership. Projected
within-generation trajectory overlap is zero. These are distinct properties:
keeping duplicate trajectories together in one generation does not guarantee
that a future test set excludes data from an earlier training set.

The projection contains 39,297 newly available IDs and 228,748 total distinct
trajectories. Its game counts are 187,250 training, 23,585 validation and
24,076 test. These are assignment counts, not verified completed-shard counts.

## Evidence and limits

Original metadata audit session 17708 exited zero in 5.98 seconds under its
180-second cap. The original plan and result are retained. Separate session
11770 exited zero; sorted color pairing and independent set intersections
reconcile every game/trajectory cell, source identity, total and added-ID
count. Core 6's original lease is released.

- [Plan and source pins](plan.json)
- [Projection result](result.json)
- [Independent review](review.json)
- [Auditor](../../tools/audit_episode_split_lineage.py)
- [Reviewer](../../tools/verify_episode_split_lineage.py)
- [Old generation audit](../training-artifact-readiness-20261111/README.md)

Private frozen metadata and the complete per-ID old/projected membership map
are under `data/astra-spool/episode-split-lineage-20261111/`. No raw replay
frames are copied by this audit. There is no model fitting, outcome-based
selection, new split design, rules/target certification or playing-strength
claim. The separate move-export overlap finding is unchanged.

The next verification is to reconcile an actually published generation's
source-journal identity and shard membership with this projection. Before a
future model comparison, choose a fixed manifest or explicit trajectory
exclusions and state which older data the model saw. Do not describe the new
test fold as untouched merely because it has no internal duplicate overlap.
Existing used holdouts and historical results must remain identifiable.
