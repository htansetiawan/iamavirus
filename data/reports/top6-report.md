# Against the top six

Updated 2026-10-11 22:59 UTC; leaderboard fetched 2026-10-11T22:59. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2155 | +398 |
| Knight Vision | 2101 | +345 |
| Decent Chess Bot | 2064 | +307 |
| Strongly Invisible | 2040 | +283 |
| **duck** | 1967 | +210 |
| **Instructors** | 1928 | +172 |
| TA Baseline S | 1654 | -103 |
| **IAmAVirus** | 1756 |  |
| TA Baseline A | 1523 | -233 |
| TA Baseline P | 1422 | -334 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision |  | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot |  |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-0-3 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** |  | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** |  | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 2-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A |  | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S |  | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.3 | 37.9 | 40.2 | 37.0 | 32.7 |
|  | vision-gaining moves | 22.6 | 25.8 | 26.9 | 11.1 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.47 | 0.41 | 0.33 | 0.29 | 0.40 |
|  | captures from unseen squares | 10.5 ⚠ | 13.6 | 7.7 | 7.4 | 8.3 |
|  | captures after a route the other side never saw | 17.3 ⚠ | 23.5 | 15.4 | 18.5 | 15.0 |
|  | long slider strikes | 5.3 | 5.3 | 3.8 | 0.0 | 4.4 |
| King pressure | moves that attack the enemy king | 3.8 ⚠ | 5.3 | 3.8 | 0.0 | 3.6 |
|  | ...with an attacker the king's side cannot see | 1.5 ⚠ | 4.5 | 0.0 | 0.0 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 3.8 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.0 | 9.1 | 3.8 | 0.0 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 6.0 ⚠ | 0.8 | 3.8 ⚠ | 0.0 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.8 ⚠ | 2.3 | 0.0 | 0.0 | 2.9 |
|  | queen left attacked by an unseen piece | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 8.3 ⚠ | 3.0 | 0.0 | 0.0 | 5.3 |
| King handling | king moves | 12.0 | 5.3 | 3.8 | 7.4 | 15.8 |
|  | king moves beyond the second rank | 1.5 | 0.0 | 0.0 | 0.0 | 5.0 |
|  | castling | 3.0 | 3.0 | 3.8 | 3.7 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 1-0-3; 3 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king already attacked by an unseen piece | 1 | 0 |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |
| king walked into an unseen attacker | 1 | 0 |

Pieces that took our king: r 1, b 1, q 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 2, opening (ply < 30) 1.
- Down 3 or more at some point in 3 of 3 losses; median first ply 37.
- Down 5 or more in 3; median first ply 37.
- Lost although we had led by 3 or more: 0 of 3.
- Our clock at 15 s or less: 0 of 3.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 2 |
| capturer visible when we moved, piece had just moved there (n) | 1 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
