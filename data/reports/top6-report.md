# Against the top six

Updated 2026-10-09 14:40 UTC; leaderboard fetched 2026-10-09T14:39. Active version: v20+21. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2191 | +569 |
| Knight Vision | 2138 | +516 |
| Decent Chess Bot | 2110 | +488 |
| Strongly Invisible | 2065 | +443 |
| **duck** | 1933 | +311 |
| **Instructors** | 1889 | +266 |
| TA Baseline S | 1705 | +83 |
| **IAmAVirus** | 1622 |  |
| TA Baseline A | 1582 | -40 |
| TA Baseline P | 1464 | -158 |

## Record by version (W-D-L)

| opponent | v20 | v19 | v18 | v17 | v16 | v15 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 |  | 0-0-4 | 0-0-4 |  | 0-0-10 |
| Knight Vision | 0-0-6 |  | 0-0-4 | 0-0-2 |  | 0-1-31 |
| Decent Chess Bot | 0-0-10 |  | 0-1-9 | 0-0-2 |  | 0-0-34 |
| Strongly Invisible | 0-2-10 |  | 0-0-2 |  | 0-0-6 | 0-0-18 |
| **duck** | 4-1-11 |  | 0-0-4 | 1-0-1 | 0-0-2 | 2-0-44 |
| **Instructors** | 2-0-6 |  | 3-0-5 | 1-0-3 | 0-0-2 | 4-0-40 |
| TA Baseline P | 15-0-3 | 2-0-0 | 9-0-3 | 3-1-2 | 1-1-2 | 61-5-54 |
| TA Baseline A | 11-3-12 |  | 7-2-5 | 2-0-2 | 2-0-2 | 31-2-41 |
| TA Baseline S | 5-3-6 |  | 3-1-12 | 2-1-5 | 1-0-1 | 19-7-44 |

## Skill gaps (rates per 100 moves unless noted)

Active version v20+21. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 31.7 | 34.2 | 30.7 | 36.3 | 32.9 | 31.7 | 32.6 |
|  | vision-gaining moves | 20.0 | 18.8 | 18.9 | 22.6 | 21.4 | 19.6 | 19.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.33 ⚠ | 0.45 | 0.27 ⚠ | 0.43 | 0.42 | 0.38 | 0.40 |
|  | captures from unseen squares | 7.2 ⚠ | 10.2 | 5.3 ⚠ | 10.3 | 10.2 | 8.5 | 8.3 |
|  | captures after a route the other side never saw | 13.6 | 15.3 | 13.1 ⚠ | 17.0 | 18.1 | 14.9 | 14.9 |
|  | long slider strikes | 4.0 | 4.4 | 3.3 ⚠ | 6.3 | 3.9 ⚠ | 6.0 | 4.3 |
| King pressure | moves that attack the enemy king | 2.5 | 2.7 | 1.3 ⚠ | 6.1 | 2.1 ⚠ | 4.2 | 3.4 |
|  | ...with an attacker the king's side cannot see | 1.5 | 0.9 | 0.4 ⚠ | 1.9 | 1.2 | 1.2 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.7 | 0.0 | 0.4 | 0.2 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.6 | 4.8 | 0.4 | 4.4 | 1.4 | 2.4 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.0 | 2.1 | 2.8 ⚠ | 0.5 | 1.8 | 3.0 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.4 ⚠ | 2.2 | 3.5 | 3.0 | 2.0 | 3.4 | 2.9 |
|  | queen left attacked by an unseen piece | 0.3 | 0.1 | 0.1 | 0.2 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 2.9 | 6.3 | 2.2 | 6.0 | 1.5 | 8.4 | 4.8 |
| King handling | king moves | 10.4 | 12.0 | 15.2 | 7.5 | 11.9 | 12.1 | 15.4 |
|  | king moves beyond the second rank | 0.4 | 4.7 | 1.9 | 1.0 | 2.9 | 2.1 | 4.9 |
|  | castling | 2.2 | 2.1 | 2.1 | 2.1 | 2.1 | 2.1 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v20+21 against the top six

Record 6-3-45; 45 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| our king walked into an attack from an unseen piece | 16 | 5 |
| king attacked in plain sight and not saved (no escape existed) | 10 | 5 |
| king already attacked by an unseen piece; no escape existed | 6 | 1 |
| king already attacked by an unseen piece | 6 | 2 |
| king attacked in plain sight and not saved | 4 | 2 |
| our move opened a line to our king (attacker unseen) | 3 | 2 |

Pieces that took our king: q 17, r 16, n 6, b 3, p 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 27, late (70+) or never 3 down 14, opening (ply < 30) 4.
- Down 3 or more at some point in 42 of 45 losses; median first ply 57.5.
- Down 5 or more in 37; median first ply 59.
- Lost although we had led by 3 or more: 7 of 45.
- Our clock at 15 s or less: 10 of 45.
- Median length 86 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 10 |
| capturer unseen when we moved, piece had just moved there (n) | 6 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer visible when we moved (q) | 4 |
| capturer unseen when we moved (q) | 4 |
| capturer unseen when we moved (p) | 3 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
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
