# Against the top six

Updated 2026-10-10 00:56 UTC; leaderboard fetched 2026-10-10T00:56. Active version: v24. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2197 | +581 |
| Knight Vision | 2123 | +506 |
| Decent Chess Bot | 2102 | +485 |
| Strongly Invisible | 2055 | +439 |
| **duck** | 1919 | +302 |
| **Instructors** | 1900 | +283 |
| TA Baseline S | 1652 | +35 |
| **IAmAVirus** | 1617 |  |
| TA Baseline A | 1517 | -100 |
| TA Baseline P | 1451 | -166 |

## Record by version (W-D-L)

| opponent | v24 | v23 | v22 | v21 | v20 | v19 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  |  |  | 0-0-2 | 0-0-2 |  |
| Knight Vision | 2-0-0 |  |  | 0-0-16 | 0-0-6 |  |
| Decent Chess Bot | 0-0-2 |  |  | 1-1-26 | 0-0-10 |  |
| Strongly Invisible |  |  |  | 0-1-13 | 0-2-10 |  |
| **duck** | 1-0-1 | 0-1-7 |  | 0-2-6 | 4-1-11 |  |
| **Instructors** |  | 2-0-2 | 1-0-1 | 3-1-10 | 2-0-8 |  |
| TA Baseline P | 1-0-1 | 2-0-0 | 3-1-0 | 29-5-8 | 15-0-3 | 2-0-0 |
| TA Baseline A | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |  |
| TA Baseline S |  | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v24. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.9 | 33.6 | 33.1 | 38.0 | 37.4 | 35.6 | 32.5 |
|  | vision-gaining moves | 19.7 | 19.7 | 23.8 | 27.7 | 21.4 | 16.0 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.26 ⚠ | 0.38 | 0.39 | 0.42 | 0.33 | 0.37 | 0.40 |
|  | captures from unseen squares | 4.7 ⚠ | 7.1 | 8.9 | 10.9 | 8.4 | 7.6 | 8.0 |
|  | captures after a route the other side never saw | 12.6 | 11.8 | 18.8 | 19.8 | 16.8 | 13.0 | 14.6 |
|  | long slider strikes | 3.1 | 2.4 | 10.9 | 8.9 | 1.5 ⚠ | 6.1 | 4.2 |
| King pressure | moves that attack the enemy king | 2.4 | 2.4 | 7.9 | 8.9 | 0.0 ⚠ | 2.3 | 3.3 |
|  | ...with an attacker the king's side cannot see | 2.4 | 0.8 | 2.0 ⚠ | 5.9 | 0.0 | 0.0 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 ⚠ | 1.5 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.9 | 3.9 | 1.0 | 5.9 | 0.0 | 2.3 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 0.8 | 2.4 | 5.0 ⚠ | 1.0 | 0.0 | 3.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 1.6 | 1.6 | 11.9 ⚠ | 0.0 | 2.3 | 3.8 | 2.9 |
|  | queen left attacked by an unseen piece | 0.0 | 0.8 | 0.0 | 1.0 | 0.0 | 0.0 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 0.8 | 0.0 | 3.0 ⚠ | 0.0 | 0.0 | 11.5 | 4.8 |
| King handling | king moves | 11.8 | 13.4 | 13.9 | 14.9 | 7.6 | 5.3 | 16.1 |
|  | king moves beyond the second rank | 0.0 | 7.9 | 3.0 | 4.0 | 0.0 | 0.0 | 4.9 |
|  | castling | 1.6 | 1.6 | 2.0 | 2.0 | 3.1 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v24 against the top six

Record 3-0-3; 3 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 2 | 1 |
| king already attacked by an unseen piece | 1 | 0 |

Pieces that took our king: q 3

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 2, opening (ply < 30) 1.
- Down 3 or more at some point in 3 of 3 losses; median first ply 53.
- Down 5 or more in 3; median first ply 61.
- Lost although we had led by 3 or more: 0 of 3.
- Our clock at 15 s or less: 1 of 3.
- Median length 116 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved (b) | 1 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |

## What worked: v24's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| 12j9j4qe | Knight Vision | B | win | 11 | King capturable |
| da7pinqq | Knight Vision | W | win | 22 | King capturable |
| ydptf4jh | duck | W | win | 134 | King capturable |
