# Against the top six

Updated 2026-10-12 02:04 UTC; leaderboard fetched 2026-10-12T02:04. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2150 | +340 |
| Knight Vision | 2125 | +315 |
| Decent Chess Bot | 2043 | +233 |
| Strongly Invisible | 2051 | +241 |
| **duck** | 1950 | +139 |
| **Instructors** | 1940 | +130 |
| TA Baseline S | 1632 | -178 |
| **IAmAVirus** | 1810 |  |
| TA Baseline A | 1533 | -277 |
| TA Baseline P | 1411 | -400 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-5 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 1-0-5 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 3-0-8 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 3-1-6 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 6-0-10 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 1-0-5 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 4-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 6-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 7-0-1 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.1 | 33.3 | 32.3 | 35.4 | 35.6 | 30.3 | 32.7 |
|  | vision-gaining moves | 20.2 | 20.7 | 18.7 | 22.4 | 23.1 | 17.3 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.41 | 0.43 | 0.39 | 0.51 | 0.34 | 0.40 |
|  | captures from unseen squares | 9.9 | 10.5 | 9.6 | 11.2 | 13.6 | 8.0 | 8.3 |
|  | captures after a route the other side never saw | 15.0 | 18.3 | 16.0 ⚠ | 20.4 | 19.2 | 16.2 | 15.0 |
|  | long slider strikes | 5.2 | 5.3 | 5.3 | 5.9 | 5.6 | 4.9 | 4.4 |
| King pressure | moves that attack the enemy king | 4.6 | 3.4 | 4.7 | 4.4 | 5.5 | 3.3 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.4 | 1.4 | 1.6 ⚠ | 2.7 | 2.6 | 0.8 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.6 | 0.2 | 0.2 | 1.0 | 0.3 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.4 | 4.2 | 3.3 | 4.5 | 3.3 | 1.5 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.6 ⚠ | 1.9 | 5.3 ⚠ | 1.2 | 1.5 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.1 | 2.9 | 3.0 | 2.8 | 1.7 | 3.4 | 2.9 |
|  | queen left attacked by an unseen piece | 0.3 | 0.3 | 0.4 | 0.1 | 0.5 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 8.8 ⚠ | 4.0 | 9.3 ⚠ | 1.7 | 2.6 | 5.9 | 5.3 |
| King handling | king moves | 14.5 | 15.2 | 15.7 | 10.0 | 8.3 | 22.2 | 15.8 |
|  | king moves beyond the second rank | 1.4 | 7.1 | 4.4 | 2.1 | 2.0 | 6.9 | 5.0 |
|  | castling | 2.1 | 2.0 | 2.5 | 2.2 | 2.1 | 2.1 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 14-1-39; 39 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 19 | 7 |
| king already attacked by an unseen piece | 8 | 1 |
| king already attacked by an unseen piece (no safe move existed) | 6 | 3 |
| king walked into an unseen attacker after taking the bait (king capture) | 6 | 4 |

Pieces that took our king: r 15, q 15, n 4, b 2, p 1, qr 1, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 22, opening (ply < 30) 14, late (70+) or never 3 down 3.
- Down 3 or more at some point in 37 of 39 losses; median first ply 37.
- Down 5 or more in 36; median first ply 43.5.
- Lost although we had led by 3 or more: 2 of 39.
- Our clock at 15 s or less: 0 of 39.
- Median length 78 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 12 |
| capturer unseen when we moved, piece had just moved there (r) | 7 |
| capturer unseen when we moved, piece had just moved there (n) | 6 |
| capturer unseen when we moved, piece had just moved there (b) | 4 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved (r) | 1 |
| other | 1 |
| capturer visible when we moved (q) | 1 |
| capturer unseen when we moved (q) | 1 |

## What worked: v33's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| adf9mah0 | Strongly Invisible | W | win | 40 | King capturable |
| z34nungm | Decent Chess Bot | B | win | 31 | King capturable |
| 43dabbw9 | Decent Chess Bot | W | win | 70 | King capturable |
| zu9sjnr6 | duck | W | win | 84 | King capturable |
| drnnxb3e | Decent Chess Bot | W | win | 86 | King capturable |
| vf7pjwhn | duck | W | win | 40 | King capturable |
| q9q9m0xi | duck | B | win | 105 | King capturable |
| feab7fld | duck | W | win | 96 | King capturable |
| aextvnui | Strongly Invisible | W | draw | 105 | Threefold repetition |
| ycvp17p2 | duck | B | win | 101 | King capturable |
| d7s2f6wk | duck | W | win | 178 | King capturable |
| bsau1i07 | Knight Vision | W | win | 68 | King capturable |
| 0q9me0sb | Instructors | B | win | 93 | King capturable |
| 8hp9vs48 | Strongly Invisible | W | win | 48 | King capturable |
| 01an1kft | Strongly Invisible | B | win | 105 | King capturable |
