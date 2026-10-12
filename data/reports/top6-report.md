# Against the top six

Updated 2026-10-12 00:01 UTC; leaderboard fetched 2026-10-12T00:01. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2161 | +404 |
| Knight Vision | 2100 | +342 |
| Decent Chess Bot | 2040 | +283 |
| Strongly Invisible | 2070 | +313 |
| **duck** | 1975 | +218 |
| **Instructors** | 1936 | +178 |
| TA Baseline S | 1633 | -124 |
| **IAmAVirus** | 1757 |  |
| TA Baseline A | 1524 | -233 |
| TA Baseline P | 1423 | -334 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-2 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 2-0-4 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-0-5 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 0-0-4 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-4 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 2-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A |  | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 4-0-0 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 29.8 | 35.5 | 32.3 | 36.4 | 34.3 | 29.1 | 32.7 |
|  | vision-gaining moves | 20.3 | 23.3 | 19.3 | 23.0 | 22.7 | 19.6 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.45 | 0.45 | 0.39 | 0.41 | 0.29 | 0.40 |
|  | captures from unseen squares | 8.8 ⚠ | 12.6 | 10.1 | 12.1 | 11.6 | 7.1 | 8.3 |
|  | captures after a route the other side never saw | 13.0 ⚠ | 19.6 | 16.6 ⚠ | 21.7 | 18.2 | 16.3 | 15.0 |
|  | long slider strikes | 4.5 | 4.9 | 4.8 ⚠ | 6.4 | 4.4 | 4.9 | 4.4 |
| King pressure | moves that attack the enemy king | 3.3 | 4.0 | 4.4 | 5.0 | 6.6 | 2.2 | 3.6 |
|  | ...with an attacker the king's side cannot see | 1.5 | 1.8 | 1.8 ⚠ | 2.9 | 2.8 | 0.0 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.6 | 0.4 | 0.4 | 1.1 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.5 | 4.6 | 3.2 | 4.5 | 5.5 | 1.6 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 5.5 ⚠ | 0.9 | 6.9 ⚠ | 1.6 | 1.1 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.6 ⚠ | 1.8 | 4.1 ⚠ | 2.0 | 0.6 | 1.1 | 2.9 |
|  | queen left attacked by an unseen piece | 0.9 | 0.0 | 0.5 | 0.0 | 0.6 | 0.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 13.3 ⚠ | 4.0 | 11.3 ⚠ | 2.3 | 3.3 | 7.1 | 5.3 |
| King handling | king moves | 22.4 | 8.9 | 13.8 | 8.7 | 9.4 | 26.1 | 15.8 |
|  | king moves beyond the second rank | 1.8 | 1.8 | 2.3 | 1.4 | 3.3 | 3.8 | 5.0 |
|  | castling | 2.1 | 2.1 | 2.8 | 2.1 | 1.7 | 1.6 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 3-0-21; 21 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 9 | 4 |
| king already attacked by an unseen piece | 5 | 0 |
| king walked into an unseen attacker after taking the bait (king capture) | 4 | 2 |
| king already attacked by an unseen piece (no safe move existed) | 3 | 2 |

Pieces that took our king: r 9, q 7, n 3, b 1, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 13, opening (ply < 30) 7, late (70+) or never 3 down 1.
- Down 3 or more at some point in 20 of 21 losses; median first ply 40.0.
- Down 5 or more in 19; median first ply 44.
- Lost although we had led by 3 or more: 0 of 21.
- Our clock at 15 s or less: 0 of 21.
- Median length 78 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 8 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved, piece had just moved there (n) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer unseen when we moved (q) | 1 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
| z34nungm | Decent Chess Bot | B | win | 31 | King capturable |
| 43dabbw9 | Decent Chess Bot | W | win | 70 | King capturable |
