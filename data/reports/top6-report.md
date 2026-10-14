# Against the top six

Updated 2026-10-14 07:29 UTC; leaderboard fetched 2026-10-14T07:28. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2240 | +412 |
| Knight Vision | 2125 | +297 |
| Decent Chess Bot | 2046 | +218 |
| Strongly Invisible | 2101 | +273 |
| **duck** | 1990 | +162 |
| **Instructors** | 1893 | +65 |
| TA Baseline S | 1660 | -169 |
| **IAmAVirus** | 1828 |  |
| TA Baseline A | 1551 | -277 |
| TA Baseline P | 1450 | -378 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision |  | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible |  | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 1-0-1 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 0-0-2 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A |  | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 2-0-0 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.2 | 36.4 | 32.9 | 36.9 | 34.4 | 28.9 | 33.1 |
|  | vision-gaining moves | 23.1 | 20.1 | 23.8 | 21.0 | 17.2 | 18.0 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 ⚠ | 0.54 | 0.50 | 0.28 | 0.42 ⚠ | 0.68 | 0.41 |
|  | captures from unseen squares | 9.4 ⚠ | 12.6 | 11.1 | 8.1 | 11.1 ⚠ | 15.0 | 8.5 |
|  | captures after a route the other side never saw | 15.6 | 15.7 | 15.9 | 19.4 | 22.2 | 14.0 | 14.9 |
|  | long slider strikes | 6.2 | 6.9 | 4.8 | 3.2 | 4.0 | 5.0 | 4.3 |
| King pressure | moves that attack the enemy king | 2.5 ⚠ | 3.8 | 4.8 | 3.2 | 6.1 | 4.0 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.9 | 2.5 | 0.0 | 0.0 | 4.0 | 0.0 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 ⚠ | 1.6 | 0.0 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 5.0 | 5.0 | 1.6 | 3.2 | 4.0 | 1.0 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.4 ⚠ | 0.6 | 4.8 ⚠ | 1.6 | 1.0 | 2.0 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.5 | 2.5 | 3.2 ⚠ | 1.6 | 3.0 | 3.0 | 3.1 |
|  | queen left attacked by an unseen piece | 0.6 | 0.0 | 0.0 | 0.0 | 0.0 | 2.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 8.1 | 11.3 | 0.0 | 0.0 | 3.0 | 5.0 | 5.7 |
| King handling | king moves | 8.8 | 7.5 | 9.5 | 6.5 | 10.1 | 15.0 | 15.2 |
|  | king moves beyond the second rank | 1.9 | 0.0 | 3.2 | 3.2 | 4.0 | 4.0 | 4.4 |
|  | castling | 1.9 | 2.5 | 3.2 | 1.6 | 2.0 | 1.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 1-0-5; 5 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 2 | 2 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 0 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |
| king already attacked by an unseen piece | 1 | 1 |

Pieces that took our king: r 2, q 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 2, middlegame (30-69) 2, late (70+) or never 3 down 1.
- Down 3 or more at some point in 4 of 5 losses; median first ply 28.0.
- Down 5 or more in 3; median first ply 30.
- Lost although we had led by 3 or more: 0 of 5.
- Our clock at 15 s or less: 0 of 5.
- Median length 70 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved, piece had just moved there (q) | 1 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer unseen when we moved, piece had just moved there (r) | 1 |

## What worked: v35's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| ol5e72pm | duck | B | win | 97 | King capturable |
