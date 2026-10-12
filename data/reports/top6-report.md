# Against the top six

Updated 2026-10-12 12:51 UTC; leaderboard fetched 2026-10-12T12:51. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2117 | +278 |
| Knight Vision | 2116 | +278 |
| Decent Chess Bot | 2094 | +256 |
| Strongly Invisible | 2056 | +218 |
| **duck** | 1941 | +102 |
| **Instructors** | 1911 | +72 |
| TA Baseline S | 1722 | -116 |
| **IAmAVirus** | 1838 |  |
| TA Baseline A | 1512 | -326 |
| TA Baseline P | 1436 | -402 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 4-0-22 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 11-0-35 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 7-0-31 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 6-1-23 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 11-1-22 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 8-0-20 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 17-0-1 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 32-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 23-0-5 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.0 | 34.1 | 32.0 | 35.9 | 35.9 | 31.3 | 32.3 |
|  | vision-gaining moves | 19.4 | 22.2 | 19.9 | 23.5 | 21.9 | 18.7 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.45 | 0.41 | 0.45 | 0.41 | 0.53 | 0.34 | 0.39 |
|  | captures from unseen squares | 9.9 | 10.2 | 10.1 | 11.7 | 13.9 | 8.1 | 7.7 |
|  | captures after a route the other side never saw | 15.2 | 17.1 | 16.3 | 20.3 | 19.6 | 15.0 | 14.2 |
|  | long slider strikes | 5.3 | 5.4 | 5.2 | 5.7 | 5.8 | 5.2 | 4.1 |
| King pressure | moves that attack the enemy king | 4.3 | 4.7 | 3.9 ⚠ | 5.4 | 4.8 | 3.4 | 3.2 |
|  | ...with an attacker the king's side cannot see | 2.2 | 2.4 | 1.5 ⚠ | 3.2 | 2.7 | 0.8 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.2 | 0.4 | 0.6 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.6 | 4.9 | 3.0 | 5.4 | 4.8 | 1.7 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.6 ⚠ | 1.6 | 4.7 ⚠ | 1.7 | 1.6 | 3.5 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 2.9 | 3.1 | 3.6 ⚠ | 2.3 | 1.6 | 4.3 | 3.0 |
|  | queen left attacked by an unseen piece | 0.4 | 0.2 | 0.4 | 0.3 | 0.2 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 8.2 ⚠ | 4.9 | 9.5 ⚠ | 2.5 | 4.8 | 5.9 | 4.7 |
| King handling | king moves | 15.5 | 13.0 | 16.3 | 9.2 | 8.8 | 15.0 | 16.1 |
|  | king moves beyond the second rank | 2.8 | 3.9 | 3.7 | 1.7 | 1.6 | 3.6 | 5.2 |
|  | castling | 2.1 | 1.9 | 2.3 | 2.2 | 2.2 | 2.3 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 47-2-153; 153 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 62 | 12 |
| king already attacked by an unseen piece | 37 | 10 |
| king walked into an unseen attacker after taking the bait (king capture) | 25 | 7 |
| king already attacked by an unseen piece (no safe move existed) | 16 | 8 |
| king left to an attacker we could see (no safe move existed) | 9 | 2 |
| our move opened a line from an unseen attacker | 4 | 3 |

Pieces that took our king: r 71, q 63, n 7, b 6, p 2, k 2, nq 1, qr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 79, opening (ply < 30) 56, late (70+) or never 3 down 18.
- Down 3 or more at some point in 145 of 153 losses; median first ply 36.
- Down 5 or more in 139; median first ply 42.
- Lost although we had led by 3 or more: 10 of 153.
- Our clock at 15 s or less: 0 of 153.
- Median length 74 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 46 |
| capturer unseen when we moved, piece had just moved there (r) | 29 |
| capturer unseen when we moved, piece had just moved there (n) | 21 |
| capturer unseen when we moved, piece had just moved there (b) | 14 |
| capturer unseen when we moved (q) | 10 |
| capturer unseen when we moved (b) | 6 |
| capturer unseen when we moved (r) | 5 |
| capturer visible when we moved, piece had just moved there (n) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 2 |
| other | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved, piece had just moved there (q) | 1 |
| capturer visible when we moved (p) | 1 |
| capturer unseen when we moved (p) | 1 |
| capturer visible when we moved (r) | 1 |
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
| udvd9eq7 | Instructors | B | win | 75 | King capturable |
| ycpjxbk0 | Instructors | B | win | 115 | King capturable |
| bkts8yup | Greek Gift | B | win | 77 | King capturable |
| ibob3d6l | Knight Vision | W | win | 40 | King capturable |
| ti3yccs0 | Strongly Invisible | B | win | 99 | King capturable |
| vzxywc1m | Knight Vision | B | win | 83 | King capturable |
| 280d7c3u | Instructors | W | win | 88 | King capturable |
| rs19o3ma | Instructors | B | win | 103 | King capturable |
| zjtrybuj | duck | W | win | 62 | King capturable |
| 3xmwlps6 | duck | W | win | 130 | King capturable |
