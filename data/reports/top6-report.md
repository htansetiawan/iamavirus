# Against the top six

Updated 2026-10-12 01:03 UTC; leaderboard fetched 2026-10-12T01:02. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2166 | +383 |
| Knight Vision | 2105 | +322 |
| Decent Chess Bot | 2038 | +254 |
| Strongly Invisible | 2064 | +281 |
| **duck** | 1958 | +175 |
| **Instructors** | 1928 | +145 |
| TA Baseline S | 1622 | -161 |
| **IAmAVirus** | 1783 |  |
| TA Baseline A | 1553 | -231 |
| TA Baseline P | 1408 | -375 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-4 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 3-0-5 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-0-5 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 4-0-6 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-4 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 4-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 2-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 7-0-1 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.9 | 34.7 | 32.6 | 36.0 | 34.5 | 29.5 | 32.7 |
|  | vision-gaining moves | 20.9 | 22.5 | 19.1 | 22.4 | 24.3 | 17.0 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.41 | 0.45 | 0.37 | 0.47 | 0.36 | 0.40 |
|  | captures from unseen squares | 10.0 | 10.8 | 10.2 | 11.4 | 12.0 | 8.7 | 8.3 |
|  | captures after a route the other side never saw | 15.5 | 18.2 | 17.5 | 21.9 | 18.3 | 16.1 | 15.0 |
|  | long slider strikes | 5.9 | 4.6 | 5.1 | 6.1 | 4.7 | 4.9 | 4.4 |
| King pressure | moves that attack the enemy king | 5.0 | 4.1 | 5.0 | 5.4 | 5.8 | 3.2 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.6 | 1.7 | 1.9 ⚠ | 3.3 | 2.8 | 0.6 | 1.6 |
|  | sacrifices that lead to a king capture | 0.2 | 0.7 | 0.4 | 0.3 | 0.9 | 0.4 | 0.2 |
| Queen activity | queen moves into the enemy half | 4.6 | 4.1 | 3.6 | 4.7 | 3.4 | 1.5 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.3 ⚠ | 2.2 | 6.5 ⚠ | 1.5 | 1.3 | 2.8 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 3.5 | 3.3 | 2.5 | 1.9 | 2.5 | 2.9 |
|  | queen left attacked by an unseen piece | 0.6 | 0.0 | 0.4 | 0.0 | 0.6 | 0.0 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 10.5 ⚠ | 4.3 | 10.4 ⚠ | 2.1 | 2.6 | 6.2 | 5.3 |
| King handling | king moves | 17.7 | 9.1 | 14.1 | 9.6 | 9.0 | 26.1 | 15.8 |
|  | king moves beyond the second rank | 1.1 | 1.7 | 3.0 | 1.8 | 2.6 | 8.7 | 5.0 |
|  | castling | 2.2 | 2.2 | 2.8 | 2.2 | 1.9 | 1.9 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 8-0-26; 26 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 11 | 4 |
| king already attacked by an unseen piece | 6 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 5 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 4 | 2 |

Pieces that took our king: r 11, q 9, n 3, b 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 14, opening (ply < 30) 9, late (70+) or never 3 down 3.
- Down 3 or more at some point in 24 of 26 losses; median first ply 38.0.
- Down 5 or more in 23; median first ply 41.
- Lost although we had led by 3 or more: 1 of 26.
- Our clock at 15 s or less: 0 of 26.
- Median length 77.0 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 9 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved, piece had just moved there (n) | 3 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved, piece had just moved there (b) | 2 |
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
