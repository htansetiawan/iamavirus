# Against the top six

Updated 2026-10-14 09:15 UTC; leaderboard fetched 2026-10-14T09:15. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2216 | +372 |
| Knight Vision | 2132 | +288 |
| Decent Chess Bot | 2037 | +193 |
| Strongly Invisible | 2097 | +253 |
| **duck** | 1988 | +144 |
| **Instructors** | 1899 | +54 |
| TA Baseline S | 1657 | -187 |
| **IAmAVirus** | 1844 |  |
| TA Baseline A | 1526 | -318 |
| TA Baseline P | 1452 | -392 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision |  | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 1-0-1 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 1-0-5 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 3-0-5 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 4-0-0 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.1 | 34.7 | 33.7 | 33.7 | 37.2 | 32.1 | 33.1 |
|  | vision-gaining moves | 23.2 | 22.4 | 21.0 | 24.7 | 21.0 | 18.5 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.37 ⚠ | 0.49 | 0.44 | 0.37 | 0.45 | 0.40 | 0.41 |
|  | captures from unseen squares | 8.3 ⚠ | 12.2 | 9.6 | 8.4 | 11.0 | 8.9 | 8.5 |
|  | captures after a route the other side never saw | 15.2 | 17.0 | 15.6 | 16.3 | 18.5 | 13.8 | 14.9 |
|  | long slider strikes | 4.6 ⚠ | 6.7 | 6.6 | 3.6 | 4.8 | 4.7 | 4.3 |
| King pressure | moves that attack the enemy king | 3.4 ⚠ | 4.8 | 4.2 | 3.6 | 5.2 | 2.0 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.7 ⚠ | 2.7 | 1.2 | 1.2 | 3.5 | 0.5 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.0 | 0.0 | 0.6 | 0.8 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.7 | 2.7 | 3.6 | 1.8 | 4.0 | 0.7 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.2 ⚠ | 0.9 | 3.0 ⚠ | 1.2 | 1.0 | 2.5 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 1.9 | 2.6 | 3.0 | 4.8 | 2.0 | 4.2 | 3.1 |
|  | queen left attacked by an unseen piece | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.7 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 4.6 | 4.1 | 1.8 | 1.8 | 4.2 | 4.0 | 5.7 |
| King handling | king moves | 13.3 | 11.0 | 7.8 | 10.8 | 6.0 | 11.9 | 15.2 |
|  | king moves beyond the second rank | 3.7 | 2.4 | 1.8 | 3.0 | 1.0 | 1.7 | 4.4 |
|  | castling | 1.7 | 2.4 | 2.4 | 1.8 | 2.0 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 5-0-13; 13 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 9 | 9 |
| king already attacked by an unseen piece | 2 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 1 | 0 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |

Pieces that took our king: r 8, q 3, k 1, p 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 7, opening (ply < 30) 5, late (70+) or never 3 down 1.
- Down 3 or more at some point in 12 of 13 losses; median first ply 32.0.
- Down 5 or more in 11; median first ply 56.
- Lost although we had led by 3 or more: 0 of 13.
- Our clock at 15 s or less: 0 of 13.
- Median length 76 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 3 |
| capturer unseen when we moved, piece had just moved there (r) | 3 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved (r) | 1 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |

## What worked: v35's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| ol5e72pm | duck | B | win | 97 | King capturable |
| 61bzys3l | Instructors | W | win | 98 | King capturable |
| c5cnjewf | Strongly Invisible | W | win | 124 | King capturable |
| h2u89knk | Instructors | B | win | 113 | King capturable |
| gt1mghiq | Instructors | W | win | 80 | King capturable |
