# Against the top six

Updated 2026-10-12 03:27 UTC; leaderboard fetched 2026-10-12T03:26. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2138 | +304 |
| Knight Vision | 2146 | +312 |
| Decent Chess Bot | 2035 | +201 |
| Strongly Invisible | 2062 | +228 |
| **duck** | 1951 | +117 |
| **Instructors** | 1943 | +109 |
| TA Baseline S | 1648 | -187 |
| **IAmAVirus** | 1834 |  |
| TA Baseline A | 1529 | -305 |
| TA Baseline P | 1428 | -406 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 1-0-9 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 1-0-7 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 5-0-11 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 3-1-6 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 6-0-10 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 2-0-6 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 4-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 11-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 10-0-2 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.3 | 33.4 | 32.5 | 35.5 | 35.6 | 31.2 | 32.7 |
|  | vision-gaining moves | 20.2 | 21.1 | 18.3 | 22.7 | 22.1 | 17.6 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.42 | 0.46 | 0.40 | 0.51 | 0.31 | 0.40 |
|  | captures from unseen squares | 9.8 | 10.6 | 10.4 | 11.4 | 13.0 | 7.4 | 8.3 |
|  | captures after a route the other side never saw | 14.9 | 17.7 | 16.2 | 20.2 | 18.3 | 15.9 | 15.0 |
|  | long slider strikes | 5.2 | 5.1 | 5.6 | 5.8 | 5.9 | 5.5 | 4.4 |
| King pressure | moves that attack the enemy king | 4.6 | 3.5 | 4.1 | 4.3 | 5.5 | 3.4 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.4 | 1.5 | 1.4 ⚠ | 2.5 | 2.6 | 0.9 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.5 | 0.3 | 0.2 | 0.6 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.2 | 4.3 | 2.8 | 5.3 | 4.6 | 2.0 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 4.1 ⚠ | 1.9 | 5.1 ⚠ | 1.3 | 1.4 | 2.7 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 3.4 | 2.8 | 3.1 | 2.1 | 4.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.5 | 0.3 | 0.4 | 0.1 | 0.3 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 8.2 ⚠ | 4.0 | 10.3 ⚠ | 2.6 | 4.2 | 5.8 | 5.3 |
| King handling | king moves | 14.1 | 14.8 | 15.2 | 10.1 | 8.7 | 18.3 | 15.8 |
|  | king moves beyond the second rank | 1.3 | 6.5 | 3.8 | 1.7 | 2.0 | 4.7 | 5.0 |
|  | castling | 2.0 | 1.9 | 2.5 | 2.1 | 2.2 | 2.1 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 18-1-49; 49 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 22 | 7 |
| king already attacked by an unseen piece | 10 | 1 |
| king walked into an unseen attacker after taking the bait (king capture) | 8 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 7 | 4 |
| king left to an attacker we could see (no safe move existed) | 1 | 0 |
| our move opened a line from an unseen attacker | 1 | 0 |

Pieces that took our king: r 20, q 20, n 4, b 2, p 1, qr 1, k 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 27, opening (ply < 30) 18, late (70+) or never 3 down 4.
- Down 3 or more at some point in 47 of 49 losses; median first ply 37.
- Down 5 or more in 45; median first ply 43.
- Lost although we had led by 3 or more: 3 of 49.
- Our clock at 15 s or less: 0 of 49.
- Median length 78 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 16 |
| capturer unseen when we moved, piece had just moved there (r) | 10 |
| capturer unseen when we moved, piece had just moved there (n) | 6 |
| capturer unseen when we moved, piece had just moved there (b) | 4 |
| capturer unseen when we moved (q) | 3 |
| capturer unseen when we moved (r) | 2 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (n) | 2 |
| other | 1 |
| capturer visible when we moved (q) | 1 |

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
| fwvo8f1r | Instructors | W | win | 92 | King capturable |
| fxr67qwn | Greek Gift | W | win | 112 | King capturable |
| 6uar266x | Decent Chess Bot | B | win | 25 | King capturable |
| cnhm1fuv | Decent Chess Bot | W | win | 54 | King capturable |
