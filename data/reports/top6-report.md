# Against the top six

Updated 2026-10-12 01:44 UTC; leaderboard fetched 2026-10-12T01:43. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2160 | +363 |
| Knight Vision | 2119 | +321 |
| Decent Chess Bot | 2042 | +244 |
| Strongly Invisible | 2062 | +264 |
| **duck** | 1941 | +144 |
| **Instructors** | 1944 | +146 |
| TA Baseline S | 1628 | -170 |
| **IAmAVirus** | 1798 |  |
| TA Baseline A | 1540 | -258 |
| TA Baseline P | 1409 | -388 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-4 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 3-0-7 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-1-6 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 6-0-8 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-4 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 4-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 6-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 7-0-1 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.4 | 32.7 | 31.6 | 35.0 | 35.6 | 30.3 | 32.7 |
|  | vision-gaining moves | 20.8 | 21.3 | 18.6 | 22.1 | 23.1 | 17.3 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.41 | 0.45 | 0.38 | 0.51 | 0.34 | 0.40 |
|  | captures from unseen squares | 9.5 | 10.1 | 9.9 | 11.1 | 13.6 | 8.0 | 8.3 |
|  | captures after a route the other side never saw | 14.7 | 17.3 | 16.5 ⚠ | 21.0 | 19.2 | 16.2 | 15.0 |
|  | long slider strikes | 5.6 | 4.6 | 5.1 | 6.3 | 5.6 | 4.9 | 4.4 |
| King pressure | moves that attack the enemy king | 4.9 | 4.0 | 4.4 | 4.9 | 5.5 | 3.3 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.4 | 1.5 | 1.7 ⚠ | 2.9 | 2.6 | 0.8 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.7 | 0.3 | 0.3 | 1.0 | 0.3 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.8 | 3.7 | 3.1 | 4.1 | 3.3 | 1.5 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.8 ⚠ | 2.3 | 5.6 ⚠ | 1.4 | 1.5 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 3.1 | 2.8 | 2.8 | 1.7 | 3.4 | 2.9 |
|  | queen left attacked by an unseen piece | 0.4 | 0.1 | 0.4 | 0.0 | 0.5 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 9.6 ⚠ | 4.1 | 10.4 ⚠ | 2.0 | 2.6 | 5.9 | 5.3 |
| King handling | king moves | 15.2 | 16.1 | 16.2 | 10.1 | 8.3 | 22.2 | 15.8 |
|  | king moves beyond the second rank | 1.5 | 7.9 | 4.4 | 2.2 | 2.0 | 6.9 | 5.0 |
|  | castling | 2.0 | 2.0 | 2.5 | 2.2 | 2.1 | 2.1 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 10-1-31; 31 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 14 | 5 |
| king already attacked by an unseen piece | 7 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 6 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 4 | 2 |

Pieces that took our king: r 13, q 10, n 3, b 2, p 1, qr 1, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 17, opening (ply < 30) 11, late (70+) or never 3 down 3.
- Down 3 or more at some point in 29 of 31 losses; median first ply 39.
- Down 5 or more in 28; median first ply 43.5.
- Lost although we had led by 3 or more: 1 of 31.
- Our clock at 15 s or less: 0 of 31.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 10 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved, piece had just moved there (n) | 5 |
| capturer unseen when we moved, piece had just moved there (b) | 4 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (n) | 1 |
| other | 1 |
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
