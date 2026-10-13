# Against the top six

Updated 2026-10-13 02:21 UTC; leaderboard fetched 2026-10-13T02:20. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2228 | +361 |
| Knight Vision | 2102 | +235 |
| Decent Chess Bot | 2038 | +171 |
| Strongly Invisible | 2046 | +179 |
| **duck** | 1980 | +114 |
| **Instructors** | 1934 | +68 |
| TA Baseline S | 1693 | -174 |
| **IAmAVirus** | 1867 |  |
| TA Baseline A | 1577 | -290 |
| TA Baseline P | 1472 | -395 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-3 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 0-0-2 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible |  | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 0-0-5 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 4-0-4 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P |  | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 2-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 2-0-0 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.9 | 36.9 | 31.8 | 36.4 | 36.9 | 31.9 | 32.3 |
|  | vision-gaining moves | 23.2 | 21.9 | 18.1 | 19.3 | 21.2 | 17.0 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.36 | 0.44 | 0.44 | 0.33 | 0.61 | 0.31 | 0.39 |
|  | captures from unseen squares | 9.0 ⚠ | 11.9 | 8.3 | 8.4 | 15.2 | 7.8 | 7.7 |
|  | captures after a route the other side never saw | 18.4 | 18.6 | 14.2 | 17.2 | 20.5 | 15.7 | 14.2 |
|  | long slider strikes | 4.7 ⚠ | 6.0 | 3.1 ⚠ | 4.2 | 7.3 | 5.9 | 4.1 |
| King pressure | moves that attack the enemy king | 4.7 ⚠ | 6.4 | 3.5 ⚠ | 7.0 | 3.3 | 0.0 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.2 ⚠ | 3.6 | 0.7 ⚠ | 4.9 | 2.6 | 0.0 | 1.4 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 | 0.4 | 1.3 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 5.7 | 7.4 | 4.2 | 8.1 | 8.6 | 1.3 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.3 ⚠ | 1.2 | 6.9 ⚠ | 2.1 | 2.6 | 4.6 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.5 ⚠ | 1.7 | 2.4 ⚠ | 1.4 | 0.0 | 2.6 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 13.0 ⚠ | 1.0 | 8.7 ⚠ | 2.8 | 0.0 | 5.2 | 4.7 |
| King handling | king moves | 9.9 | 8.8 | 19.1 | 7.7 | 6.0 | 5.2 | 16.1 |
|  | king moves beyond the second rank | 1.2 | 1.9 | 5.9 | 0.7 | 0.0 | 0.0 | 5.2 |
|  | castling | 2.4 | 2.4 | 2.1 | 2.8 | 1.3 | 2.0 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 5-0-16; 16 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 7 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 4 | 2 |
| king left to an attacker we could see (no safe move existed) | 2 | 1 |
| king already attacked by an unseen piece | 1 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 0 |
| our move opened a line from an unseen attacker | 1 | 1 |

Pieces that took our king: q 11, r 4, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 7, middlegame (30-69) 6, late (70+) or never 3 down 3.
- Down 3 or more at some point in 15 of 16 losses; median first ply 30.
- Down 5 or more in 14; median first ply 44.0.
- Lost although we had led by 3 or more: 1 of 16.
- Our clock at 15 s or less: 0 of 16.
- Median length 67.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 6 |
| capturer unseen when we moved, piece had just moved there (r) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved (n) | 1 |
| capturer visible when we moved (p) | 1 |

## What worked: v34's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| gzj7ox1o | Instructors | W | win | 66 | King capturable |
| y4qk2v2b | Instructors | B | win | 9 | King capturable |
| np6c6tub | Instructors | B | win | 61 | King capturable |
| 05l0ejxw | Instructors | W | win | 66 | King capturable |
| 19pwd8n9 | Knight Vision | W | win | 50 | King capturable |
