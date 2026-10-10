# Against the top six

Updated 2026-10-10 00:16 UTC; leaderboard fetched 2026-10-10T00:15. Active version: v23. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2195 | +600 |
| Knight Vision | 2129 | +534 |
| Decent Chess Bot | 2114 | +520 |
| Strongly Invisible | 2054 | +460 |
| **duck** | 1927 | +332 |
| **Instructors** | 1906 | +311 |
| TA Baseline S | 1670 | +75 |
| **IAmAVirus** | 1595 |  |
| TA Baseline A | 1540 | -55 |
| TA Baseline P | 1450 | -145 |

## Record by version (W-D-L)

| opponent | v23 | v22 | v21 | v20 | v19 | v18 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  |  | 0-0-2 | 0-0-2 |  | 0-0-4 |
| Knight Vision |  |  | 0-0-16 | 0-0-6 |  | 0-0-4 |
| Decent Chess Bot |  |  | 1-1-26 | 0-0-10 |  | 0-1-9 |
| Strongly Invisible |  |  | 0-1-13 | 0-2-10 |  | 0-0-2 |
| **duck** | 0-0-4 |  | 0-2-6 | 4-1-11 |  | 0-0-4 |
| **Instructors** | 2-0-2 | 1-0-1 | 3-1-10 | 2-0-8 |  | 3-0-5 |
| TA Baseline P |  | 3-1-0 | 29-5-8 | 15-0-3 | 2-0-0 | 9-0-3 |
| TA Baseline A | 1-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |  | 7-2-5 |
| TA Baseline S |  | 0-1-1 | 11-4-9 | 5-4-7 |  | 3-1-12 |

## Skill gaps (rates per 100 moves unless noted)

Active version v23. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.3 | 35.0 | 28.5 ⚠ | 36.2 | 32.5 |
|  | vision-gaining moves | 17.7 | 20.4 | 21.8 | 17.7 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.37 ⚠ | 0.54 | 0.59 | 0.47 | 0.40 |
|  | captures from unseen squares | 7.9 ⚠ | 11.9 | 10.3 | 11.6 | 8.0 |
|  | captures after a route the other side never saw | 14.5 | 15.9 | 12.7 | 14.0 | 14.6 |
|  | long slider strikes | 4.5 | 3.2 | 1.8 ⚠ | 4.3 | 4.2 |
| King pressure | moves that attack the enemy king | 2.1 ⚠ | 5.0 | 2.4 ⚠ | 6.7 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.3 ⚠ | 2.7 | 0.6 ⚠ | 2.4 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 | 0.6 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.4 | 1.9 | 0.0 | 2.4 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.4 ⚠ | 1.1 | 3.6 ⚠ | 2.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.1 | 2.1 | 2.4 | 1.8 | 2.9 |
|  | queen left attacked by an unseen piece | 0.5 | 0.3 | 0.0 | 0.0 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 1.8 | 5.8 | 16.4 ⚠ | 1.2 | 4.8 |
| King handling | king moves | 15.0 | 10.9 | 27.3 | 6.1 | 16.1 |
|  | king moves beyond the second rank | 4.7 | 4.0 | 1.8 | 0.0 | 4.9 |
|  | castling | 1.8 | 2.1 | 2.4 | 2.4 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v23 against the top six

Record 2-0-6; 6 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 4 | 4 |
| king already attacked by an unseen piece | 1 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 1 |

Pieces that took our king: q 3, r 2, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: late (70+) or never 3 down 3, middlegame (30-69) 3.
- Down 3 or more at some point in 5 of 6 losses; median first ply 62.
- Down 5 or more in 4; median first ply 54.5.
- Lost although we had led by 3 or more: 0 of 6.
- Our clock at 15 s or less: 2 of 6.
- Median length 89.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |
| capturer unseen when we moved, piece had just moved there (r) | 1 |
| other | 1 |

## What worked: v23's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| oyhs29v2 | Instructors | B | win | 75 | King capturable |
| dc1ebyd9 | Instructors | W | win | 124 | King capturable |
