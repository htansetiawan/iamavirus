# Against the top six

Updated 2026-10-09 20:18 UTC; leaderboard fetched 2026-10-09T20:17. Active version: v20+21. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2163 | +567 |
| Knight Vision | 2135 | +538 |
| Decent Chess Bot | 2089 | +493 |
| Strongly Invisible | 2089 | +493 |
| **duck** | 1973 | +376 |
| **Instructors** | 1928 | +331 |
| TA Baseline S | 1674 | +78 |
| **IAmAVirus** | 1596 |  |
| TA Baseline A | 1568 | -28 |
| TA Baseline P | 1441 | -156 |

## Record by version (W-D-L)

| opponent | v21 | v20 | v19 | v18 | v17 | v16 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 |  | 0-0-4 | 0-0-4 |  |
| Knight Vision | 0-0-14 | 0-0-6 |  | 0-0-4 | 0-0-2 |  |
| Decent Chess Bot | 1-1-22 | 0-0-10 |  | 0-1-9 | 0-0-2 |  |
| Strongly Invisible | 0-1-13 | 0-2-10 |  | 0-0-2 |  | 0-0-6 |
| **duck** | 0-2-6 | 4-1-11 |  | 0-0-4 | 1-0-1 | 0-0-2 |
| **Instructors** | 2-1-9 | 2-0-8 |  | 3-0-5 | 1-0-3 | 0-0-2 |
| TA Baseline P | 24-5-3 | 15-0-3 | 2-0-0 | 9-0-3 | 3-1-2 | 1-1-2 |
| TA Baseline A | 13-3-12 | 11-3-12 |  | 7-2-5 | 2-0-2 | 2-0-2 |
| TA Baseline S | 7-3-6 | 5-4-7 |  | 3-1-12 | 2-1-5 | 1-0-1 |

## Skill gaps (rates per 100 moves unless noted)

Active version v20+21. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.2 | 34.5 | 30.2 | 36.3 | 33.6 | 31.9 | 32.5 |
|  | vision-gaining moves | 20.9 | 18.7 | 18.6 | 21.4 | 21.8 | 19.9 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.32 ⚠ | 0.48 | 0.29 ⚠ | 0.46 | 0.40 | 0.40 | 0.40 |
|  | captures from unseen squares | 6.8 ⚠ | 11.0 | 5.3 ⚠ | 10.7 | 10.0 | 9.4 | 8.0 |
|  | captures after a route the other side never saw | 13.7 | 15.8 | 12.2 ⚠ | 16.4 | 18.3 | 15.7 | 14.6 |
|  | long slider strikes | 3.7 ⚠ | 4.9 | 3.3 ⚠ | 5.9 | 4.2 ⚠ | 6.2 | 4.2 |
| King pressure | moves that attack the enemy king | 2.3 ⚠ | 3.5 | 1.3 ⚠ | 5.5 | 2.4 ⚠ | 4.5 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.9 | 1.6 | 0.3 ⚠ | 2.4 | 1.6 | 1.3 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.5 | 0.0 | 0.5 | 0.1 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.3 | 4.8 | 0.5 | 5.1 | 1.8 | 2.5 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.5 | 1.7 | 3.2 ⚠ | 0.7 | 2.1 | 3.2 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 2.0 | 3.7 ⚠ | 2.7 | 2.2 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.4 | 0.1 | 0.2 | 0.1 | 0.1 | 0.3 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 3.4 | 6.2 | 2.9 | 4.5 | 1.9 | 8.7 | 4.8 |
| King handling | king moves | 11.8 | 10.9 | 16.3 | 8.0 | 11.6 | 12.4 | 16.1 |
|  | king moves beyond the second rank | 0.7 | 3.7 | 1.9 | 2.0 | 3.0 | 2.2 | 4.9 |
|  | castling | 2.0 | 2.1 | 2.0 | 2.0 | 2.1 | 2.2 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v20+21 against the top six

Record 9-8-113; 113 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 57 | 15 |
| king walked into an unseen attacker after taking the bait (king capture) | 26 | 10 |
| king already attacked by an unseen piece | 12 | 4 |
| our move opened a line from an unseen attacker | 8 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 1 |
| king left to an attacker we could see (no safe move existed) | 5 | 1 |

Pieces that took our king: q 55, r 30, n 12, b 9, p 5, br 1, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 60, late (70+) or never 3 down 36, opening (ply < 30) 17.
- Down 3 or more at some point in 107 of 113 losses; median first ply 51.
- Down 5 or more in 101; median first ply 61.
- Lost although we had led by 3 or more: 11 of 113.
- Our clock at 15 s or less: 27 of 113.
- Median length 89 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 23 |
| capturer unseen when we moved, piece had just moved there (n) | 13 |
| capturer unseen when we moved, piece had just moved there (r) | 11 |
| capturer unseen when we moved, piece had just moved there (b) | 8 |
| capturer unseen when we moved (r) | 7 |
| capturer unseen when we moved (q) | 7 |
| capturer unseen when we moved, piece had just moved there (p) | 6 |
| capturer unseen when we moved (p) | 5 |
| other | 5 |
| capturer unseen when we moved (b) | 5 |
| capturer visible when we moved (q) | 4 |
| capturer unseen when we moved (n) | 4 |
| capturer visible when we moved (b) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer visible when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer visible when we moved (n) | 1 |
| capturer visible when we moved, piece had just moved there (b) | 1 |

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
| 8cevua8y | duck | W | draw | 107 | Threefold repetition |
| xg5iuc9j | Instructors | B | draw | 93 | Threefold repetition |
| y5ficigq | duck | W | draw | 120 | Threefold repetition |
| ws27f3sg | Decent Chess Bot | W | draw | 81 | Threefold repetition |
| 3wf7byum | Strongly Invisible | B | draw | 60 | Threefold repetition |
| s09udc3w | Decent Chess Bot | W | win | 76 | King capturable |
