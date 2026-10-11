# Against the top six

Updated 2026-10-11 03:07 UTC; leaderboard fetched 2026-10-11T03:07. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2118 | +395 |
| Knight Vision | 2055 | +332 |
| Decent Chess Bot | 2027 | +304 |
| Strongly Invisible | 2075 | +351 |
| **duck** | 1926 | +203 |
| **Instructors** | 1935 | +212 |
| TA Baseline S | 1691 | -32 |
| **IAmAVirus** | 1724 |  |
| TA Baseline A | 1574 | -149 |
| TA Baseline P | 1415 | -309 |

## Record by version (W-D-L)

| opponent | v30 | v28 | v27 | v26 | v25 | v24 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-1-3 |  |  |  | 0-0-18 | 0-0-2 |
| Knight Vision | 0-0-2 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 | 4-0-0 |
| Decent Chess Bot | 1-0-5 | 0-0-2 |  | 0-0-4 | 0-1-23 | 0-0-2 |
| Strongly Invisible | 1-0-1 | 0-0-2 |  |  | 2-0-34 | 1-0-7 |
| **duck** | 1-1-4 | 1-0-3 |  |  | 9-9-42 | 2-0-2 |
| **Instructors** | 1-0-1 | 1-0-1 |  | 0-0-2 | 12-5-41 | 0-0-4 |
| TA Baseline P | 2-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 | 1-1-2 |
| TA Baseline A | 7-2-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 | 1-0-1 |
| TA Baseline S |  | 4-0-0 |  | 2-0-2 | 30-8-30 | 0-0-4 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 34.5 | 30.3 | 33.4 | 35.6 | 36.1 | 31.1 | 32.5 |
|  | vision-gaining moves | 25.0 | 23.0 | 21.0 | 23.6 | 22.7 | 19.3 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.38 | 0.47 | 0.45 | 0.38 | 0.54 | 0.32 | 0.40 |
|  | captures from unseen squares | 9.6 | 11.5 | 9.9 | 10.4 | 13.2 | 7.8 | 8.0 |
|  | captures after a route the other side never saw | 16.6 | 13.9 | 15.1 | 18.0 | 17.7 | 15.1 | 14.6 |
|  | long slider strikes | 6.0 | 6.0 | 5.0 | 5.2 | 4.2 | 3.7 | 4.2 |
| King pressure | moves that attack the enemy king | 5.1 | 3.0 | 1.6 ⚠ | 6.6 | 3.2 | 2.3 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.5 | 1.5 | 0.4 ⚠ | 3.0 | 1.1 | 0.8 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.6 | 0.0 | 0.0 | 1.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.4 | 0.9 | 2.6 | 3.4 | 4.5 | 0.8 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.1 | 3.0 | 2.2 | 1.2 | 2.4 | 3.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.3 | 2.4 | 3.4 | 3.0 | 1.3 | 4.7 | 2.9 |
|  | queen left attacked by an unseen piece | 0.0 | 0.6 | 0.4 | 0.0 | 0.0 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 1.8 | 2.7 | 6.0 | 6.2 | 1.8 | 1.8 | 4.8 |
| King handling | king moves | 13.9 | 18.7 | 11.9 | 10.2 | 10.3 | 16.2 | 16.1 |
|  | king moves beyond the second rank | 1.2 | 5.4 | 2.6 | 0.6 | 3.4 | 1.3 | 4.9 |
|  | castling | 2.1 | 1.8 | 1.8 | 2.2 | 2.4 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 4-2-16; 16 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 8 | 3 |
| king already attacked by an unseen piece | 6 | 1 |
| king left to an attacker we could see | 1 | 0 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 1 |

Pieces that took our king: r 9, q 4, p 1, n 1, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 8, middlegame (30-69) 5, late (70+) or never 3 down 3.
- Down 3 or more at some point in 13 of 16 losses; median first ply 26.
- Down 5 or more in 13; median first ply 41.
- Lost although we had led by 3 or more: 1 of 16.
- Our clock at 15 s or less: 0 of 16.
- Median length 70.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 5 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer unseen when we moved (n) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
| capturer unseen when we moved, piece had just moved there (q) | 1 |
| capturer unseen when we moved, piece had just moved there (r) | 1 |

## What worked: v30's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| wq5d0hzo | Instructors | B | win | 101 | King capturable |
| denxaibc | Strongly Invisible | W | win | 42 | King capturable |
| 5h4xih5q | Decent Chess Bot | B | win | 85 | King capturable |
| ykpadh8e | duck | B | draw | 109 | Threefold repetition |
| mzjmy3l6 | Greek Gift | W | draw | 125 | Threefold repetition |
| 7seq6wow | duck | W | win | 114 | King capturable |
