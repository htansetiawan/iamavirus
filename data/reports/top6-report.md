# Against the top six

Updated 2026-10-14 08:12 UTC; leaderboard fetched 2026-10-14T08:11. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2251 | +428 |
| Knight Vision | 2105 | +282 |
| Decent Chess Bot | 2037 | +214 |
| Strongly Invisible | 2104 | +281 |
| **duck** | 1992 | +169 |
| **Instructors** | 1914 | +91 |
| TA Baseline S | 1652 | -171 |
| **IAmAVirus** | 1823 |  |
| TA Baseline A | 1531 | -292 |
| TA Baseline P | 1459 | -364 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision |  | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible |  | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 1-0-1 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 1-0-3 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 2-0-0 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.9 | 35.1 | 32.9 | 36.9 | 37.6 | 31.7 | 33.1 |
|  | vision-gaining moves | 21.5 | 20.7 | 23.8 | 21.0 | 21.8 | 19.3 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.38 ⚠ | 0.52 | 0.50 | 0.28 | 0.45 | 0.42 | 0.41 |
|  | captures from unseen squares | 8.5 ⚠ | 12.2 | 11.1 | 8.1 | 11.2 | 9.2 | 8.5 |
|  | captures after a route the other side never saw | 15.8 | 16.3 | 15.9 | 19.4 | 18.6 | 13.6 | 14.9 |
|  | long slider strikes | 5.3 ⚠ | 7.3 | 4.8 | 3.2 | 5.4 | 4.7 | 4.3 |
| King pressure | moves that attack the enemy king | 2.8 ⚠ | 4.1 | 4.8 | 3.2 | 5.4 | 1.9 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.2 | 1.6 | 0.0 | 0.0 | 3.5 | 0.3 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 ⚠ | 1.6 | 0.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.6 | 4.5 | 1.6 | 3.2 | 4.2 | 0.6 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.0 ⚠ | 1.2 | 4.8 ⚠ | 1.6 | 1.0 | 2.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 1.6 | 2.8 | 3.2 ⚠ | 1.6 | 1.9 | 3.8 | 3.1 |
|  | queen left attacked by an unseen piece | 0.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.9 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 6.1 | 8.9 | 0.0 | 0.0 | 4.2 | 3.8 | 5.7 |
| King handling | king moves | 11.3 | 12.2 | 9.5 | 6.5 | 7.1 | 11.4 | 15.2 |
|  | king moves beyond the second rank | 2.8 | 1.2 | 3.2 | 3.2 | 1.3 | 1.9 | 4.4 |
|  | castling | 2.0 | 2.4 | 3.2 | 1.6 | 1.9 | 1.9 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 2-0-6; 6 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 3 | 3 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 0 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |
| king already attacked by an unseen piece | 1 | 1 |

Pieces that took our king: r 2, q 2, k 1, p 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: opening (ply < 30) 3, middlegame (30-69) 2, late (70+) or never 3 down 1.
- Down 3 or more at some point in 5 of 6 losses; median first ply 26.
- Down 5 or more in 4; median first ply 35.5.
- Lost although we had led by 3 or more: 0 of 6.
- Our clock at 15 s or less: 0 of 6.
- Median length 71.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |
| capturer unseen when we moved, piece had just moved there (q) | 1 |
| capturer unseen when we moved, piece had just moved there (b) | 1 |
| capturer unseen when we moved, piece had just moved there (r) | 1 |

## What worked: v35's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| ol5e72pm | duck | B | win | 97 | King capturable |
| 61bzys3l | Instructors | W | win | 98 | King capturable |
