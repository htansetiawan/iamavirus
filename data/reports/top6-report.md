# Against the top six

Updated 2026-10-10 03:20 UTC; leaderboard fetched 2026-10-10T03:19. Active version: v25. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2182 | +562 |
| Knight Vision | 2055 | +435 |
| Decent Chess Bot | 2094 | +473 |
| Strongly Invisible | 2058 | +438 |
| **duck** | 1944 | +324 |
| **Instructors** | 1885 | +264 |
| TA Baseline S | 1647 | +27 |
| **IAmAVirus** | 1620 |  |
| TA Baseline A | 1554 | -66 |
| TA Baseline P | 1417 | -203 |

## Record by version (W-D-L)

| opponent | v25 | v24 | v23 | v22 | v21 | v20 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 0-0-2 |  |  | 0-0-2 | 0-0-2 |
| Knight Vision |  | 4-0-0 |  |  | 0-0-16 | 0-0-6 |
| Decent Chess Bot | 0-0-2 | 0-0-2 |  |  | 1-1-26 | 0-0-10 |
| Strongly Invisible | 1-0-1 | 1-0-7 |  |  | 0-1-13 | 0-2-10 |
| **duck** | 0-0-2 | 2-0-2 | 0-1-9 |  | 0-2-6 | 4-1-11 |
| **Instructors** | 1-0-4 | 0-0-4 | 3-0-3 | 1-0-1 | 3-1-10 | 2-0-8 |
| TA Baseline P | 8-0-2 | 1-1-2 | 4-0-0 | 3-1-0 | 29-5-8 | 15-0-3 |
| TA Baseline A | 3-1-0 | 1-0-1 | 3-0-3 | 4-2-0 | 14-5-17 | 11-3-12 |
| TA Baseline S |  | 0-0-4 | 2-0-0 | 0-1-1 | 11-4-9 | 5-4-7 |

## Skill gaps (rates per 100 moves unless noted)

Active version v25. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.8 | 35.4 | 33.6 | 38.3 | 35.7 | 30.5 | 32.5 |
|  | vision-gaining moves | 19.5 | 22.3 | 22.1 | 23.5 | 25.4 | 16.3 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.33 | 0.41 | 0.24 ⚠ | 0.39 | 0.44 | 0.37 | 0.40 |
|  | captures from unseen squares | 7.1 | 8.6 | 4.9 ⚠ | 9.3 | 11.3 | 7.9 | 8.0 |
|  | captures after a route the other side never saw | 13.9 | 13.7 | 13.5 ⚠ | 17.9 | 18.2 | 13.0 | 14.6 |
|  | long slider strikes | 4.2 ⚠ | 6.0 | 3.1 ⚠ | 7.4 | 5.1 | 6.1 | 4.2 |
| King pressure | moves that attack the enemy king | 1.4 ⚠ | 6.3 | 3.1 | 3.7 | 3.7 | 2.5 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.6 ⚠ | 2.0 | 2.5 | 1.2 | 3.0 | 0.7 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.6 | 0.0 | 0.0 | 0.4 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.3 | 4.0 | 1.2 | 4.3 | 2.6 | 1.6 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.8 ⚠ | 1.1 | 4.9 ⚠ | 2.5 | 1.6 | 4.6 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 2.0 | 5.5 ⚠ | 3.1 | 2.3 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.0 | 0.3 | 0.6 | 0.0 | 0.0 | 0.2 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 1.4 | 7.7 | 1.8 | 6.8 | 0.2 | 5.1 | 4.8 |
| King handling | king moves | 7.1 | 6.3 | 8.0 | 11.1 | 4.8 | 17.7 | 16.1 |
|  | king moves beyond the second rank | 1.1 | 0.6 | 0.6 | 1.2 | 0.4 | 4.2 | 4.9 |
|  | castling | 2.0 | 2.0 | 2.5 | 2.5 | 2.1 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v25 against the top six

Record 2-0-9; 9 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king already attacked by an unseen piece | 3 | 3 |
| king walked into an unseen attacker | 2 | 1 |
| our move opened a line from an unseen attacker | 1 | 0 |
| king left to an attacker we could see (no safe move existed) | 1 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 1 | 0 |

Pieces that took our king: q 6, r 3

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 6, late (70+) or never 3 down 3.
- Down 3 or more at some point in 9 of 9 losses; median first ply 63.
- Down 5 or more in 9; median first ply 68.
- Lost although we had led by 3 or more: 0 of 9.
- Our clock at 15 s or less: 0 of 9.
- Median length 98 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 3 |
| capturer unseen when we moved, piece had just moved there (q) | 2 |
| capturer unseen when we moved (n) | 1 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer visible when we moved, piece had just moved there (p) | 1 |

## What worked: v25's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| 58swoa7s | Strongly Invisible | W | win | 104 | King capturable |
| 7he7y2og | Instructors | B | win | 83 | King capturable |
