# Against the top six

Updated 2026-10-14 09:57 UTC; leaderboard fetched 2026-10-14T09:56. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2221 | +375 |
| Knight Vision | 2138 | +292 |
| Decent Chess Bot | 2048 | +202 |
| Strongly Invisible | 2095 | +249 |
| **duck** | 1974 | +128 |
| **Instructors** | 1918 | +72 |
| TA Baseline S | 1646 | -200 |
| **IAmAVirus** | 1846 |  |
| TA Baseline A | 1512 | -334 |
| TA Baseline P | 1452 | -393 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 0-0-2 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot |  | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 2-0-4 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 1-0-5 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 3-0-7 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P |  | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 6-0-0 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 7-0-0 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.2 | 35.5 | 31.5 | 33.6 | 36.5 | 31.8 | 33.1 |
|  | vision-gaining moves | 23.0 | 23.0 | 20.8 | 22.2 | 22.9 | 17.3 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.39 | 0.48 | 0.41 | 0.43 | 0.45 | 0.42 | 0.41 |
|  | captures from unseen squares | 8.7 ⚠ | 12.4 | 8.9 | 10.5 | 11.2 | 9.6 | 8.5 |
|  | captures after a route the other side never saw | 15.5 | 17.5 | 15.2 | 17.4 | 18.5 | 14.5 | 14.9 |
|  | long slider strikes | 4.5 ⚠ | 6.5 | 5.0 | 4.6 | 4.7 | 5.3 | 4.3 |
| King pressure | moves that attack the enemy king | 3.0 ⚠ | 5.6 | 2.8 | 3.3 | 5.0 | 2.2 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.5 ⚠ | 3.3 | 0.4 ⚠ | 1.7 | 3.2 | 0.6 | 1.6 |
|  | sacrifices that lead to a king capture | 0.0 | 0.2 | 0.0 | 0.2 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.7 | 3.8 | 1.5 | 3.5 | 3.4 | 1.3 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.6 ⚠ | 0.9 | 2.4 ⚠ | 0.7 | 1.1 | 2.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.1 | 2.3 | 3.9 | 3.3 | 1.7 | 3.5 | 3.1 |
|  | queen left attacked by an unseen piece | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.6 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 4.2 | 3.6 | 11.0 ⚠ | 7.6 | 3.4 | 5.2 | 5.7 |
| King handling | king moves | 13.4 | 10.0 | 13.6 | 13.5 | 7.3 | 12.2 | 15.2 |
|  | king moves beyond the second rank | 3.6 | 2.1 | 4.3 | 6.1 | 1.9 | 2.9 | 4.4 |
|  | castling | 1.8 | 2.4 | 2.2 | 2.0 | 1.7 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 6-0-20; 20 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 13 | 10 |
| king walked into an unseen attacker after taking the bait (king capture) | 4 | 1 |
| king already attacked by an unseen piece | 2 | 1 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |

Pieces that took our king: r 12, q 5, k 2, p 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 12, opening (ply < 30) 6, late (70+) or never 3 down 2.
- Down 3 or more at some point in 18 of 20 losses; median first ply 36.5.
- Down 5 or more in 16; median first ply 47.5.
- Lost although we had led by 3 or more: 1 of 20.
- Our clock at 15 s or less: 0 of 20.
- Median length 81.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 5 |
| capturer unseen when we moved, piece had just moved there (r) | 4 |
| capturer unseen when we moved, piece had just moved there (b) | 3 |
| capturer unseen when we moved (r) | 2 |
| capturer unseen when we moved (q) | 1 |
| capturer unseen when we moved (b) | 1 |
| capturer unseen when we moved, piece had just moved there (n) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |

## What worked: v35's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| ol5e72pm | duck | B | win | 97 | King capturable |
| 61bzys3l | Instructors | W | win | 98 | King capturable |
| c5cnjewf | Strongly Invisible | W | win | 124 | King capturable |
| h2u89knk | Instructors | B | win | 113 | King capturable |
| gt1mghiq | Instructors | W | win | 80 | King capturable |
| tlaqq2oz | Strongly Invisible | W | win | 120 | King capturable |
