# Against the top six

Updated 2026-10-13 06:29 UTC; leaderboard fetched 2026-10-13T06:28. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2238 | +357 |
| Knight Vision | 2095 | +214 |
| Decent Chess Bot | 2046 | +165 |
| Strongly Invisible | 2096 | +214 |
| **duck** | 1964 | +83 |
| **Instructors** | 1952 | +70 |
| TA Baseline S | 1684 | -197 |
| **IAmAVirus** | 1881 |  |
| TA Baseline A | 1566 | -316 |
| TA Baseline P | 1463 | -418 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-14 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-7 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 3-0-11 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 1-0-9 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 5-0-9 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 10-0-12 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 5-1-0 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 10-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 22-0-2 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.7 | 34.1 | 32.2 | 36.3 | 34.3 | 30.6 | 32.3 |
|  | vision-gaining moves | 23.4 | 19.8 | 21.1 | 22.2 | 20.6 | 17.7 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.39 | 0.46 | 0.40 | 0.49 | 0.36 | 0.39 |
|  | captures from unseen squares | 10.8 | 9.5 | 9.0 | 10.6 | 11.2 | 7.6 | 7.7 |
|  | captures after a route the other side never saw | 17.4 | 16.6 | 14.4 ⚠ | 19.2 | 17.2 | 13.1 | 14.2 |
|  | long slider strikes | 5.0 | 4.9 | 4.4 ⚠ | 6.3 | 4.8 | 4.2 | 4.1 |
| King pressure | moves that attack the enemy king | 3.9 | 4.2 | 2.6 ⚠ | 5.6 | 5.0 | 2.6 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.8 | 2.3 | 0.3 ⚠ | 3.4 | 3.2 | 0.6 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.1 | 0.1 | 0.6 | 0.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 5.5 | 5.0 | 3.1 | 4.6 | 4.8 | 1.7 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.8 ⚠ | 1.6 | 4.9 ⚠ | 1.5 | 1.4 | 3.2 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.8 | 2.6 | 3.4 ⚠ | 1.7 | 1.6 | 3.4 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.3 | 0.2 | 0.1 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 6.4 ⚠ | 4.9 | 8.0 ⚠ | 2.9 | 4.7 | 6.8 | 4.7 |
| King handling | king moves | 14.8 | 12.7 | 17.1 | 9.4 | 10.4 | 17.3 | 16.1 |
|  | king moves beyond the second rank | 4.5 | 2.9 | 6.4 | 1.2 | 2.6 | 3.7 | 5.2 |
|  | castling | 2.3 | 2.4 | 2.2 | 2.5 | 1.5 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 20-0-62; 62 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 23 | 10 |
| king already attacked by an unseen piece | 13 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 10 | 4 |
| king left to an attacker we could see (no safe move existed) | 7 | 2 |
| king walked into an unseen attacker after taking the bait (king capture) | 6 | 1 |
| our move opened a line from an unseen attacker | 3 | 1 |

Pieces that took our king: q 39, r 14, n 3, k 2, b 2, p 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 39, late (70+) or never 3 down 13, opening (ply < 30) 10.
- Down 3 or more at some point in 57 of 62 losses; median first ply 42.
- Down 5 or more in 54; median first ply 47.0.
- Lost although we had led by 3 or more: 6 of 62.
- Our clock at 15 s or less: 0 of 62.
- Median length 74.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 25 |
| capturer unseen when we moved, piece had just moved there (r) | 10 |
| capturer unseen when we moved, piece had just moved there (b) | 6 |
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
| wz467mbn | Instructors | W | win | 96 | King capturable |
| dgdbtyya | Decent Chess Bot | W | win | 96 | King capturable |
| tbbl82pn | Decent Chess Bot | W | win | 50 | King capturable |
