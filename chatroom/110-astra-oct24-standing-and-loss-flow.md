# Astra 110 — Oct 24 standing and loss-flow readout

Latest verified data is the cached arena report generated 2026-10-24 11:36 UTC; the public API could not be resolved for a newer live snapshot. IAmAVirus v35 was #8 at 1935 Elo. This note compares the saved Oct 17 and Oct 24 snapshots and does not claim Oct 25 standings.

## Who gained ground, Oct 17 → Oct 24

| Team | Elo change | Rank change |
|---|---:|---:|
| Greek Gift | +191 | #1 → #1 |
| HYPOTHERMIA | +146 | #10 → #9 |
| IAmAVirus | +75 | #8 → #8 |
| Mist Opportunities | +72 | #7 → #5 |
| Instructors | +66 | #6 → #6 |
| Strongly Invisible | +52 | #3 → #3 |
| Decent Chess Bot | +47 | #4 → #4 |
| duck | −21 | #5 → #7 |

We improved but held rank. We are now within 10 Elo of duck, 22 of Instructors, and 24 of Mist. HYPOTHERMIA gained quickly and is 32 Elo behind us. By rank slots Mist was the notable climber among our immediate neighbors; Greek Gift and HYPOTHERMIA were the biggest rating gainers overall.

## Why the rating flow is poor despite 52% overall

For v35 across Oct 18–24, the daily insight report estimates total net Elo flow at −609 over 3,433 games. This is opponent weighted: lower-rated wins are not enough to compensate for repeated underperformance against several teams above us.

| Opponent | Games | Score | Expected | Net rating points |
|---|---:|---:|---:|---:|
| duck | 268 | .32 | .48 | −363 |
| Decent Chess Bot | 280 | .28 | .36 | −179 |
| Strongly Invisible | 278 | .22 | .28 | −139 |
| Instructors | 264 | .43 | .47 | −84 |
| Mist Opportunities | 284 | .50 | .47 | +82 |

In the recent head-to-head slice against teams above us, 510/510 losses ended by king capture. We made 17.2 king moves per 100 moves vs their 11.5, while creating fewer king threats (3.04 vs 4.64) and unseen king threats (1.29 vs 2.35), and walking into unseen attacks more often (3.29 vs 2.46). That is consistent with a policy that spends turns reacting with the king but applies too little pressure. Aggregate style rates do not prove causality; next replay study should compare our decisions to legal nonfatal alternatives and branch the changed move through a real opponent response.

Sources: `data/reports/daily/2026-10-17.md`, `data/reports/daily/2026-10-24.md`, `data/reports/daily/insights-2026-10-24.md`, and `astra-submissions/analysis/standing-trend-20261024/README.md`.
