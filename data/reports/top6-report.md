# Against the top six

Updated 2026-10-11 05:26 UTC; leaderboard fetched 2026-10-11T05:24. Active version: v32. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2130 | +395 |
| Knight Vision | 2061 | +326 |
| Decent Chess Bot | 2039 | +303 |
| Strongly Invisible | 2071 | +336 |
| **duck** | 1904 | +169 |
| **Instructors** | 1943 | +208 |
| TA Baseline S | 1667 | -68 |
| **IAmAVirus** | 1735 |  |
| TA Baseline A | 1556 | -179 |
| TA Baseline P | 1436 | -299 |

## Record by version (W-D-L)

| opponent | v32 | v30 | v28 | v27 | v26 | v25 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-1-3 |  |  |  | 0-0-18 |
| Knight Vision | 0-0-2 | 0-0-2 | 0-0-2 | 0-0-2 | 0-0-4 | 27-0-3 |
| Decent Chess Bot |  | 2-0-6 | 0-0-2 |  | 0-0-4 | 0-1-23 |
| Strongly Invisible |  | 1-1-4 | 0-0-2 |  |  | 2-0-34 |
| **duck** | 0-0-4 | 3-2-7 | 1-0-3 |  |  | 9-9-42 |
| **Instructors** | 2-0-4 | 1-0-3 | 1-0-1 |  | 0-0-2 | 12-5-41 |
| TA Baseline P |  | 4-0-0 | 2-0-0 | 1-0-1 |  | 47-4-7 |
| TA Baseline A | 4-0-0 | 8-3-1 | 3-0-1 | 1-0-1 | 2-1-1 | 57-12-27 |
| TA Baseline S | 3-0-3 | 6-1-3 | 4-0-0 |  | 2-0-2 | 30-8-30 |

## Skill gaps (rates per 100 moves unless noted)

Active version v32. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.5 | 32.5 | 30.0 ⚠ | 38.2 | 32.8 | 33.0 | 32.5 |
|  | vision-gaining moves | 21.9 | 21.6 | 23.0 | 23.4 | 19.0 | 17.4 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.40 ⚠ | 0.52 | 0.45 | 0.38 | 0.41 | 0.35 | 0.40 |
|  | captures from unseen squares | 9.2 ⚠ | 13.8 | 9.4 | 11.7 | 9.2 | 8.5 | 8.0 |
|  | captures after a route the other side never saw | 15.9 | 19.0 | 15.8 ⚠ | 21.9 | 15.6 | 17.2 | 14.6 |
|  | long slider strikes | 5.5 | 5.0 | 5.8 ⚠ | 7.3 | 4.4 ⚠ | 5.8 | 4.2 |
| King pressure | moves that attack the enemy king | 2.7 | 3.0 | 5.8 | 5.1 | 2.4 ⚠ | 3.6 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.7 | 1.3 | 2.2 | 2.2 | 1.2 | 1.0 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.3 | 0.0 ⚠ | 1.5 | 0.0 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.2 | 2.3 | 0.7 | 5.8 | 2.7 | 3.9 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.0 ⚠ | 1.0 | 7.2 ⚠ | 1.5 | 2.2 | 2.2 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.8 | 4.3 ⚠ | 0.7 | 1.9 | 2.9 | 2.9 |
|  | queen left attacked by an unseen piece | 0.7 | 0.3 | 0.0 | 0.7 | 0.0 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 4.5 | 4.8 | 4.3 ⚠ | 0.0 | 2.4 | 5.8 | 4.8 |
| King handling | king moves | 13.7 | 12.8 | 25.2 | 12.4 | 9.7 | 14.3 | 16.1 |
|  | king moves beyond the second rank | 6.2 | 1.8 | 6.5 | 5.1 | 3.6 | 3.1 | 4.9 |
|  | castling | 2.0 | 2.0 | 2.9 | 2.9 | 2.4 | 2.4 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v32 against the top six

Record 2-0-12; 12 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king already attacked by an unseen piece | 4 | 3 |
| king walked into an unseen attacker | 3 | 2 |
| king walked into an unseen attacker after taking the bait (king capture) | 3 | 2 |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |
| king left to an attacker we could see (no safe move existed) | 1 | 1 |

Pieces that took our king: r 6, q 3, b 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 7, opening (ply < 30) 4, late (70+) or never 3 down 1.
- Down 3 or more at some point in 11 of 12 losses; median first ply 33.
- Down 5 or more in 9; median first ply 36.
- Lost although we had led by 3 or more: 1 of 12.
- Our clock at 15 s or less: 0 of 12.
- Median length 67.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 4 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
| capturer unseen when we moved, piece had just moved there (r) | 2 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved (n) | 1 |
| capturer unseen when we moved (b) | 1 |

## What worked: v32's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| rotnqcus | Instructors | W | win | 108 | King capturable |
| d4ca125s | Instructors | W | win | 130 | King capturable |
