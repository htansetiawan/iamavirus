# Against the top six

Updated 2026-10-13 01:40 UTC; leaderboard fetched 2026-10-13T01:39. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2239 | +381 |
| Knight Vision | 2090 | +232 |
| Decent Chess Bot | 2033 | +175 |
| Strongly Invisible | 2055 | +197 |
| **duck** | 1985 | +127 |
| **Instructors** | 1910 | +52 |
| TA Baseline S | 1695 | -163 |
| **IAmAVirus** | 1858 |  |
| TA Baseline A | 1586 | -272 |
| TA Baseline P | 1477 | -381 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-3 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot |  | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible |  | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 0-0-4 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 4-0-4 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P |  | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 2-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S |  | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.8 | 36.8 | 32.1 | 37.5 | 36.6 | 30.7 | 32.3 |
|  | vision-gaining moves | 23.3 | 21.4 | 16.0 | 20.0 | 22.7 | 17.1 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.34 ⚠ | 0.44 | 0.48 | 0.32 | 0.74 | 0.27 | 0.39 |
|  | captures from unseen squares | 8.4 ⚠ | 12.0 | 8.4 | 9.2 | 22.7 | 7.9 | 7.7 |
|  | captures after a route the other side never saw | 18.2 | 18.3 | 12.2 ⚠ | 16.9 | 25.3 | 18.4 | 14.2 |
|  | long slider strikes | 4.8 ⚠ | 6.1 | 3.1 ⚠ | 4.6 | 8.0 | 6.6 | 4.1 |
| King pressure | moves that attack the enemy king | 5.1 ⚠ | 6.6 | 3.8 | 4.6 | 2.7 | 0.0 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.3 ⚠ | 3.8 | 1.5 ⚠ | 3.1 | 2.7 | 0.0 | 1.4 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 5.6 | 7.4 | 6.9 | 6.2 | 9.3 | 2.6 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.3 ⚠ | 1.3 | 8.4 ⚠ | 3.1 | 1.3 | 5.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.3 ⚠ | 1.8 | 2.3 | 1.5 | 0.0 | 2.6 | 3.0 |
|  | queen left attacked by an unseen piece | 0.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 13.7 ⚠ | 1.0 | 14.5 ⚠ | 1.5 | 0.0 | 7.9 | 4.7 |
| King handling | king moves | 9.9 | 9.2 | 13.7 | 5.4 | 6.7 | 3.9 | 16.1 |
|  | king moves beyond the second rank | 1.3 | 2.0 | 1.5 | 0.0 | 0.0 | 0.0 | 5.2 |
|  | castling | 2.3 | 2.3 | 1.5 | 3.1 | 1.3 | 1.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 5-0-11; 11 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 6 | 4 |
| king left to an attacker we could see (no safe move existed) | 2 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 2 | 2 |
| king already attacked by an unseen piece | 1 | 1 |

Pieces that took our king: q 7, r 3, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 7, late (70+) or never 3 down 2, middlegame (30-69) 2.
- Down 3 or more at some point in 10 of 11 losses; median first ply 22.0.
- Down 5 or more in 9; median first ply 40.
- Lost although we had led by 3 or more: 1 of 11.
- Our clock at 15 s or less: 0 of 11.
- Median length 70 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 4 |
| capturer unseen when we moved, piece had just moved there (r) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |
| capturer visible when we moved (p) | 1 |

## What worked: v34's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| gzj7ox1o | Instructors | W | win | 66 | King capturable |
| y4qk2v2b | Instructors | B | win | 9 | King capturable |
| np6c6tub | Instructors | B | win | 61 | King capturable |
| 05l0ejxw | Instructors | W | win | 66 | King capturable |
| 19pwd8n9 | Knight Vision | W | win | 50 | King capturable |
