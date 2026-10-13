# Against the top six

Updated 2026-10-13 04:25 UTC; leaderboard fetched 2026-10-13T04:24. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2234 | +358 |
| Knight Vision | 2130 | +253 |
| Decent Chess Bot | 2020 | +144 |
| Strongly Invisible | 2063 | +187 |
| **duck** | 1959 | +83 |
| **Instructors** | 1945 | +69 |
| TA Baseline S | 1708 | -169 |
| **IAmAVirus** | 1876 |  |
| TA Baseline A | 1582 | -294 |
| TA Baseline P | 1455 | -421 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-8 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-5 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 1-0-5 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 0-0-4 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 5-0-9 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 6-0-6 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 5-1-0 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 4-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 11-0-1 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 34.2 | 34.8 | 31.5 | 36.2 | 33.4 | 29.8 | 32.3 |
|  | vision-gaining moves | 23.3 | 20.2 | 20.0 | 21.4 | 21.1 | 17.2 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.38 | 0.46 | 0.37 | 0.48 | 0.34 | 0.39 |
|  | captures from unseen squares | 11.0 | 9.7 | 8.5 | 9.5 | 10.2 | 7.0 | 7.7 |
|  | captures after a route the other side never saw | 18.9 | 17.5 | 14.2 | 17.5 | 16.4 | 12.1 | 14.2 |
|  | long slider strikes | 5.2 | 5.7 | 3.7 ⚠ | 5.5 | 4.6 | 4.4 | 4.1 |
| King pressure | moves that attack the enemy king | 4.8 | 5.2 | 2.3 ⚠ | 6.6 | 3.7 | 2.4 | 3.2 |
|  | ...with an attacker the king's side cannot see | 2.0 | 2.7 | 0.2 ⚠ | 3.9 | 2.6 | 0.5 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.1 | 0.0 | 0.3 | 0.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 6.3 | 5.8 | 2.8 | 5.4 | 5.1 | 1.5 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.8 ⚠ | 1.4 | 4.9 ⚠ | 1.4 | 1.6 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.8 | 2.6 | 2.5 ⚠ | 1.3 | 0.9 | 3.3 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.0 | 0.3 | 0.1 | 0.1 | 0.6 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 8.3 ⚠ | 4.7 | 8.8 ⚠ | 4.1 | 3.7 | 7.5 | 4.7 |
| King handling | king moves | 11.3 | 11.3 | 21.0 | 8.7 | 11.6 | 18.5 | 16.1 |
|  | king moves beyond the second rank | 2.9 | 2.2 | 9.3 | 1.2 | 3.5 | 4.4 | 5.2 |
|  | castling | 2.4 | 2.5 | 2.2 | 2.6 | 1.3 | 1.8 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 13-0-37; 37 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 15 | 7 |
| king already attacked by an unseen piece | 6 | 2 |
| king left to an attacker we could see (no safe move existed) | 6 | 2 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 2 |
| king walked into an unseen attacker after taking the bait (king capture) | 3 | 1 |
| our move opened a line from an unseen attacker | 2 | 1 |

Pieces that took our king: q 24, r 9, b 2, nq 1, n 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 21, opening (ply < 30) 9, late (70+) or never 3 down 7.
- Down 3 or more at some point in 34 of 37 losses; median first ply 37.5.
- Down 5 or more in 31; median first ply 41.
- Lost although we had led by 3 or more: 3 of 37.
- Our clock at 15 s or less: 0 of 37.
- Median length 70 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 15 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved, piece had just moved there (b) | 4 |
| capturer unseen when we moved (q) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer visible when we moved (q) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer unseen when we moved (b) | 1 |
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
