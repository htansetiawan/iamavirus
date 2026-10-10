# Against the top six

Updated 2026-10-10 01:58 UTC; leaderboard fetched 2026-10-10T01:57. Active version: v23. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2190 | +587 |
| Knight Vision | 2085 | +482 |
| Decent Chess Bot | 2107 | +504 |
| Strongly Invisible | 2040 | +437 |
| **duck** | 1909 | +306 |
| **Instructors** | 1904 | +301 |
| TA Baseline S | 1663 | +60 |
| **IAmAVirus** | 1603 |  |
| TA Baseline A | 1544 | -59 |
| TA Baseline P | 1458 | -145 |

## Record by version (W-D-L)

| opponent | v24 | v23 | v22 | v21 | v20 | v19 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-1 |  |  | 0-0-2 | 0-0-2 |  |
| Knight Vision | 4-0-0 |  |  | 0-0-16 | 0-0-6 |  |
| Decent Chess Bot | 0-0-2 |  |  | 1-1-26 | 0-0-10 |  |
| Strongly Invisible | 1-0-7 |  |  | 0-1-13 | 0-2-10 |  |
| **duck** | 2-0-2 | 0-1-7 |  | 0-2-6 | 4-1-11 |  |
| **Instructors** | 0-0-4 | 2-0-2 | 1-0-1 | 3-1-10 | 2-0-8 |  |
| TA Baseline P | 1-1-2 | 4-0-0 | 3-1-0 | 29-5-8 | 15-0-3 | 2-0-0 |
| TA Baseline A | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |  |
| TA Baseline S | 0-0-4 | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v23. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.6 | 35.0 | 34.2 | 32.8 | 32.5 |
|  | vision-gaining moves | 18.2 | 21.2 | 23.4 | 16.7 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.35 ⚠ | 0.50 | 0.44 | 0.45 | 0.40 |
|  | captures from unseen squares | 7.6 ⚠ | 11.7 | 11.2 | 10.5 | 8.0 |
|  | captures after a route the other side never saw | 13.8 | 15.6 | 18.9 | 13.7 | 14.6 |
|  | long slider strikes | 4.8 | 4.3 | 4.7 ⚠ | 6.2 | 4.2 |
| King pressure | moves that attack the enemy king | 2.3 ⚠ | 5.5 | 2.8 | 3.6 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.2 ⚠ | 2.9 | 1.9 | 0.9 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.2 | 0.0 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.9 | 3.1 | 1.9 | 1.9 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.3 ⚠ | 1.0 | 1.5 | 4.5 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.1 | 2.1 | 1.7 | 4.1 | 2.9 |
|  | queen left attacked by an unseen piece | 0.6 | 0.2 | 0.0 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 1.7 | 5.7 | 6.0 | 8.8 | 4.8 |
| King handling | king moves | 14.0 | 10.1 | 12.0 | 9.8 | 16.1 |
|  | king moves beyond the second rank | 3.7 | 3.7 | 0.6 | 0.2 | 4.9 |
|  | castling | 1.9 | 2.3 | 2.4 | 2.6 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v23 against the top six

Record 2-1-9; 9 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 7 | 7 |
| king already attacked by an unseen piece | 1 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 1 |

Pieces that took our king: q 5, r 3, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: late (70+) or never 3 down 4, middlegame (30-69) 3, opening (ply < 30) 2.
- Down 3 or more at some point in 8 of 9 losses; median first ply 46.5.
- Down 5 or more in 7; median first ply 39.
- Lost although we had led by 3 or more: 0 of 9.
- Our clock at 15 s or less: 2 of 9.
- Median length 87 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 3 |
| capturer visible when we moved (q) | 1 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |
| capturer unseen when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| other | 1 |

## What worked: v23's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| oyhs29v2 | Instructors | B | win | 75 | King capturable |
| dc1ebyd9 | Instructors | W | win | 124 | King capturable |
| gsbbnv8o | duck | W | draw | 70 | Threefold repetition |
