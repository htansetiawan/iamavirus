# Against the top six

Updated 2026-10-13 02:41 UTC; leaderboard fetched 2026-10-13T02:41. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2230 | +368 |
| Knight Vision | 2107 | +245 |
| Decent Chess Bot | 2034 | +172 |
| Strongly Invisible | 2036 | +174 |
| **duck** | 1991 | +129 |
| **Instructors** | 1930 | +69 |
| TA Baseline S | 1694 | -168 |
| **IAmAVirus** | 1862 |  |
| TA Baseline A | 1573 | -289 |
| TA Baseline P | 1472 | -390 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 1-0-3 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 1-0-3 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 0-0-2 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 0-0-6 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 4-0-4 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P |  | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 2-0-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 4-0-0 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.7 | 37.0 | 31.2 | 35.3 | 36.6 | 32.5 | 32.3 |
|  | vision-gaining moves | 23.2 | 21.6 | 19.0 | 20.0 | 24.2 | 18.3 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.38 | 0.44 | 0.40 | 0.39 | 0.55 | 0.31 | 0.39 |
|  | captures from unseen squares | 9.2 ⚠ | 12.1 | 7.0 ⚠ | 9.3 | 14.5 | 7.8 | 7.7 |
|  | captures after a route the other side never saw | 18.0 | 19.0 | 13.6 | 15.8 | 21.1 | 13.9 | 14.2 |
|  | long slider strikes | 5.2 | 6.0 | 3.2 | 3.6 | 7.0 | 4.8 | 4.1 |
| King pressure | moves that attack the enemy king | 4.5 ⚠ | 6.9 | 2.8 ⚠ | 5.7 | 5.3 | 1.3 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.3 ⚠ | 4.1 | 0.4 ⚠ | 3.8 | 4.4 | 0.0 | 1.4 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 | 0.2 | 0.9 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 5.6 | 8.2 | 3.2 | 5.5 | 7.9 | 1.3 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.3 ⚠ | 1.1 | 5.0 ⚠ | 1.6 | 1.8 | 5.7 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.6 ⚠ | 2.4 | 2.2 | 1.2 | 0.4 | 2.6 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.0 | 0.4 | 0.2 | 0.4 | 0.0 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 12.0 ⚠ | 0.9 | 9.6 ⚠ | 3.8 | 0.0 | 7.0 | 4.7 |
| King handling | king moves | 10.3 | 8.4 | 22.6 | 9.7 | 7.9 | 10.4 | 16.1 |
|  | king moves beyond the second rank | 1.7 | 1.7 | 10.0 | 1.2 | 2.2 | 2.2 | 5.2 |
|  | castling | 2.4 | 2.4 | 1.8 | 2.4 | 1.3 | 1.7 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 6-0-20; 20 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 7 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 2 |
| king left to an attacker we could see (no safe move existed) | 3 | 2 |
| king already attacked by an unseen piece | 2 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 2 | 0 |
| our move opened a line from an unseen attacker | 1 | 1 |

Pieces that took our king: q 12, r 5, nq 1, n 1, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 9, opening (ply < 30) 8, late (70+) or never 3 down 3.
- Down 3 or more at some point in 19 of 20 losses; median first ply 32.
- Down 5 or more in 18; median first ply 40.5.
- Lost although we had led by 3 or more: 1 of 20.
- Our clock at 15 s or less: 0 of 20.
- Median length 69.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 8 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved, piece had just moved there (r) | 2 |
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
