# Against the top six

Updated 2026-10-11 04:29 UTC; leaderboard fetched 2026-10-11T04:28. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2111 | +367 |
| Knight Vision | 2062 | +317 |
| Decent Chess Bot | 2048 | +304 |
| Strongly Invisible | 2071 | +327 |
| **duck** | 1916 | +171 |
| **Instructors** | 1937 | +192 |
| TA Baseline S | 1674 | -70 |
| **IAmAVirus** | 1744 |  |
| TA Baseline A | 1555 | -189 |
| TA Baseline P | 1429 | -316 |

## Record by version (W-D-L)

| opponent | v30 | v28 | v27 | v26 | v25 | v24 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-1-3 |  |  |  | 0-0-18 | 0-0-2 |
| Knight Vision | 0-0-2 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 | 4-0-0 |
| Decent Chess Bot | 2-0-6 | 0-0-2 |  | 0-0-4 | 0-1-23 | 0-0-2 |
| Strongly Invisible | 1-1-4 | 0-0-2 |  |  | 2-0-34 | 1-0-7 |
| **duck** | 3-2-7 | 1-0-3 |  |  | 9-9-42 | 2-0-2 |
| **Instructors** | 1-0-1 | 1-0-1 |  | 0-0-2 | 12-5-41 | 0-0-4 |
| TA Baseline P | 4-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 | 1-1-2 |
| TA Baseline A | 8-3-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 | 1-0-1 |
| TA Baseline S | 6-1-3 | 4-0-0 |  | 2-0-2 | 30-8-30 | 0-0-4 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.2 | 31.2 | 32.5 | 35.9 | 36.1 | 31.1 | 32.5 |
|  | vision-gaining moves | 22.7 | 20.5 | 20.3 | 23.3 | 23.4 | 19.4 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.41 | 0.47 | 0.45 | 0.40 | 0.52 | 0.37 | 0.40 |
|  | captures from unseen squares | 9.7 | 11.0 | 9.6 | 10.9 | 12.2 | 8.2 | 8.0 |
|  | captures after a route the other side never saw | 15.9 | 14.7 | 15.0 | 18.0 | 17.2 | 14.2 | 14.6 |
|  | long slider strikes | 4.7 ⚠ | 6.3 | 4.8 ⚠ | 6.0 | 3.8 | 4.2 | 4.2 |
| King pressure | moves that attack the enemy king | 5.2 | 3.6 | 2.1 ⚠ | 5.6 | 4.5 | 3.2 | 3.3 |
|  | ...with an attacker the king's side cannot see | 2.1 | 1.3 | 0.5 ⚠ | 2.6 | 2.9 | 0.8 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.1 | 0.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.8 | 1.6 | 1.8 | 3.8 | 6.0 | 2.4 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 1.9 | 2.7 | 2.2 ⚠ | 0.9 | 1.3 | 4.2 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.5 ⚠ | 2.1 | 2.9 | 3.0 | 1.1 | 5.5 | 2.9 |
|  | queen left attacked by an unseen piece | 0.2 | 0.3 | 0.3 | 0.3 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.4 | 5.5 | 4.6 | 4.2 | 2.5 | 4.6 | 4.8 |
| King handling | king moves | 15.1 | 16.8 | 14.8 | 10.4 | 8.3 | 12.4 | 16.1 |
|  | king moves beyond the second rank | 1.4 | 5.0 | 4.4 | 1.0 | 1.6 | 1.0 | 4.9 |
|  | castling | 1.9 | 1.8 | 2.0 | 2.1 | 1.8 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 7-4-23; 23 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 13 | 5 |
| king already attacked by an unseen piece | 7 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 2 | 2 |
| king left to an attacker we could see | 1 | 0 |

Pieces that took our king: r 13, q 7, p 1, n 1, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 12, middlegame (30-69) 8, late (70+) or never 3 down 3.
- Down 3 or more at some point in 20 of 23 losses; median first ply 27.0.
- Down 5 or more in 20; median first ply 40.0.
- Lost although we had led by 3 or more: 1 of 23.
- Our clock at 15 s or less: 0 of 23.
- Median length 74 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 8 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer unseen when we moved, piece had just moved there (q) | 2 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer visible when we moved (b) | 1 |
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
| 9cw08jfq | Decent Chess Bot | W | win | 58 | King capturable |
| ry2oejta | duck | W | win | 116 | King capturable |
| cjb3jsbm | duck | B | win | 117 | King capturable |
| 8v8q5fh7 | Strongly Invisible | W | draw | 102 | Threefold repetition |
| 4geubeqf | duck | B | draw | 100 | Threefold repetition |
