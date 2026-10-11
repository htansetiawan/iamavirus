# Against the top six

Updated 2026-10-11 23:20 UTC; leaderboard fetched 2026-10-11T23:19. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2157 | +396 |
| Knight Vision | 2090 | +328 |
| Decent Chess Bot | 2058 | +296 |
| Strongly Invisible | 2048 | +286 |
| **duck** | 1972 | +210 |
| **Instructors** | 1933 | +171 |
| TA Baseline S | 1649 | -113 |
| **IAmAVirus** | 1762 |  |
| TA Baseline A | 1526 | -235 |
| TA Baseline P | 1424 | -338 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-2 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 1-0-3 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-0-3 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** |  | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-2 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 2-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A |  | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 2-0-0 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.2 | 33.6 | 32.1 | 37.4 | 34.0 | 27.8 | 32.7 |
|  | vision-gaining moves | 21.4 | 18.8 | 21.3 | 22.7 | 22.1 | 23.6 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.33 ⚠ | 0.55 | 0.45 | 0.41 | 0.34 | 0.29 | 0.40 |
|  | captures from unseen squares | 8.6 ⚠ | 17.4 | 10.5 ⚠ | 13.6 | 9.6 | 6.6 | 8.3 |
|  | captures after a route the other side never saw | 12.9 ⚠ | 26.1 | 16.5 ⚠ | 21.5 | 18.3 | 16.0 | 15.0 |
|  | long slider strikes | 5.7 | 5.8 | 4.2 ⚠ | 6.4 | 4.8 | 4.7 | 4.4 |
| King pressure | moves that attack the enemy king | 5.7 | 5.8 | 4.5 | 4.8 | 4.8 | 2.8 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.9 | 2.9 | 2.1 ⚠ | 3.3 | 1.9 | 0.0 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 ⚠ | 1.4 | 0.3 | 0.3 | 1.0 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.4 | 4.3 | 2.1 | 5.5 | 5.8 | 0.0 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.3 ⚠ | 1.4 | 8.7 ⚠ | 1.8 | 1.0 | 3.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.9 ⚠ | 0.0 | 4.5 ⚠ | 2.1 | 0.0 | 0.0 | 2.9 |
|  | queen left attacked by an unseen piece | 1.4 ⚠ | 0.0 | 0.6 | 0.0 | 0.0 | 0.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 10.0 | 15.9 | 12.3 ⚠ | 1.5 | 0.0 | 1.9 | 5.3 |
| King handling | king moves | 15.7 | 13.0 | 12.0 | 7.0 | 11.5 | 29.2 | 15.8 |
|  | king moves beyond the second rank | 2.9 | 2.9 | 0.9 | 0.6 | 4.8 | 3.8 | 5.0 |
|  | castling | 2.9 | 2.9 | 3.0 | 1.8 | 1.9 | 1.9 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 2-0-10; 10 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king already attacked by an unseen piece | 4 | 0 |
| king walked into an unseen attacker | 3 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 2 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |

Pieces that took our king: r 5, n 2, q 2, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 7, opening (ply < 30) 3.
- Down 3 or more at some point in 10 of 10 losses; median first ply 40.0.
- Down 5 or more in 9; median first ply 41.
- Lost although we had led by 3 or more: 0 of 10.
- Our clock at 15 s or less: 0 of 10.
- Median length 76.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 5 |
| capturer unseen when we moved, piece had just moved there (r) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
| z34nungm | Decent Chess Bot | B | win | 31 | King capturable |
