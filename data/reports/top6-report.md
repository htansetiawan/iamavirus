# Against the top six

Updated 2026-10-12 10:04 UTC; leaderboard fetched 2026-10-12T10:04. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2119 | +289 |
| Knight Vision | 2108 | +277 |
| Decent Chess Bot | 2048 | +218 |
| Strongly Invisible | 2071 | +241 |
| **duck** | 1994 | +163 |
| **Instructors** | 1927 | +97 |
| TA Baseline S | 1668 | -163 |
| **IAmAVirus** | 1831 |  |
| TA Baseline A | 1516 | -315 |
| TA Baseline P | 1438 | -392 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 3-0-19 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 9-0-27 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 7-0-27 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 5-1-18 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 9-1-20 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 4-0-16 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 14-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 28-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 16-0-4 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.5 | 34.2 | 32.2 | 36.0 | 36.1 | 31.2 | 32.7 |
|  | vision-gaining moves | 19.1 | 21.5 | 19.7 | 23.5 | 21.9 | 18.4 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.41 | 0.45 | 0.41 | 0.54 | 0.34 | 0.40 |
|  | captures from unseen squares | 10.0 | 10.2 | 10.1 | 11.7 | 14.3 | 8.3 | 8.3 |
|  | captures after a route the other side never saw | 15.1 | 17.2 | 16.3 | 20.2 | 19.7 | 15.3 | 15.0 |
|  | long slider strikes | 5.3 | 5.4 | 5.1 | 5.8 | 6.0 | 5.3 | 4.4 |
| King pressure | moves that attack the enemy king | 4.0 | 4.7 | 4.1 ⚠ | 5.3 | 5.0 | 3.2 | 3.6 |
|  | ...with an attacker the king's side cannot see | 1.8 | 2.4 | 1.5 ⚠ | 3.2 | 2.8 | 0.8 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.2 | 0.4 | 0.5 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.8 | 5.1 | 3.1 | 5.5 | 5.2 | 1.8 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.9 ⚠ | 1.5 | 4.8 ⚠ | 1.7 | 1.4 | 3.5 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.1 | 3.2 | 3.7 ⚠ | 2.5 | 1.7 | 4.3 | 2.9 |
|  | queen left attacked by an unseen piece | 0.4 | 0.2 | 0.4 | 0.3 | 0.2 | 0.6 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 9.3 ⚠ | 4.4 | 9.8 ⚠ | 2.8 | 4.3 | 6.9 | 5.3 |
| King handling | king moves | 16.3 | 12.3 | 16.2 | 9.2 | 8.3 | 16.0 | 15.8 |
|  | king moves beyond the second rank | 2.9 | 4.0 | 3.5 | 1.5 | 1.5 | 3.8 | 5.0 |
|  | castling | 2.1 | 2.0 | 2.3 | 2.2 | 2.3 | 2.4 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 37-2-127; 127 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 52 | 11 |
| king already attacked by an unseen piece | 31 | 8 |
| king walked into an unseen attacker after taking the bait (king capture) | 19 | 6 |
| king already attacked by an unseen piece (no safe move existed) | 15 | 8 |
| king left to an attacker we could see (no safe move existed) | 7 | 1 |
| our move opened a line from an unseen attacker | 3 | 2 |

Pieces that took our king: r 62, q 50, n 5, b 4, p 2, k 2, nq 1, qr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 66, opening (ply < 30) 45, late (70+) or never 3 down 16.
- Down 3 or more at some point in 120 of 127 losses; median first ply 36.5.
- Down 5 or more in 115; median first ply 42.
- Lost although we had led by 3 or more: 8 of 127.
- Our clock at 15 s or less: 0 of 127.
- Median length 76 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 39 |
| capturer unseen when we moved, piece had just moved there (r) | 27 |
| capturer unseen when we moved, piece had just moved there (n) | 17 |
| capturer unseen when we moved (q) | 10 |
| capturer unseen when we moved, piece had just moved there (b) | 10 |
| capturer unseen when we moved (r) | 4 |
| capturer unseen when we moved (b) | 4 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
| capturer unseen when we moved (p) | 1 |
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
| w9qqx1o6 | Instructors | B | win | 119 | King capturable |
| ogi8uqdp | Strongly Invisible | B | win | 145 | King capturable |
| v7ktyiix | Knight Vision | W | win | 52 | King capturable |
| tvvbuxsq | Knight Vision | B | win | 73 | King capturable |
| tlp12p59 | Knight Vision | B | win | 51 | King capturable |
| bhinpotr | Knight Vision | B | win | 63 | King capturable |
| 5czrp3gh | duck | W | win | 46 | King capturable |
| q306dmfl | Greek Gift | B | win | 113 | King capturable |
| tcsvy2wq | Instructors | W | win | 90 | King capturable |
| lt2ti00a | Knight Vision | W | win | 40 | King capturable |
| u1sc59rx | Decent Chess Bot | W | win | 72 | King capturable |
| yrfljayz | Strongly Invisible | W | win | 120 | King capturable |
| k2me7228 | Knight Vision | W | win | 72 | King capturable |
| y525aue6 | Decent Chess Bot | W | win | 112 | King capturable |
| nsolnuo2 | Knight Vision | B | win | 63 | King capturable |
| iu8utd4m | Knight Vision | W | win | 78 | King capturable |
| aia0wnjp | duck | B | win | 39 | King capturable |
| fv8eih1b | duck | W | draw | 139 | Threefold repetition |
| oj97cy55 | Greek Gift | W | win | 80 | King capturable |
| 1wu8gw1v | duck | B | win | 103 | King capturable |
