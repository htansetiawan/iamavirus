# Against the top six

Updated 2026-10-13 07:31 UTC; leaderboard fetched 2026-10-13T07:30. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2234 | +338 |
| Knight Vision | 2072 | +177 |
| Decent Chess Bot | 2058 | +162 |
| Strongly Invisible | 2085 | +189 |
| **duck** | 1979 | +83 |
| **Instructors** | 1973 | +78 |
| TA Baseline S | 1682 | -214 |
| **IAmAVirus** | 1896 |  |
| TA Baseline A | 1581 | -314 |
| TA Baseline P | 1442 | -454 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-14 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 3-1-8 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 4-0-12 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 4-0-12 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 5-0-14 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 11-0-13 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 5-1-0 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 14-2-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 22-0-2 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 33.0 | 34.4 | 32.0 | 35.1 | 34.1 | 31.0 | 32.3 |
|  | vision-gaining moves | 22.6 | 19.6 | 21.0 | 21.3 | 20.2 | 17.9 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.39 | 0.47 | 0.40 | 0.50 | 0.35 | 0.39 |
|  | captures from unseen squares | 10.1 | 9.4 | 9.2 | 10.0 | 11.0 | 7.4 | 7.7 |
|  | captures after a route the other side never saw | 16.4 | 16.4 | 14.5 | 17.7 | 17.0 | 13.1 | 14.2 |
|  | long slider strikes | 5.2 | 4.8 | 4.6 | 5.6 | 4.7 | 4.3 | 4.1 |
| King pressure | moves that attack the enemy king | 3.8 | 4.3 | 2.8 ⚠ | 5.2 | 4.7 | 2.6 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.6 | 2.4 | 0.5 ⚠ | 2.8 | 3.0 | 0.6 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.2 | 0.0 | 0.5 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 4.9 | 5.2 | 3.4 | 4.1 | 4.7 | 2.2 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.2 ⚠ | 1.4 | 4.1 ⚠ | 1.6 | 1.8 | 3.1 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.5 | 2.9 | 2.2 | 1.8 | 3.3 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.3 | 0.2 | 0.1 | 0.5 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 6.1 ⚠ | 4.0 | 7.5 ⚠ | 3.5 | 4.6 | 6.1 | 4.7 |
| King handling | king moves | 16.7 | 12.3 | 17.6 | 10.7 | 11.6 | 16.3 | 16.1 |
|  | king moves beyond the second rank | 5.2 | 3.1 | 6.9 | 2.6 | 3.0 | 3.3 | 5.2 |
|  | castling | 2.3 | 2.3 | 2.1 | 2.3 | 1.5 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 27-1-73; 73 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 27 | 12 |
| king already attacked by an unseen piece | 16 | 5 |
| king already attacked by an unseen piece (no safe move existed) | 11 | 5 |
| king walked into an unseen attacker after taking the bait (king capture) | 9 | 2 |
| king left to an attacker we could see (no safe move existed) | 7 | 2 |
| our move opened a line from an unseen attacker | 3 | 1 |

Pieces that took our king: q 45, r 17, n 5, k 2, b 2, p 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 45, late (70+) or never 3 down 15, opening (ply < 30) 13.
- Down 3 or more at some point in 68 of 73 losses; median first ply 42.5.
- Down 5 or more in 65; median first ply 47.
- Lost although we had led by 3 or more: 6 of 73.
- Our clock at 15 s or less: 0 of 73.
- Median length 77 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 28 |
| capturer unseen when we moved, piece had just moved there (r) | 13 |
| capturer unseen when we moved, piece had just moved there (b) | 7 |
| capturer unseen when we moved, piece had just moved there (n) | 5 |
| capturer unseen when we moved (q) | 3 |
| capturer visible when we moved (q) | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer visible when we moved (b) | 2 |
| capturer unseen when we moved (b) | 2 |
| capturer unseen when we moved (n) | 1 |
| capturer unseen when we moved (r) | 1 |
| other | 1 |
| capturer visible when we moved (p) | 1 |

## What worked: v34's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| gzj7ox1o | Instructors | W | win | 66 | King capturable |
| y4qk2v2b | Instructors | B | win | 9 | King capturable |
| np6c6tub | Instructors | B | win | 61 | King capturable |
| 05l0ejxw | Instructors | W | win | 66 | King capturable |
| 19pwd8n9 | Knight Vision | W | win | 50 | King capturable |
| sdr3y95n | Decent Chess Bot | W | win | 138 | King capturable |
| znv5996o | duck | W | win | 44 | King capturable |
| u5hyxqe5 | duck | B | win | 61 | King capturable |
| sjyd7bcw | duck | W | win | 86 | King capturable |
| wnso8ft4 | duck | B | win | 107 | King capturable |
| n3e191mm | Instructors | B | win | 45 | King capturable |
| p5k8pu4u | Instructors | W | win | 68 | King capturable |
| n9entvtq | duck | B | win | 101 | King capturable |
| frmdez59 | Instructors | W | win | 66 | King capturable |
| bd2qdd48 | Instructors | B | win | 87 | King capturable |
| qo7iigz9 | Strongly Invisible | B | win | 9 | King capturable |
| fkt72pd8 | Instructors | W | win | 102 | King capturable |
| wz467mbn | Instructors | W | win | 96 | King capturable |
| dgdbtyya | Decent Chess Bot | W | win | 96 | King capturable |
| tbbl82pn | Decent Chess Bot | W | win | 50 | King capturable |
| 17fl1nq7 | Decent Chess Bot | B | win | 79 | King capturable |
| iwo0axp7 | Strongly Invisible | B | win | 153 | King capturable |
| mqfh05o1 | Knight Vision | B | draw | 160 | Threefold repetition |
| jo0cu337 | Strongly Invisible | W | win | 60 | King capturable |
| bq2vio40 | Strongly Invisible | B | win | 101 | King capturable |
| e1v2pu2s | Knight Vision | B | win | 29 | King capturable |
| pdsihv7f | Knight Vision | W | win | 58 | King capturable |
| 4nun0itq | Instructors | B | win | 93 | King capturable |
