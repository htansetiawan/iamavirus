# Against the top six

Updated 2026-10-13 05:27 UTC; leaderboard fetched 2026-10-13T05:26. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2249 | +372 |
| Knight Vision | 2105 | +229 |
| Decent Chess Bot | 2038 | +161 |
| Strongly Invisible | 2075 | +198 |
| **duck** | 1941 | +64 |
| **Instructors** | 1967 | +91 |
| TA Baseline S | 1683 | -194 |
| **IAmAVirus** | 1877 |  |
| TA Baseline A | 1573 | -303 |
| TA Baseline P | 1474 | -402 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-12 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-7 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 1-0-5 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 1-0-9 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 5-0-9 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 9-0-12 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 5-1-0 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 10-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 19-0-1 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.6 | 34.2 | 31.6 | 36.2 | 34.8 | 30.8 | 32.3 |
|  | vision-gaining moves | 23.6 | 20.0 | 20.6 | 22.5 | 21.0 | 17.1 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.39 | 0.45 | 0.38 | 0.49 | 0.33 | 0.39 |
|  | captures from unseen squares | 10.7 | 9.6 | 8.7 | 10.4 | 11.4 | 7.0 | 7.7 |
|  | captures after a route the other side never saw | 17.5 | 16.7 | 14.6 ⚠ | 19.1 | 17.3 | 12.6 | 14.2 |
|  | long slider strikes | 5.0 | 4.9 | 4.3 ⚠ | 6.2 | 5.0 | 4.2 | 4.1 |
| King pressure | moves that attack the enemy king | 4.1 | 4.4 | 2.2 ⚠ | 6.3 | 5.2 | 2.3 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.8 | 2.4 | 0.1 ⚠ | 3.9 | 3.3 | 0.5 | 1.4 |
|  | sacrifices that lead to a king capture | 0.2 | 0.2 | 0.0 | 0.4 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 5.5 | 5.2 | 2.7 | 5.0 | 5.2 | 1.4 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.9 ⚠ | 1.5 | 5.2 ⚠ | 1.4 | 1.4 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 2.3 | 3.2 ⚠ | 1.4 | 1.4 | 3.5 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.4 | 0.2 | 0.1 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 6.7 ⚠ | 5.1 | 8.6 ⚠ | 3.5 | 3.3 | 6.9 | 4.7 |
| King handling | king moves | 14.8 | 12.4 | 19.6 | 8.2 | 9.5 | 16.3 | 16.1 |
|  | king moves beyond the second rank | 4.2 | 2.7 | 7.9 | 1.2 | 2.3 | 3.7 | 5.2 |
|  | castling | 2.3 | 2.4 | 2.2 | 2.6 | 1.5 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 17-0-54; 54 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 22 | 10 |
| king already attacked by an unseen piece | 11 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 10 | 4 |
| king left to an attacker we could see (no safe move existed) | 6 | 2 |
| king walked into an unseen attacker after taking the bait (king capture) | 3 | 1 |
| our move opened a line from an unseen attacker | 2 | 1 |

Pieces that took our king: q 35, r 12, n 2, k 2, b 2, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 33, late (70+) or never 3 down 11, opening (ply < 30) 10.
- Down 3 or more at some point in 49 of 54 losses; median first ply 41.
- Down 5 or more in 46; median first ply 47.0.
- Lost although we had led by 3 or more: 4 of 54.
- Our clock at 15 s or less: 0 of 54.
- Median length 73.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 19 |
| capturer unseen when we moved, piece had just moved there (r) | 9 |
| capturer unseen when we moved, piece had just moved there (b) | 5 |
| capturer unseen when we moved, piece had just moved there (n) | 4 |
| capturer unseen when we moved (p) | 2 |
| capturer unseen when we moved (q) | 2 |
| capturer visible when we moved (b) | 2 |
| capturer unseen when we moved (b) | 2 |
| capturer visible when we moved (q) | 1 |
| capturer unseen when we moved (n) | 1 |
| other | 1 |
| capturer visible when we moved (p) | 1 |

## What worked: v34's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| gzj7ox1o | Instructors | W | win | 66 | King capturable |
| y4qk2v2b | Instructors | B | win | 9 | King capturable |
| np6c6tub | Instructors | B | win | 61 | King capturable |
| 05l0ejxw | Instructors | W | win | 66 | King capturable |
| 19pwd8n9 | Knight Vision | W | win | 50 | King capturable |
| sdr3y95n | Decent Chess Bot | W | win | 138 | King capturable |
| znv5996o | duck | W | win | 44 | King capturable |
| u5hyxqe5 | duck | B | win | 61 | King capturable |
| sjyd7bcw | duck | W | win | 86 | King capturable |
| wnso8ft4 | duck | B | win | 107 | King capturable |
| n3e191mm | Instructors | B | win | 45 | King capturable |
| p5k8pu4u | Instructors | W | win | 68 | King capturable |
| n9entvtq | duck | B | win | 101 | King capturable |
| frmdez59 | Instructors | W | win | 66 | King capturable |
| bd2qdd48 | Instructors | B | win | 87 | King capturable |
| qo7iigz9 | Strongly Invisible | B | win | 9 | King capturable |
| fkt72pd8 | Instructors | W | win | 102 | King capturable |
