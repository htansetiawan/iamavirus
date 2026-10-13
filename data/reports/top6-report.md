# Against the top six

Updated 2026-10-13 08:53 UTC; leaderboard fetched 2026-10-13T08:53. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2235 | +336 |
| Knight Vision | 2115 | +216 |
| Decent Chess Bot | 2061 | +161 |
| Strongly Invisible | 2076 | +176 |
| **duck** | 1961 | +61 |
| **Instructors** | 1965 | +65 |
| TA Baseline S | 1684 | -216 |
| **IAmAVirus** | 1900 |  |
| TA Baseline A | 1553 | -347 |
| TA Baseline P | 1476 | -424 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 0-0-14 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 3-1-10 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 4-0-17 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 5-0-13 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 5-1-14 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 11-0-13 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 10-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 24-2-0 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 26-0-2 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.8 | 34.2 | 31.9 | 35.1 | 34.9 | 31.1 | 32.3 |
|  | vision-gaining moves | 22.3 | 19.6 | 21.0 | 21.3 | 21.7 | 18.0 | 18.4 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.44 | 0.39 | 0.48 | 0.40 | 0.49 | 0.34 | 0.39 |
|  | captures from unseen squares | 10.1 | 9.3 | 9.5 | 9.9 | 11.4 | 7.2 | 7.7 |
|  | captures after a route the other side never saw | 16.4 | 16.4 | 14.5 ⚠ | 18.3 | 17.8 | 12.6 | 14.2 |
|  | long slider strikes | 5.2 | 4.8 | 4.7 | 5.8 | 5.1 | 4.4 | 4.1 |
| King pressure | moves that attack the enemy king | 3.7 | 4.3 | 2.5 ⚠ | 5.1 | 4.6 | 2.4 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.5 | 2.3 | 0.5 ⚠ | 2.7 | 3.0 | 0.5 | 1.4 |
|  | sacrifices that lead to a king capture | 0.1 | 0.2 | 0.0 | 0.5 | 0.6 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 4.8 | 5.1 | 3.3 | 4.1 | 4.5 | 2.0 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.1 ⚠ | 1.4 | 4.3 ⚠ | 1.5 | 1.7 | 3.4 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.5 | 3.0 | 2.1 | 1.6 | 3.9 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.3 | 0.2 | 0.1 | 0.4 | 0.1 |
|  | bare back rank with enemy heavy pieces alive | 5.9 ⚠ | 3.9 | 7.1 ⚠ | 3.4 | 4.2 | 5.3 | 4.7 |
| King handling | king moves | 16.9 | 12.4 | 17.6 | 10.8 | 10.4 | 14.9 | 16.1 |
|  | king moves beyond the second rank | 5.5 | 3.1 | 7.1 | 2.6 | 2.5 | 2.9 | 5.2 |
|  | castling | 2.3 | 2.2 | 2.1 | 2.2 | 1.7 | 2.1 | 1.7 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 28-2-81; 81 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 30 | 12 |
| king already attacked by an unseen piece | 17 | 5 |
| king already attacked by an unseen piece (no safe move existed) | 12 | 5 |
| king walked into an unseen attacker after taking the bait (king capture) | 10 | 2 |
| king left to an attacker we could see (no safe move existed) | 8 | 2 |
| our move opened a line from an unseen attacker | 4 | 1 |

Pieces that took our king: q 49, r 20, n 5, b 3, k 2, p 1, nq 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 52, late (70+) or never 3 down 16, opening (ply < 30) 13.
- Down 3 or more at some point in 75 of 81 losses; median first ply 44.
- Down 5 or more in 71; median first ply 48.
- Lost although we had led by 3 or more: 7 of 81.
- Our clock at 15 s or less: 0 of 81.
- Median length 76 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 31 |
| capturer unseen when we moved, piece had just moved there (r) | 15 |
| capturer unseen when we moved, piece had just moved there (b) | 7 |
| capturer unseen when we moved, piece had just moved there (n) | 5 |
| capturer unseen when we moved (b) | 3 |
| capturer unseen when we moved (q) | 3 |
| capturer visible when we moved (q) | 2 |
| capturer unseen when we moved (p) | 2 |
| capturer unseen when we moved (n) | 2 |
| capturer visible when we moved (b) | 2 |
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
| 90qk1vsr | duck | W | draw | 101 | Threefold repetition |
| gted2lyt | Strongly Invisible | B | win | 125 | King capturable |
