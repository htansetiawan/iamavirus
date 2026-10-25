# 111 — Astra: Oct 25 current standing and the latest loss pattern

Snapshot pulled from the repository's public-API cache at 2026-10-25 10:12 UTC;
the report was regenerated at 10:15 UTC over the ingested replay corpus. This
supersedes note 110's Oct 24 standings as the latest available view.

## Standing

IAmAVirus v35 is **#10 at 1881 Elo**. The teams immediately above it are
HYPOTHERMIA (1885), duck (1959), Mist Opportunities (1961), Instructors
(1985), Crimson Fog (2036), Decent Chess Bot (2095), Strongly Invisible
(2099), Knight Vision (2166), and Greek Gift (2354). The prior Oct 24 report
had us #8 at 1935; the current cached rating is 54 points lower and two places
lower. Treat endpoint rating deltas as snapshots, not a controlled estimate of
the effect of any one opponent or game.

Over the latest 24 hours, v35 scored **232W–10D–240L in 482 games (49.2%)**;
over seven days it scored **1721W–94D–1621L in 3436 (51.5%)**. The 24-hour
sample is poor against Greek Gift (1/12), Decent Chess Bot (8/40), Knight
Vision (5/36), Strongly Invisible (6/36), Crimson Fog (12/36), Mist
Opportunities (13/36), Duck (9/28), and Instructors (16/40). It remains strong
against TA Baselines A/S/P (60/70 combined). Sample sizes differ and the
smallest matchups are noisy.

## Recent behavior signal

In 840 games over three days against teams currently rated above us, our
taxonomy rates per 100 moves were 16.8 king moves vs 11.6 for those opponents,
4.3 king departures from home vs 3.3, 3.2 king threats vs 4.4, and 1.4 hidden
king threats vs 2.2. We also walked into unseen attacks at 3.2 vs 2.6 and
sacrificed at 2.8 vs 1.5. All **554 losses** in this slice ended by king
capture. This is an aggregate behavioral association, not proof that any one
term causes the losses. It does reinforce the next experiment should test
choices and full replies, rather than turn these frequencies directly into
global weights.

## Next measurement

Keep v35 as the reference. For any candidate, stratify exact replay choices by
loss, nonfatal, and random controls; then branch the candidate's changed moves
through the referee to measure whether the apparent safety gain survives
opponent replies. Track color and opponent version separately. Do not promote
from the one-ply risk gate or the small self-play samples already recorded in
notes 108–109.

Evidence: [`2026-10-25.md`](../astra-submissions/analysis/standing-20261025-current/2026-10-25.md),
[`2026-10-25.json`](../astra-submissions/analysis/standing-20261025-current/2026-10-25.json),
and the cached leaderboard snapshot
[`leaderboard.json`](../data/raw/snapshots/2026-10-25T101243.632817Z0000/leaderboard.json).
