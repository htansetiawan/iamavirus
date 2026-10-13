# Against the top six

Updated 2026-10-13 03:02 UTC; leaderboard fetched 2026-10-13T03:02. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2232 | +357 |
| Knight Vision | 2114 | +239 |
| Decent Chess Bot | 2033 | +158 |
| Strongly Invisible | 2031 | +156 |
| **duck** | 1974 | +99 |
| **Instructors** | 1941 | +66 |
| TA Baseline S | 1696 | -179 |
| **IAmAVirus** | 1875 |  |
| TA Baseline A | 1556 | -319 |
| TA Baseline P | 1479 | -396 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-4 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-3 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 1-0-3 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 0-0-2 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 2-0-6 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 4-0-4 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 2-0-0 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 4-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 4-0-0 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 34.4 | 36.9 | 31.8 | 35.7 | 36.2 | 31.0 | 32.3 |
|  | vision-gaining moves | 24.1 | 21.9 | 19.9 | 20.6 | 24.5 | 17.4 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.37 | 0.44 | 0.45 | 0.38 | 0.54 | 0.32 | 0.39 |
|  | captures from unseen squares | 9.5 ⚠ | 12.0 | 8.2 | 9.4 | 13.6 | 7.8 | 7.7 |
|  | captures after a route the other side never saw | 18.9 | 18.8 | 14.5 | 16.5 | 20.7 | 12.9 | 14.2 |
|  | long slider strikes | 5.6 | 6.6 | 3.6 | 4.2 | 6.0 | 4.6 | 4.1 |
| King pressure | moves that attack the enemy king | 4.8 ⚠ | 6.6 | 2.7 ⚠ | 5.6 | 5.4 | 1.9 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.5 ⚠ | 3.9 | 0.4 ⚠ | 3.6 | 4.6 | 0.0 | 1.4 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 | 0.2 | 0.8 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 6.2 | 8.1 | 3.8 | 5.6 | 6.2 | 1.1 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.9 ⚠ | 1.4 | 4.8 ⚠ | 1.6 | 1.9 | 5.6 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.3 | 2.3 | 2.0 | 1.3 | 0.3 | 4.8 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.0 | 0.4 | 0.2 | 0.3 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 10.8 ⚠ | 3.3 | 10.0 ⚠ | 3.4 | 0.0 | 7.8 | 4.7 |
| King handling | king moves | 10.2 | 8.3 | 21.5 | 9.4 | 8.7 | 12.1 | 16.1 |
|  | king moves beyond the second rank | 1.5 | 1.6 | 9.1 | 1.1 | 3.8 | 3.5 | 5.2 |
|  | castling | 2.5 | 2.5 | 2.0 | 2.5 | 1.6 | 1.9 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 8-0-22; 22 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 8 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 2 |
| king left to an attacker we could see (no safe move existed) | 4 | 2 |
| king already attacked by an unseen piece | 2 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 2 | 0 |
| our move opened a line from an unseen attacker | 1 | 1 |

Pieces that took our king: q 13, r 6, nq 1, n 1, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 11, opening (ply < 30) 8, late (70+) or never 3 down 3.
- Down 3 or more at some point in 21 of 22 losses; median first ply 33.
- Down 5 or more in 20; median first ply 40.5.
- Lost although we had led by 3 or more: 1 of 22.
- Our clock at 15 s or less: 0 of 22.
- Median length 67.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 9 |
| capturer unseen when we moved, piece had just moved there (r) | 3 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved (q) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
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
| sdr3y95n | Decent Chess Bot | W | win | 138 | King capturable |
| znv5996o | duck | W | win | 44 | King capturable |
| u5hyxqe5 | duck | B | win | 61 | King capturable |
