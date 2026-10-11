# Against the top six

Updated 2026-10-11 06:28 UTC; leaderboard fetched 2026-10-11T06:28. Active version: v30. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2133 | +382 |
| Knight Vision | 2039 | +288 |
| Decent Chess Bot | 2035 | +283 |
| Strongly Invisible | 2061 | +310 |
| **duck** | 1915 | +164 |
| **Instructors** | 1959 | +208 |
| TA Baseline S | 1672 | -80 |
| **IAmAVirus** | 1752 |  |
| TA Baseline A | 1535 | -216 |
| TA Baseline P | 1437 | -314 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-1-3 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-4 | 1-1-2 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 2-0-6 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 1-1-6 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 3-2-9 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 1-0-3 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 8-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 11-3-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 9-1-4 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v30. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.1 | 32.4 | 32.4 | 35.3 | 36.4 | 31.6 | 32.5 |
|  | vision-gaining moves | 22.5 | 19.5 | 20.1 | 22.8 | 23.3 | 19.4 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 | 0.47 | 0.45 | 0.39 | 0.52 | 0.36 | 0.40 |
|  | captures from unseen squares | 9.5 | 11.3 | 9.3 | 10.3 | 12.7 | 8.2 | 8.0 |
|  | captures after a route the other side never saw | 16.4 | 15.2 | 14.6 | 17.6 | 17.8 | 14.5 | 14.6 |
|  | long slider strikes | 5.0 ⚠ | 6.3 | 4.6 | 5.6 | 4.2 | 3.9 | 4.2 |
| King pressure | moves that attack the enemy king | 4.7 | 3.6 | 2.2 ⚠ | 4.9 | 5.1 | 2.9 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.7 | 1.6 | 0.8 ⚠ | 2.1 | 3.2 | 0.7 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.1 | 0.1 | 0.5 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.6 | 2.0 | 1.8 | 3.2 | 6.3 | 2.4 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.0 | 2.6 | 2.1 ⚠ | 1.1 | 1.2 | 3.9 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.6 ⚠ | 2.2 | 2.7 | 2.7 | 1.5 | 5.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.1 | 0.3 | 0.2 | 0.2 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.4 | 5.1 | 5.7 ⚠ | 3.4 | 3.5 | 4.8 | 4.8 |
| King handling | king moves | 14.5 | 15.1 | 15.6 | 12.1 | 8.3 | 11.9 | 16.1 |
|  | king moves beyond the second rank | 1.2 | 4.2 | 4.6 | 1.9 | 1.8 | 1.4 | 4.9 |
|  | castling | 1.9 | 1.9 | 2.0 | 2.0 | 1.9 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v30 against the top six

Record 8-5-29; 29 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 16 | 6 |
| king already attacked by an unseen piece | 9 | 3 |
| king walked into an unseen attacker after taking the bait (king capture) | 3 | 3 |
| king left to an attacker we could see | 1 | 0 |

Pieces that took our king: r 14, q 9, b 3, p 1, n 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 13, middlegame (30-69) 12, late (70+) or never 3 down 4.
- Down 3 or more at some point in 25 of 29 losses; median first ply 29.
- Down 5 or more in 24; median first ply 43.0.
- Lost although we had led by 3 or more: 2 of 29.
- Our clock at 15 s or less: 0 of 29.
- Median length 74 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (n) | 9 |
| capturer unseen when we moved, piece had just moved there (q) | 3 |
| capturer unseen when we moved (r) | 3 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer unseen when we moved, piece had just moved there (r) | 2 |
| capturer visible when we moved (p) | 1 |
| capturer visible when we moved (b) | 1 |

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
