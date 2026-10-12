# Against the top six

Updated 2026-10-12 00:42 UTC; leaderboard fetched 2026-10-12T00:42. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2158 | +393 |
| Knight Vision | 2112 | +347 |
| Decent Chess Bot | 2039 | +273 |
| Strongly Invisible | 2059 | +293 |
| **duck** | 1970 | +205 |
| **Instructors** | 1931 | +165 |
| TA Baseline S | 1633 | -133 |
| **IAmAVirus** | 1766 |  |
| TA Baseline A | 1531 | -234 |
| TA Baseline P | 1426 | -339 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-2 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 2-0-4 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-0-5 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 1-0-5 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-4 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 2-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 2-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 7-0-1 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.2 | 35.3 | 32.3 | 36.4 | 34.1 | 28.7 | 32.7 |
|  | vision-gaining moves | 20.6 | 21.9 | 19.3 | 23.0 | 22.8 | 16.5 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.43 | 0.45 | 0.39 | 0.45 | 0.37 | 0.40 |
|  | captures from unseen squares | 9.2 ⚠ | 11.8 | 10.1 | 12.1 | 11.2 | 8.4 | 8.3 |
|  | captures after a route the other side never saw | 13.9 ⚠ | 19.1 | 16.6 ⚠ | 21.7 | 18.2 | 15.6 | 15.0 |
|  | long slider strikes | 4.5 | 4.8 | 4.8 ⚠ | 6.4 | 3.9 | 4.8 | 4.4 |
| King pressure | moves that attack the enemy king | 3.5 | 4.3 | 4.4 | 5.0 | 5.8 | 3.1 | 3.6 |
|  | ...with an attacker the king's side cannot see | 1.2 | 2.0 | 1.8 ⚠ | 2.9 | 2.9 | 0.5 | 1.6 |
|  | sacrifices that lead to a king capture | 0.2 | 0.8 | 0.4 | 0.4 | 0.7 | 0.5 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.2 | 5.0 | 3.2 | 4.5 | 3.6 | 1.7 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 5.5 ⚠ | 1.5 | 6.9 ⚠ | 1.6 | 1.0 | 3.1 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.7 ⚠ | 2.5 | 4.1 ⚠ | 2.0 | 1.5 | 2.4 | 2.9 |
|  | queen left attacked by an unseen piece | 0.7 | 0.0 | 0.5 | 0.0 | 0.5 | 0.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 12.2 ⚠ | 4.8 | 11.3 ⚠ | 2.3 | 1.9 | 4.6 | 5.3 |
| King handling | king moves | 20.6 | 9.0 | 13.8 | 8.7 | 9.5 | 28.3 | 15.8 |
|  | king moves beyond the second rank | 1.5 | 1.5 | 2.3 | 1.4 | 2.9 | 9.8 | 5.0 |
|  | castling | 2.2 | 2.3 | 2.8 | 2.1 | 1.7 | 1.7 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 4-0-22; 22 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 9 | 4 |
| king already attacked by an unseen piece | 5 | 0 |
| king walked into an unseen attacker after taking the bait (king capture) | 5 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 3 | 2 |

Pieces that took our king: r 9, q 7, n 3, b 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 13, opening (ply < 30) 8, late (70+) or never 3 down 1.
- Down 3 or more at some point in 21 of 22 losses; median first ply 39.
- Down 5 or more in 20; median first ply 42.5.
- Lost although we had led by 3 or more: 0 of 22.
- Our clock at 15 s or less: 0 of 22.
- Median length 77.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 8 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved, piece had just moved there (n) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
| capturer unseen when we moved (q) | 1 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
| z34nungm | Decent Chess Bot | B | win | 31 | King capturable |
| 43dabbw9 | Decent Chess Bot | W | win | 70 | King capturable |
| zu9sjnr6 | duck | W | win | 84 | King capturable |
