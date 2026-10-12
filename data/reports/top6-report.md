# Against the top six

Updated 2026-10-12 05:10 UTC; leaderboard fetched 2026-10-12T05:10. Active version: v33. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2146 | +314 |
| Knight Vision | 2118 | +286 |
| Decent Chess Bot | 2047 | +215 |
| Strongly Invisible | 2063 | +231 |
| **duck** | 1970 | +138 |
| **Instructors** | 1927 | +95 |
| TA Baseline S | 1638 | -194 |
| **IAmAVirus** | 1832 |  |
| TA Baseline A | 1507 | -324 |
| TA Baseline P | 1441 | -391 |

## Record by version (W-D-L)

| opponent | v33 | v32 | v30 | v28 | v27 | v26 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 1-0-11 | 0-0-2 | 2-2-24 |  |  |  |
| Knight Vision | 5-0-15 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 | 0-0-4 |
| Decent Chess Bot | 5-0-15 |  | 6-1-31 | 0-0-2 |  | 0-0-4 |
| Strongly Invisible | 4-1-7 |  | 4-1-31 | 0-0-2 |  |  |
| **duck** | 6-0-10 | 0-0-4 | 9-5-40 | 1-0-3 |  |  |
| **Instructors** | 3-0-11 | 2-0-4 | 10-3-35 | 1-0-1 |  | 0-0-2 |
| TA Baseline P | 8-0-0 |  | 50-2-2 | 2-0-0 | 1-0-1 |  |
| TA Baseline A | 19-0-0 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 | 2-1-1 |
| TA Baseline S | 12-0-4 | 3-0-3 | 27-5-18 | 4-0-0 |  | 2-0-2 |

## Skill gaps (rates per 100 moves unless noted)

Active version v33. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.6 | 33.5 | 32.2 | 35.2 | 36.4 | 31.7 | 32.7 |
|  | vision-gaining moves | 19.3 | 20.8 | 18.5 | 22.4 | 21.8 | 18.2 | 19.1 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.47 | 0.42 | 0.45 | 0.41 | 0.54 | 0.34 | 0.40 |
|  | captures from unseen squares | 10.4 | 10.7 | 9.9 | 11.2 | 14.4 | 8.2 | 8.3 |
|  | captures after a route the other side never saw | 15.0 | 17.8 | 15.8 | 19.4 | 19.3 | 16.0 | 15.0 |
|  | long slider strikes | 5.4 | 5.6 | 5.0 | 5.5 | 6.4 | 5.3 | 4.4 |
| King pressure | moves that attack the enemy king | 4.2 | 4.0 | 4.7 | 4.2 | 5.6 | 3.3 | 3.6 |
|  | ...with an attacker the king's side cannot see | 2.0 | 2.0 | 2.0 | 2.5 | 3.1 | 0.9 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.4 | 0.2 | 0.3 | 0.7 | 0.2 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.7 | 4.0 | 3.1 | 4.7 | 5.7 | 1.9 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.9 ⚠ | 1.7 | 4.5 ⚠ | 1.5 | 1.8 | 3.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.3 | 3.6 | 3.3 | 2.7 | 1.8 | 4.6 | 2.9 |
|  | queen left attacked by an unseen piece | 0.5 | 0.2 | 0.4 | 0.2 | 0.3 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 10.2 ⚠ | 3.6 | 9.5 ⚠ | 2.8 | 4.8 | 6.1 | 5.3 |
| King handling | king moves | 14.1 | 14.3 | 15.7 | 10.6 | 7.9 | 16.0 | 15.8 |
|  | king moves beyond the second rank | 1.8 | 5.7 | 4.0 | 2.0 | 1.2 | 3.8 | 5.0 |
|  | castling | 2.1 | 1.9 | 2.3 | 2.1 | 2.3 | 2.3 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v33 against the top six

Record 24-1-69; 69 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 29 | 8 |
| king already attacked by an unseen piece | 13 | 3 |
| king walked into an unseen attacker after taking the bait (king capture) | 12 | 4 |
| king already attacked by an unseen piece (no safe move existed) | 10 | 6 |
| king left to an attacker we could see (no safe move existed) | 4 | 0 |
| our move opened a line from an unseen attacker | 1 | 0 |

Pieces that took our king: r 31, q 27, n 4, b 3, k 2, p 1, qr 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 35, opening (ply < 30) 25, late (70+) or never 3 down 9.
- Down 3 or more at some point in 65 of 69 losses; median first ply 37.
- Down 5 or more in 61; median first ply 43.
- Lost although we had led by 3 or more: 6 of 69.
- Our clock at 15 s or less: 0 of 69.
- Median length 78 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 24 |
| capturer unseen when we moved, piece had just moved there (r) | 12 |
| capturer unseen when we moved, piece had just moved there (n) | 9 |
| capturer unseen when we moved, piece had just moved there (b) | 5 |
| capturer unseen when we moved (q) | 5 |
| capturer unseen when we moved (r) | 2 |
| capturer visible when we moved, piece had just moved there (n) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer unseen when we moved (b) | 1 |
| capturer unseen when we moved, piece had just moved there (p) | 1 |
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
