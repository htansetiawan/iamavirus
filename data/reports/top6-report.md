# Against the top six

Updated 2026-10-11 05:04 UTC; leaderboard fetched 2026-10-11T05:04. Active version: v32. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2112 | +362 |
| Knight Vision | 2061 | +312 |
| Decent Chess Bot | 2049 | +299 |
| Strongly Invisible | 2078 | +328 |
| **duck** | 1900 | +150 |
| **Instructors** | 1947 | +198 |
| TA Baseline S | 1663 | -87 |
| **IAmAVirus** | 1749 |  |
| TA Baseline A | 1555 | -194 |
| TA Baseline P | 1435 | -314 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-1-3 |  |  |  | 0-0-18 |
| Knight Vision |  | 0-0-2 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 2-0-6 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 1-1-4 | 0-0-2 |  |  | 2-0-34 |
| **duck** |  | 3-2-7 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 1-0-2 | 1-0-3 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 4-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 8-3-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S |  | 6-1-3 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v32. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.6 | 33.5 | 26.6 ⚠ | 36.6 | 37.0 | 33.9 | 32.5 |
|  | vision-gaining moves | 15.9 ⚠ | 21.5 | 17.5 | 20.3 | 21.6 | 15.3 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.29 ⚠ | 0.57 | 0.33 ⚠ | 0.45 | 0.44 | 0.28 | 0.40 |
|  | captures from unseen squares | 6.5 ⚠ | 15.0 | 6.2 ⚠ | 11.4 | 10.8 | 6.0 | 8.0 |
|  | captures after a route the other side never saw | 15.0 ⚠ | 22.4 | 15.0 ⚠ | 20.3 | 15.5 | 14.0 | 14.6 |
|  | long slider strikes | 2.8 | 3.7 | 6.2 | 3.8 | 5.4 | 4.0 | 4.2 |
| King pressure | moves that attack the enemy king | 2.8 ⚠ | 5.6 | 8.8 | 3.8 | 3.4 | 2.0 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.9 | 0.9 | 3.8 | 1.3 | 2.7 | 0.0 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 ⚠ | 2.5 | 0.0 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.9 | 4.7 | 1.2 | 1.3 | 4.7 | 1.3 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 6.5 ⚠ | 1.9 | 5.0 ⚠ | 2.5 | 1.4 | 2.7 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 4.7 ⚠ | 1.9 | 5.0 ⚠ | 1.3 | 1.4 | 4.0 | 2.9 |
|  | queen left attacked by an unseen piece | 0.9 | 0.9 | 0.0 | 1.3 | 0.0 | 1.3 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 0.9 | 0.0 | 1.2 ⚠ | 0.0 | 1.4 | 11.3 | 4.8 |
| King handling | king moves | 13.1 | 15.0 | 38.8 | 16.5 | 4.1 | 6.7 | 16.1 |
|  | king moves beyond the second rank | 8.4 | 2.8 | 11.2 | 8.9 | 0.0 | 0.0 | 4.9 |
|  | castling | 1.9 | 1.9 | 2.5 | 2.5 | 2.7 | 2.7 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v32 against the top six

Record 1-0-4; 4 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |
| king left to an attacker we could see (no safe move existed) | 1 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 0 |
| king already attacked by an unseen piece | 1 | 1 |

Pieces that took our king: b 2, r 1, q 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 2, opening (ply < 30) 1, late (70+) or never 3 down 1.
- Down 3 or more at some point in 3 of 4 losses; median first ply 30.
- Down 5 or more in 2; median first ply 24.5.
- Lost although we had led by 3 or more: 1 of 4.
- Our clock at 15 s or less: 0 of 4.
- Median length 53.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 1 |
| capturer unseen when we moved, piece had just moved there (q) | 1 |
| capturer unseen when we moved (n) | 1 |

## What worked: v32's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| rotnqcus | Instructors | W | win | 108 | King capturable |
