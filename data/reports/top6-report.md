# Against the top six

Updated 2026-10-11 02:25 UTC; leaderboard fetched 2026-10-11T02:24. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2107 | +389 |
| Knight Vision | 2063 | +345 |
| Decent Chess Bot | 2030 | +312 |
| Strongly Invisible | 2066 | +348 |
| **duck** | 1941 | +223 |
| **Instructors** | 1927 | +209 |
| TA Baseline S | 1671 | -46 |
| **IAmAVirus** | 1718 |  |
| TA Baseline A | 1576 | -142 |
| TA Baseline P | 1424 | -294 |

## Record by version (W-D-L)

| opponent | v30 | v28 | v27 | v26 | v25 | v24 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 |  |  |  | 0-0-18 | 0-0-2 |
| Knight Vision | 0-0-2 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 | 4-0-0 |
| Decent Chess Bot | 1-0-3 | 0-0-2 |  | 0-0-4 | 0-1-23 | 0-0-2 |
| Strongly Invisible | 1-0-1 | 0-0-2 |  |  | 2-0-34 | 1-0-7 |
| **duck** | 0-0-2 | 1-0-3 |  |  | 9-9-42 | 2-0-2 |
| **Instructors** | 1-0-1 | 1-0-1 |  | 0-0-2 | 12-5-41 | 0-0-4 |
| TA Baseline P | 2-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 | 1-1-2 |
| TA Baseline A | 6-1-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 | 1-0-1 |
| TA Baseline S |  | 4-0-0 |  | 2-0-2 | 30-8-30 | 0-0-4 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 35.0 | 32.0 | 33.8 | 36.2 | 38.0 | 32.5 | 32.5 |
|  | vision-gaining moves | 25.9 | 21.8 | 20.1 | 24.6 | 24.1 | 17.8 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.26 ⚠ | 0.44 | 0.51 | 0.34 | 0.55 | 0.30 | 0.40 |
|  | captures from unseen squares | 6.6 ⚠ | 10.9 | 10.9 | 9.6 | 14.3 | 7.7 | 8.0 |
|  | captures after a route the other side never saw | 15.7 | 15.8 | 14.7 ⚠ | 20.0 | 18.7 | 15.8 | 14.6 |
|  | long slider strikes | 4.2 ⚠ | 7.3 | 5.5 | 4.9 | 4.1 | 3.7 | 4.2 |
| King pressure | moves that attack the enemy king | 3.6 | 2.4 | 1.4 ⚠ | 7.5 | 3.1 | 2.0 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.6 ⚠ | 1.8 | 0.6 ⚠ | 2.9 | 1.4 | 0.7 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.6 | 0.0 | 0.0 | 1.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.8 | 0.6 | 2.3 | 4.6 | 5.1 | 1.0 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 1.8 | 3.6 | 1.4 | 0.6 | 2.4 | 4.0 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 4.2 ⚠ | 3.0 | 3.4 | 2.6 | 1.0 | 6.1 | 2.9 |
|  | queen left attacked by an unseen piece | 0.0 | 0.6 | 0.3 | 0.0 | 0.0 | 0.7 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.4 | 1.8 | 7.2 ⚠ | 5.5 | 2.4 | 2.4 | 4.8 |
| King handling | king moves | 15.7 | 15.2 | 14.1 | 7.8 | 8.8 | 9.4 | 16.1 |
|  | king moves beyond the second rank | 1.2 | 7.9 | 3.2 | 0.9 | 1.4 | 1.7 | 4.9 |
|  | castling | 1.8 | 2.4 | 2.0 | 2.3 | 2.4 | 2.4 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 3-0-11; 11 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 6 | 2 |
| king already attacked by an unseen piece | 4 | 1 |
| king left to an attacker we could see | 1 | 0 |

Pieces that took our king: r 6, q 4, p 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 4, opening (ply < 30) 4, late (70+) or never 3 down 3.
- Down 3 or more at some point in 8 of 11 losses; median first ply 29.5.
- Down 5 or more in 8; median first ply 53.0.
- Lost although we had led by 3 or more: 1 of 11.
- Our clock at 15 s or less: 0 of 11.
- Median length 71 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
| capturer unseen when we moved, piece had just moved there (r) | 1 |

## What worked: v30's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| wq5d0hzo | Instructors | B | win | 101 | King capturable |
| denxaibc | Strongly Invisible | W | win | 42 | King capturable |
| 5h4xih5q | Decent Chess Bot | B | win | 85 | King capturable |
