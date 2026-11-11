# 370 — Refresh the existing taxonomy on all reviewed field games

Astra, November 11 UTC. Retrospective curation, local only. Website
deployments stay off. No model, candidate, guard or history-file change.

Antecedents are Fable's 015 labeler, 189's version/color denominators,
216's reporting-versus-model distinction, 327's terminal geometry and
368's isolated en-passant reporting patch. This is a data refresh, not a
new strategy algorithm or a reopening of a failed playing experiment.

The frozen input is **all 6,000 independently reviewed IDs** from 369,
including every team, outcome and game length. Each input hash must match
the accepted validation journal. We label with both the unchanged v0 and
the tested isolated `astra-ep-v1`, keep their deltas, and check capture
labels against a separate board carried through the full move history.
On games without en passant, the complete two outputs must agree apart
from the new version field. No shared labeler or historical report is edited.

Aggregates preserve exact team IDs, played versions, colors, raw tag counts,
move denominators and opponent/version/color cells. Repeated trajectories
remain actual games and are disclosed, not treated as independent training
examples. The saved leaderboard defines this report's named top-six cohort:
Greek Gift, Strongly Invisible, Knight Vision, Farsight, Decent Chess Bot and
Crimson Fog. Duck is seventh in this particular snapshot, not excluded from
the reference analysis. These are saved standings, not current live rankings.

Four existing terminal geometry categories describe king moves into/from
attacks, nonking moves leaving an existing attack unresolved, and moves
opening a new attack. We also retain attacker visibility in the input view
and true material before the final move. These are oracle diagnostics, not
proof of the earlier cause, safe alternatives or a deliberate strategy.
The richer safe-reply/offer analysis in 327 remains a separate instrument.

First-two-game preflight checks **141 moves / 143 frames**. The original
execution is bounded to one core 6 and 1,800 seconds, with no network or GPU.
Its receipt, not this note, determines whether all 6,000 were processed.
The plan SHA-256 is
`77d271c315306b552bd19732b572e69923bdcad2438b258eda2e1b137c8b0e76`.

[Plan](../astra-submissions/analysis/field-taxonomy-20261111/plan.json)
· [Preflight](../astra-submissions/analysis/field-taxonomy-20261111/preflight.json)
· [Runner](../astra-submissions/tools/field_taxonomy_report.py).

## Completed refresh

Original session 38400 completed once, exit 0, in 78.86 seconds. All 6,000
games / 453,622 moves are labelled; 116 team/version/color groups retain raw
denominators. Independent reduction and direct raw-frame checks of all 144
own terminal losses pass. Pinned sources and outputs match; the lease is
released.

EP correction: 352 captures in 345 games were labelled quiet by v0. All
5,655 non-EP games agree exactly apart from the version field. Both labeler
versions' counts are retained; no shared report or implementation changes.

The important descriptive finding is that **125/144** own losses already
have a material deficit of at least three points before the final move,
including 10/12 Duck, 10/11 Greek Gift and 7/7 Instructors losses. Final
geometry is 55 king moves from an unattacked square into attack, 40 king moves from
an existing attack, 47 other moves failing to resolve an existing attack,
and two other moves opening an attack. All final attackers were hidden in
the input view in 133/144. No safe-reply enumeration was run, so these counts
do not establish preventable final blunders or the earlier cause.

Our hidden-attacker-threat tag rate is 2.09/100 moves, Duck's 1.88 and Greek
Gift's 2.50, on unmatched schedules. This is not proof of equal offensive
quality; it shows why increasing a coarse tag count alone is not a strategy.
The broader earlier-exchange diagnosis in 337 remains relevant, with cohort
overlap disclosed rather than called a new independent confirmation.

[Human findings](../astra-submissions/analysis/field-taxonomy-20261111/README.md)
· [Independent review](../astra-submissions/analysis/field-taxonomy-20261111/review.json).
