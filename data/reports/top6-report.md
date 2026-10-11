# Against the top six

Updated 2026-10-11 06:49 UTC; leaderboard fetched 2026-10-11T06:48. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2134 | +392 |
| Knight Vision | 2044 | +301 |
| Decent Chess Bot | 2038 | +295 |
| Strongly Invisible | 2088 | +345 |
| **duck** | 1919 | +176 |
| **Instructors** | 1942 | +199 |
| TA Baseline S | 1669 | -74 |
| **IAmAVirus** | 1742 |  |
| TA Baseline A | 1524 | -219 |
| TA Baseline P | 1443 | -299 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-1-3 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-4 | 1-1-6 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 2-0-6 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 1-1-10 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 3-2-10 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 1-0-3 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 8-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 14-3-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 9-1-4 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.1 | 32.5 | 32.4 | 35.8 | 36.4 | 31.6 | 32.5 |
|  | vision-gaining moves | 22.7 | 19.7 | 20.3 | 23.1 | 22.8 | 18.8 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 | 0.47 | 0.41 | 0.41 | 0.53 | 0.36 | 0.40 |
|  | captures from unseen squares | 9.5 | 11.4 | 8.5 ⚠ | 10.8 | 12.8 | 8.2 | 8.0 |
|  | captures after a route the other side never saw | 16.4 | 15.2 | 14.5 | 18.0 | 17.7 | 14.5 | 14.6 |
|  | long slider strikes | 4.9 ⚠ | 6.4 | 4.9 | 5.9 | 4.3 | 4.1 | 4.2 |
| King pressure | moves that attack the enemy king | 4.7 | 3.8 | 2.3 ⚠ | 5.3 | 5.0 | 2.9 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.7 | 1.7 | 0.6 ⚠ | 2.1 | 3.2 | 0.8 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.1 | 0.3 | 0.5 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.6 | 2.0 | 1.8 | 3.7 | 6.9 | 2.2 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.0 | 2.6 | 2.4 ⚠ | 1.0 | 1.1 | 3.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.6 ⚠ | 2.1 | 3.5 ⚠ | 2.3 | 1.6 | 5.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.1 | 0.3 | 0.2 | 0.2 | 0.1 | 0.3 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.4 | 5.1 | 7.5 ⚠ | 2.9 | 3.5 | 4.7 | 4.8 |
| King handling | king moves | 14.4 | 15.0 | 15.3 | 11.2 | 8.5 | 11.9 | 16.1 |
|  | king moves beyond the second rank | 1.2 | 4.2 | 4.0 | 2.1 | 1.6 | 1.5 | 4.9 |
|  | castling | 1.9 | 1.9 | 2.0 | 2.2 | 2.0 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 8-5-38; 38 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 19 | 6 |
| king already attacked by an unseen piece | 10 | 4 |
| king walked into an unseen attacker after taking the bait (king capture) | 6 | 3 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |
| king left to an attacker we could see | 1 | 0 |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |

Pieces that took our king: r 14, q 14, b 4, p 2, n 2, k 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 16, opening (ply < 30) 15, late (70+) or never 3 down 7.
- Down 3 or more at some point in 32 of 38 losses; median first ply 33.0.
- Down 5 or more in 29; median first ply 41.
- Lost although we had led by 3 or more: 2 of 38.
- Our clock at 15 s or less: 0 of 38.
- Median length 71.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 10 |
| capturer unseen when we moved, piece had just moved there (q) | 5 |
| capturer unseen when we moved, piece had just moved there (r) | 4 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer visible when we moved (p) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer unseen when we moved (p) | 1 |

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
| gr6iofmo | Knight Vision | W | win | 114 | King capturable |
| ee7u7ywy | Knight Vision | B | draw | 99 | Threefold repetition |
