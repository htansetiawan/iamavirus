# Against the top six

Updated 2026-10-11 09:14 UTC; leaderboard fetched 2026-10-11T09:14. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2161 | +397 |
| Knight Vision | 2074 | +310 |
| Decent Chess Bot | 2064 | +300 |
| Strongly Invisible | 2026 | +262 |
| **duck** | 1923 | +159 |
| **Instructors** | 1903 | +138 |
| TA Baseline S | 1663 | -101 |
| **IAmAVirus** | 1764 |  |
| TA Baseline A | 1514 | -251 |
| TA Baseline P | 1453 | -311 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-1-5 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-4 | 3-1-8 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 2-1-9 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 2-1-13 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 5-2-11 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 3-1-4 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 11-0-1 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 15-4-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 9-1-6 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.0 | 32.5 | 32.6 | 35.7 | 36.1 | 31.8 | 32.5 |
|  | vision-gaining moves | 22.6 | 20.6 | 20.1 | 22.7 | 22.7 | 19.1 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.41 | 0.48 | 0.43 | 0.40 | 0.53 | 0.37 | 0.40 |
|  | captures from unseen squares | 9.7 | 11.2 | 9.0 | 10.7 | 12.7 | 8.8 | 8.0 |
|  | captures after a route the other side never saw | 16.1 | 15.3 | 14.7 | 17.7 | 17.7 | 14.8 | 14.6 |
|  | long slider strikes | 4.3 ⚠ | 6.6 | 5.0 | 5.5 | 4.5 | 4.6 | 4.2 |
| King pressure | moves that attack the enemy king | 3.7 | 3.8 | 2.5 ⚠ | 5.0 | 4.7 | 3.1 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.3 | 1.4 | 0.9 ⚠ | 1.9 | 3.0 | 0.9 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.1 | 0.3 | 0.5 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.5 | 1.9 | 2.7 | 3.4 | 7.0 | 2.3 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 1.6 | 2.3 | 2.5 ⚠ | 1.0 | 1.3 | 3.7 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 ⚠ | 2.1 | 3.3 | 3.1 | 1.6 | 5.2 | 2.9 |
|  | queen left attacked by an unseen piece | 0.1 | 0.2 | 0.2 | 0.3 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.4 | 4.8 | 8.2 ⚠ | 3.3 | 3.8 | 5.2 | 4.8 |
| King handling | king moves | 13.6 | 15.3 | 15.0 | 10.1 | 9.7 | 11.8 | 16.1 |
|  | king moves beyond the second rank | 1.7 | 5.0 | 3.3 | 1.6 | 2.0 | 1.5 | 4.9 |
|  | castling | 1.9 | 1.9 | 2.0 | 2.0 | 2.1 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 15-7-50; 50 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 24 | 6 |
| king already attacked by an unseen piece | 11 | 4 |
| king walked into an unseen attacker after taking the bait (king capture) | 8 | 4 |
| king left to an attacker we could see (no safe move existed) | 3 | 1 |
| king left to an attacker we could see | 2 | 0 |
| king already attacked by an unseen piece (no safe move existed) | 2 | 0 |

Pieces that took our king: q 20, r 16, b 6, n 4, p 2, k 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 21, opening (ply < 30) 17, late (70+) or never 3 down 12.
- Down 3 or more at some point in 42 of 50 losses; median first ply 35.0.
- Down 5 or more in 39; median first ply 45.
- Lost although we had led by 3 or more: 3 of 50.
- Our clock at 15 s or less: 0 of 50.
- Median length 71.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 13 |
| capturer unseen when we moved, piece had just moved there (r) | 7 |
| capturer unseen when we moved, piece had just moved there (q) | 6 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved (p) | 1 |
| capturer visible when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer unseen when we moved (b) | 1 |
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
| 1q0b4ac9 | Instructors | B | draw | 61 | Threefold repetition |
| oguoh5me | Knight Vision | W | win | 60 | King capturable |
| bnys3dom | duck | B | win | 63 | King capturable |
| hj4jbrrc | duck | W | win | 102 | King capturable |
| zx2qah3c | Strongly Invisible | W | win | 106 | King capturable |
| fxqi02p2 | Instructors | B | win | 87 | King capturable |
| io7zwfom | Instructors | W | win | 128 | King capturable |
| rezmiay9 | Knight Vision | B | win | 49 | King capturable |
| zf3v2fi1 | Decent Chess Bot | W | draw | 58 | Threefold repetition |
