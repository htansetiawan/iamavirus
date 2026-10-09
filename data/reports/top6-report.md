# Against the top six

Updated 2026-10-09 18:46 UTC; leaderboard fetched 2026-10-09T18:45. Active version: v20+21. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2177 | +510 |
| Knight Vision | 2133 | +466 |
| Decent Chess Bot | 2069 | +402 |
| Strongly Invisible | 2066 | +399 |
| **duck** | 1984 | +317 |
| **Instructors** | 1931 | +264 |
| TA Baseline S | 1684 | +18 |
| **IAmAVirus** | 1667 |  |
| TA Baseline A | 1557 | -110 |
| TA Baseline P | 1453 | -214 |

## Record by version (W-D-L)

| opponent | v21 | v20 | v19 | v18 | v17 | v16 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 |  | 0-0-4 | 0-0-4 |  |
| Knight Vision | 0-0-14 | 0-0-6 |  | 0-0-4 | 0-0-2 |  |
| Decent Chess Bot | 1-1-18 | 0-0-10 |  | 0-1-9 | 0-0-2 |  |
| Strongly Invisible | 0-1-7 | 0-2-10 |  | 0-0-2 |  | 0-0-6 |
| **duck** | 0-2-6 | 4-1-11 |  | 0-0-4 | 1-0-1 | 0-0-2 |
| **Instructors** | 2-1-7 | 2-0-8 |  | 3-0-5 | 1-0-3 | 0-0-2 |
| TA Baseline P | 20-5-1 | 15-0-3 | 2-0-0 | 9-0-3 | 3-1-2 | 1-1-2 |
| TA Baseline A | 10-3-4 | 11-3-12 |  | 7-2-5 | 2-0-2 | 2-0-2 |
| TA Baseline S | 6-3-3 | 5-4-7 |  | 3-1-12 | 2-1-5 | 1-0-1 |

## Skill gaps (rates per 100 moves unless noted)

Active version v20+21. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.5 | 34.5 | 30.0 | 36.2 | 33.6 | 31.6 | 32.5 |
|  | vision-gaining moves | 21.1 | 18.9 | 18.7 | 21.3 | 21.6 | 19.6 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.32 ⚠ | 0.48 | 0.29 ⚠ | 0.45 | 0.40 | 0.41 | 0.40 |
|  | captures from unseen squares | 6.9 ⚠ | 10.9 | 5.3 ⚠ | 10.7 | 10.0 | 9.3 | 8.0 |
|  | captures after a route the other side never saw | 14.0 | 15.8 | 12.1 ⚠ | 16.4 | 18.4 | 15.5 | 14.6 |
|  | long slider strikes | 3.8 ⚠ | 5.0 | 3.3 ⚠ | 5.8 | 4.1 ⚠ | 6.0 | 4.2 |
| King pressure | moves that attack the enemy king | 2.2 ⚠ | 3.5 | 1.2 ⚠ | 5.4 | 2.5 ⚠ | 4.2 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.9 | 1.6 | 0.3 ⚠ | 2.3 | 1.7 | 1.2 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.5 | 0.0 | 0.4 | 0.1 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.3 | 4.9 | 0.5 | 4.9 | 1.8 | 2.5 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.3 | 1.8 | 3.0 ⚠ | 0.6 | 1.7 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 2.1 | 3.7 ⚠ | 2.6 | 2.0 | 3.1 | 2.9 |
|  | queen left attacked by an unseen piece | 0.3 | 0.2 | 0.2 | 0.1 | 0.1 | 0.3 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 3.3 | 6.5 | 2.6 | 4.7 | 1.2 | 8.2 | 4.8 |
| King handling | king moves | 11.8 | 10.8 | 16.3 | 8.2 | 10.8 | 13.2 | 16.1 |
|  | king moves beyond the second rank | 0.7 | 3.6 | 1.7 | 2.2 | 2.7 | 2.5 | 4.9 |
|  | castling | 2.1 | 2.1 | 2.0 | 2.0 | 2.1 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v20+21 against the top six

Record 9-8-101; 101 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 51 | 14 |
| king walked into an unseen attacker after taking the bait (king capture) | 22 | 10 |
| king already attacked by an unseen piece | 11 | 3 |
| our move opened a line from an unseen attacker | 8 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 5 | 1 |
| king left to an attacker we could see (no safe move existed) | 4 | 1 |

Pieces that took our king: q 49, r 27, n 11, b 9, p 3, br 1, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 52, late (70+) or never 3 down 33, opening (ply < 30) 16.
- Down 3 or more at some point in 95 of 101 losses; median first ply 51.
- Down 5 or more in 89; median first ply 61.
- Lost although we had led by 3 or more: 10 of 101.
- Our clock at 15 s or less: 24 of 101.
- Median length 87 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 20 |
| capturer unseen when we moved, piece had just moved there (n) | 13 |
| capturer unseen when we moved, piece had just moved there (r) | 10 |
| capturer unseen when we moved, piece had just moved there (b) | 8 |
| capturer unseen when we moved (q) | 7 |
| capturer unseen when we moved (r) | 6 |
| capturer unseen when we moved (p) | 5 |
| other | 5 |
| capturer visible when we moved (q) | 4 |
| capturer unseen when we moved (n) | 4 |
| capturer unseen when we moved (b) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer visible when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved (b) | 1 |
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
