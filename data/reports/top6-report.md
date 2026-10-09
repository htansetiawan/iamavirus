# Against the top six

Updated 2026-10-09 15:11 UTC; leaderboard fetched 2026-10-09T15:11. Active version: v20+21. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2179 | +544 |
| Knight Vision | 2150 | +515 |
| Decent Chess Bot | 2111 | +476 |
| Strongly Invisible | 2073 | +437 |
| **duck** | 1917 | +282 |
| **Instructors** | 1892 | +257 |
| TA Baseline S | 1690 | +55 |
| **IAmAVirus** | 1635 |  |
| TA Baseline A | 1592 | -44 |
| TA Baseline P | 1450 | -185 |

## Record by version (W-D-L)

| opponent | v21 | v20 | v19 | v18 | v17 | v16 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift |  | 0-0-2 |  | 0-0-4 | 0-0-4 |  |
| Knight Vision |  | 0-0-6 |  | 0-0-4 | 0-0-2 |  |
| Decent Chess Bot | 0-0-2 | 0-0-10 |  | 0-1-9 | 0-0-2 |  |
| Strongly Invisible |  | 0-2-10 |  | 0-0-2 |  | 0-0-6 |
| **duck** | 0-0-1 | 4-1-11 |  | 0-0-4 | 1-0-1 | 0-0-2 |
| **Instructors** | 2-0-0 | 2-0-8 |  | 3-0-5 | 1-0-3 | 0-0-2 |
| TA Baseline P | 2-0-0 | 15-0-3 | 2-0-0 | 9-0-3 | 3-1-2 | 1-1-2 |
| TA Baseline A | 2-1-1 | 11-3-12 |  | 7-2-5 | 2-0-2 | 2-0-2 |
| TA Baseline S |  | 5-4-7 |  | 3-1-12 | 2-1-5 | 1-0-1 |

## Skill gaps (rates per 100 moves unless noted)

Active version v20+21. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.4 | 34.2 | 30.8 | 36.6 | 33.1 | 31.6 | 32.5 |
|  | vision-gaining moves | 20.3 | 19.0 | 18.8 | 22.7 | 22.0 | 19.4 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.33 ⚠ | 0.45 | 0.28 ⚠ | 0.42 | 0.41 | 0.38 | 0.40 |
|  | captures from unseen squares | 7.5 ⚠ | 10.3 | 5.4 ⚠ | 10.3 | 10.1 | 8.5 | 8.0 |
|  | captures after a route the other side never saw | 14.4 | 15.5 | 13.2 ⚠ | 17.2 | 18.3 | 15.0 | 14.6 |
|  | long slider strikes | 4.3 | 4.6 | 3.2 ⚠ | 6.1 | 4.1 ⚠ | 5.8 | 4.2 |
| King pressure | moves that attack the enemy king | 2.4 | 2.8 | 1.3 ⚠ | 6.1 | 2.1 ⚠ | 4.0 | 3.3 |
|  | ...with an attacker the king's side cannot see | 1.3 | 1.0 | 0.4 ⚠ | 2.0 | 1.2 | 1.2 | 1.5 |
|  | sacrifices that lead to a king capture | 0.1 | 0.6 | 0.0 | 0.3 | 0.1 | 0.3 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.7 | 4.9 | 0.4 | 4.7 | 1.9 | 2.3 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.1 | 2.4 | 3.0 ⚠ | 0.5 | 1.7 | 3.1 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 2.4 | 3.5 | 3.0 | 2.0 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.3 | 0.1 | 0.1 | 0.2 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.5 | 6.5 | 2.4 | 5.7 | 1.5 | 8.0 | 4.8 |
| King handling | king moves | 9.8 | 11.4 | 15.3 | 7.2 | 11.2 | 12.3 | 16.1 |
|  | king moves beyond the second rank | 0.3 | 4.1 | 1.9 | 0.9 | 2.6 | 2.5 | 4.9 |
|  | castling | 2.3 | 2.3 | 2.1 | 2.1 | 2.1 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v20+21 against the top six

Record 8-3-50; 50 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 23 | 5 |
| king walked into an unseen attacker after taking the bait (king capture) | 14 | 9 |
| king already attacked by an unseen piece | 7 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 3 | 1 |
| our move opened a line from an unseen attacker | 3 | 2 |

Pieces that took our king: q 20, r 17, n 7, b 3, p 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 29, late (70+) or never 3 down 16, opening (ply < 30) 5.
- Down 3 or more at some point in 45 of 50 losses; median first ply 57.
- Down 5 or more in 40; median first ply 58.5.
- Lost although we had led by 3 or more: 8 of 50.
- Our clock at 15 s or less: 10 of 50.
- Median length 85.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 12 |
| capturer unseen when we moved, piece had just moved there (n) | 6 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer visible when we moved (q) | 4 |
| capturer unseen when we moved (q) | 4 |
| capturer unseen when we moved (p) | 3 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
| capturer unseen when we moved (b) | 1 |
| other | 1 |
| capturer unseen when we moved (n) | 1 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer visible when we moved (n) | 1 |

## What worked: v20+21's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| hhafy6qt | duck | W | win | 114 | King capturable |
| y2uobbz5 | duck | B | draw | 103 | Threefold repetition |
| qw4isxjp | Strongly Invisible | W | draw | 117 | Threefold repetition |
| v54nfn62 | Instructors | W | win | 88 | King capturable |
| t8m4vfh6 | Instructors | B | win | 101 | King capturable |
| w9w3l7e1 | duck | W | win | 72 | King capturable |
| ei1w3le2 | Strongly Invisible | W | draw | 101 | Threefold repetition |
| dbabc0gq | duck | B | win | 117 | King capturable |
| lo9hjq50 | duck | W | win | 96 | King capturable |
| o7syjm26 | Instructors | B | win | 81 | King capturable |
| cugdggr0 | Instructors | W | win | 82 | King capturable |
