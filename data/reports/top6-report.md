# Against the top six

Updated 2026-10-09 22:33 UTC; leaderboard fetched 2026-10-09T22:32. Active version: v21. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2197 | +612 |
| Knight Vision | 2138 | +552 |
| Decent Chess Bot | 2099 | +514 |
| Strongly Invisible | 2053 | +467 |
| **duck** | 1928 | +342 |
| **Instructors** | 1937 | +352 |
| TA Baseline S | 1643 | +57 |
| **IAmAVirus** | 1585 |  |
| TA Baseline A | 1553 | -33 |
| TA Baseline P | 1432 | -153 |

## Record by version (W-D-L)

| opponent | v21 | v20 | v19 | v18 | v17 | v16 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 |  | 0-0-4 | 0-0-4 |  |
| Knight Vision | 0-0-16 | 0-0-6 |  | 0-0-4 | 0-0-2 |  |
| Decent Chess Bot | 1-1-26 | 0-0-10 |  | 0-1-9 | 0-0-2 |  |
| Strongly Invisible | 0-1-13 | 0-2-10 |  | 0-0-2 |  | 0-0-6 |
| **duck** | 0-2-6 | 4-1-11 |  | 0-0-4 | 1-0-1 | 0-0-2 |
| **Instructors** | 3-1-10 | 2-0-8 |  | 3-0-5 | 1-0-3 | 0-0-2 |
| TA Baseline P | 29-5-8 | 15-0-3 | 2-0-0 | 9-0-3 | 3-1-2 | 1-1-2 |
| TA Baseline A | 14-5-13 | 11-3-12 |  | 7-2-5 | 2-0-2 | 2-0-2 |
| TA Baseline S | 11-4-9 | 5-4-7 |  | 3-1-12 | 2-1-5 | 1-0-1 |

## Skill gaps (rates per 100 moves unless noted)

Active version v21. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 30.7 | 34.5 | 30.0 | 36.6 | 34.2 | 32.2 | 32.5 |
|  | vision-gaining moves | 22.5 | 18.4 | 18.8 | 21.0 | 21.7 | 19.8 | 18.8 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.32 ⚠ | 0.50 | 0.31 ⚠ | 0.47 | 0.39 | 0.42 | 0.40 |
|  | captures from unseen squares | 6.5 ⚠ | 11.6 | 5.6 ⚠ | 11.1 | 9.9 | 10.1 | 8.0 |
|  | captures after a route the other side never saw | 13.6 | 16.2 | 12.1 ⚠ | 16.7 | 18.4 | 16.6 | 14.6 |
|  | long slider strikes | 3.4 ⚠ | 5.3 | 3.3 ⚠ | 5.8 | 4.4 ⚠ | 6.4 | 4.2 |
| King pressure | moves that attack the enemy king | 2.1 ⚠ | 4.2 | 1.3 ⚠ | 5.3 | 2.5 ⚠ | 4.4 | 3.3 |
|  | ...with an attacker the king's side cannot see | 0.4 ⚠ | 2.2 | 0.3 ⚠ | 2.8 | 1.9 | 1.4 | 1.5 |
|  | sacrifices that lead to a king capture | 0.0 | 0.2 | 0.0 | 0.6 | 0.1 | 0.3 | 0.2 |
| Queen activity | queen moves into the enemy half | 1.0 | 4.4 | 0.6 | 5.6 | 1.9 | 2.9 | 2.9 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.7 ⚠ | 1.2 | 3.5 ⚠ | 0.8 | 2.3 | 3.2 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 ⚠ | 2.1 | 4.1 ⚠ | 2.5 | 2.4 | 3.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.6 | 0.2 | 0.3 | 0.0 | 0.2 | 0.3 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 3.9 | 7.2 | 3.1 | 3.8 | 2.3 | 8.4 | 4.8 |
| King handling | king moves | 13.0 | 9.8 | 16.4 | 8.1 | 10.8 | 12.3 | 16.1 |
|  | king moves beyond the second rank | 1.1 | 2.8 | 1.8 | 2.4 | 2.6 | 2.2 | 4.9 |
|  | castling | 1.8 | 2.0 | 2.0 | 1.9 | 2.2 | 2.2 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v21 against the top six

Record 4-5-73; 73 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 38 | 10 |
| king walked into an unseen attacker after taking the bait (king capture) | 15 | 2 |
| king already attacked by an unseen piece | 7 | 2 |
| king left to an attacker we could see (no safe move existed) | 5 | 1 |
| our move opened a line from an unseen attacker | 5 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 3 | 0 |

Pieces that took our king: q 42, r 14, b 6, n 5, p 5, br 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 36, late (70+) or never 3 down 22, opening (ply < 30) 15.
- Down 3 or more at some point in 71 of 73 losses; median first ply 49.
- Down 5 or more in 70; median first ply 59.5.
- Lost although we had led by 3 or more: 5 of 73.
- Our clock at 15 s or less: 18 of 73.
- Median length 89 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 16 |
| capturer unseen when we moved, piece had just moved there (n) | 8 |
| capturer unseen when we moved, piece had just moved there (b) | 6 |
| capturer unseen when we moved, piece had just moved there (r) | 6 |
| capturer unseen when we moved (r) | 5 |
| capturer unseen when we moved (b) | 5 |
| capturer unseen when we moved (n) | 4 |
| other | 4 |
| capturer unseen when we moved (q) | 4 |
| capturer unseen when we moved, piece had just moved there (p) | 4 |
| capturer visible when we moved (b) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer visible when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved, piece had just moved there (b) | 1 |

## What worked: v21's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| o7syjm26 | Instructors | B | win | 81 | King capturable |
| cugdggr0 | Instructors | W | win | 82 | King capturable |
| 8cevua8y | duck | W | draw | 107 | Threefold repetition |
| xg5iuc9j | Instructors | B | draw | 93 | Threefold repetition |
| y5ficigq | duck | W | draw | 120 | Threefold repetition |
| ws27f3sg | Decent Chess Bot | W | draw | 81 | Threefold repetition |
| 3wf7byum | Strongly Invisible | B | draw | 60 | Threefold repetition |
| s09udc3w | Decent Chess Bot | W | win | 76 | King capturable |
| 24581iwu | Instructors | W | win | 76 | King capturable |
