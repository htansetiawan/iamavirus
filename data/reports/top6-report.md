# Against the top six

Updated 2026-10-12 01:23 UTC; leaderboard fetched 2026-10-12T01:23. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2161 | +370 |
| Knight Vision | 2121 | +330 |
| Decent Chess Bot | 2044 | +254 |
| Strongly Invisible | 2053 | +262 |
| **duck** | 1939 | +148 |
| **Instructors** | 1935 | +144 |
| TA Baseline S | 1628 | -163 |
| **IAmAVirus** | 1791 |  |
| TA Baseline A | 1539 | -251 |
| TA Baseline P | 1403 | -388 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-2 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 0-0-4 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 3-0-5 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 1-1-6 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 4-0-6 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 0-0-4 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 4-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 4-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 7-0-1 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.9 | 34.7 | 32.3 | 35.7 | 35.1 | 29.7 | 32.7 |
|  | vision-gaining moves | 20.9 | 22.5 | 18.9 | 22.5 | 23.5 | 17.1 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.41 | 0.44 | 0.37 | 0.50 | 0.34 | 0.40 |
|  | captures from unseen squares | 10.0 | 10.8 | 9.9 | 11.0 | 13.4 | 8.2 | 8.3 |
|  | captures after a route the other side never saw | 15.5 | 18.2 | 16.8 ⚠ | 21.3 | 19.0 | 16.4 | 15.0 |
|  | long slider strikes | 5.9 | 4.6 | 5.1 | 6.4 | 5.6 | 5.0 | 4.4 |
| King pressure | moves that attack the enemy king | 5.0 | 4.1 | 4.9 | 5.2 | 5.5 | 3.7 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.6 | 1.7 | 1.8 ⚠ | 3.1 | 2.6 | 0.9 | 1.6 |
|  | sacrifices that lead to a king capture | 0.2 | 0.7 | 0.4 | 0.4 | 0.9 | 0.4 | 0.2 |
| Queen activity | queen moves into the enemy half | 4.6 | 4.1 | 3.4 | 4.3 | 3.6 | 1.5 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.3 ⚠ | 2.2 | 6.0 ⚠ | 1.5 | 1.3 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 3.5 | 2.9 | 2.7 | 1.9 | 3.0 | 2.9 |
|  | queen left attacked by an unseen piece | 0.6 | 0.0 | 0.5 | 0.0 | 0.6 | 0.2 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 10.5 ⚠ | 4.3 | 11.4 ⚠ | 2.2 | 3.0 | 6.5 | 5.3 |
| King handling | king moves | 17.7 | 9.1 | 14.5 | 10.2 | 8.7 | 23.8 | 15.8 |
|  | king moves beyond the second rank | 1.1 | 1.7 | 3.1 | 1.7 | 2.3 | 7.6 | 5.0 |
|  | castling | 2.2 | 2.2 | 2.7 | 2.2 | 2.1 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 8-1-27; 27 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 11 | 4 |
| king already attacked by an unseen piece | 7 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 5 | 3 |
| king already attacked by an unseen piece (no safe move existed) | 4 | 2 |

Pieces that took our king: r 11, q 10, n 3, b 2, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 14, opening (ply < 30) 10, late (70+) or never 3 down 3.
- Down 3 or more at some point in 25 of 27 losses; median first ply 37.
- Down 5 or more in 24; median first ply 42.5.
- Lost although we had led by 3 or more: 1 of 27.
- Our clock at 15 s or less: 0 of 27.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 9 |
| capturer unseen when we moved, piece had just moved there (r) | 5 |
| capturer unseen when we moved, piece had just moved there (n) | 4 |
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
| aextvnui | Strongly Invisible | W | draw | 105 | Threefold repetition |
