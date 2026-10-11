# Against the top six

Updated 2026-10-11 23:41 UTC; leaderboard fetched 2026-10-11T23:40. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2159 | +404 |
| Knight Vision | 2101 | +346 |
| Decent Chess Bot | 2050 | +296 |
| Strongly Invisible | 2067 | +313 |
| **duck** | 1965 | +210 |
| **Instructors** | 1930 | +175 |
| TA Baseline S | 1645 | -110 |
| **IAmAVirus** | 1754 |  |
| TA Baseline A | 1522 | -233 |
| TA Baseline P | 1425 | -329 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-2 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 1-0-3 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-0-3 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 0-0-4 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-2 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 2-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A |  | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 2-0-0 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 29.9 | 36.0 | 32.1 | 37.4 | 34.0 | 27.8 | 32.7 |
|  | vision-gaining moves | 20.1 | 23.3 | 21.3 | 22.7 | 22.1 | 23.6 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 | 0.47 | 0.45 | 0.41 | 0.34 | 0.29 | 0.40 |
|  | captures from unseen squares | 8.4 ⚠ | 13.6 | 10.5 ⚠ | 13.6 | 9.6 | 6.6 | 8.3 |
|  | captures after a route the other side never saw | 13.4 ⚠ | 21.6 | 16.5 ⚠ | 21.5 | 18.3 | 16.0 | 15.0 |
|  | long slider strikes | 4.2 | 4.7 | 4.2 ⚠ | 6.4 | 4.8 | 4.7 | 4.4 |
| King pressure | moves that attack the enemy king | 3.3 | 4.2 | 4.5 | 4.8 | 4.8 | 2.8 | 3.6 |
|  | ...with an attacker the king's side cannot see | 1.7 | 2.1 | 2.1 ⚠ | 3.3 | 1.9 | 0.0 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.4 | 0.3 | 0.3 | 1.0 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.7 | 5.5 | 2.1 | 5.5 | 5.8 | 0.0 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 5.9 ⚠ | 0.4 | 8.7 ⚠ | 1.8 | 1.0 | 3.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.8 ⚠ | 0.8 | 4.5 ⚠ | 2.1 | 0.0 | 0.0 | 2.9 |
|  | queen left attacked by an unseen piece | 0.8 | 0.0 | 0.6 | 0.0 | 0.0 | 0.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 14.2 ⚠ | 5.5 | 12.3 ⚠ | 1.5 | 0.0 | 1.9 | 5.3 |
| King handling | king moves | 23.0 | 9.7 | 12.0 | 7.0 | 11.5 | 29.2 | 15.8 |
|  | king moves beyond the second rank | 2.1 | 2.5 | 0.9 | 0.6 | 4.8 | 3.8 | 5.0 |
|  | castling | 2.1 | 2.5 | 3.0 | 1.8 | 1.9 | 1.9 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 2-0-14; 14 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 6 | 4 |
| king already attacked by an unseen piece | 4 | 0 |
| king walked into an unseen attacker after taking the bait (king capture) | 2 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 2 | 1 |

Pieces that took our king: r 6, q 4, n 3, b 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 9, opening (ply < 30) 5.
- Down 3 or more at some point in 14 of 14 losses; median first ply 40.0.
- Down 5 or more in 13; median first ply 44.
- Lost although we had led by 3 or more: 0 of 14.
- Our clock at 15 s or less: 0 of 14.
- Median length 77.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 6 |
| capturer unseen when we moved, piece had just moved there (r) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
| z34nungm | Decent Chess Bot | B | win | 31 | King capturable |
