# Against the top six

Updated 2026-10-15 02:07 UTC; leaderboard fetched 2026-10-15T02:06. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2266 | +339 |
| Knight Vision | 2081 | +154 |
| Decent Chess Bot | 2021 | +95 |
| Strongly Invisible | 2074 | +147 |
| **duck** | 1977 | +50 |
| **Instructors** | 1933 | +6 |
| TA Baseline S | 1681 | -246 |
| **IAmAVirus** | 1927 |  |
| TA Baseline A | 1521 | -406 |
| TA Baseline P | 1390 | -537 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 3-1-16 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 12-0-28 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot | 8-1-11 | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 8-0-24 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 12-0-34 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 9-0-25 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P | 14-0-0 | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 21-0-1 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 21-0-3 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.0 | 34.7 | 32.4 | 34.5 | 36.1 | 32.0 | 33.2 |
|  | vision-gaining moves | 20.0 | 21.2 | 20.8 | 21.6 | 22.4 | 17.8 | 18.9 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.41 | 0.42 | 0.41 | 0.38 | 0.47 | 0.39 | 0.39 |
|  | captures from unseen squares | 8.7 | 9.9 | 9.1 | 9.7 | 11.6 | 9.2 | 8.1 |
|  | captures after a route the other side never saw | 15.4 | 16.3 | 15.6 | 18.5 | 18.7 | 14.0 | 14.7 |
|  | long slider strikes | 4.7 | 5.2 | 4.9 | 5.1 | 5.2 | 5.4 | 4.2 |
| King pressure | moves that attack the enemy king | 2.8 ⚠ | 4.7 | 3.0 ⚠ | 4.8 | 4.9 | 2.7 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.3 | 2.2 | 1.1 ⚠ | 2.5 | 3.2 | 0.7 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.4 | 0.1 | 0.2 | 0.8 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.7 | 4.3 | 2.2 | 3.5 | 3.5 | 1.9 | 3.0 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.3 ⚠ | 1.5 | 2.7 ⚠ | 1.3 | 2.1 | 3.3 | 1.6 |
|  | pieces walked onto squares hit by unseen attackers | 3.0 | 2.7 | 3.3 ⚠ | 2.2 | 1.8 | 4.2 | 3.0 |
|  | queen left attacked by an unseen piece | 0.2 | 0.1 | 0.3 | 0.2 | 0.0 | 0.3 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 8.0 ⚠ | 4.6 | 8.2 ⚠ | 3.3 | 2.8 | 5.8 | 5.3 |
| King handling | king moves | 17.7 | 9.5 | 15.4 | 11.6 | 7.9 | 11.9 | 15.1 |
|  | king moves beyond the second rank | 3.5 | 1.7 | 3.2 | 3.4 | 1.5 | 3.8 | 4.6 |
|  | castling | 1.9 | 2.1 | 2.2 | 2.1 | 1.8 | 2.0 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 52-2-138; 138 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 72 | 32 |
| king already attacked by an unseen piece | 31 | 11 |
| king walked into an unseen attacker after taking the bait (king capture) | 22 | 11 |
| king left to an attacker we could see (no safe move existed) | 11 | 4 |
| our move opened a line from an unseen attacker | 2 | 1 |

Pieces that took our king: r 63, q 55, b 7, n 5, k 4, p 3, br 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 93, opening (ply < 30) 23, late (70+) or never 3 down 22.
- Down 3 or more at some point in 130 of 138 losses; median first ply 45.0.
- Down 5 or more in 122; median first ply 54.5.
- Lost although we had led by 3 or more: 7 of 138.
- Our clock at 15 s or less: 0 of 138.
- Median length 81.5 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 42 |
| capturer unseen when we moved, piece had just moved there (n) | 20 |
| capturer unseen when we moved, piece had just moved there (b) | 14 |
| capturer unseen when we moved, piece had just moved there (q) | 12 |
| capturer unseen when we moved (q) | 6 |
| capturer unseen when we moved (n) | 6 |
| capturer unseen when we moved (r) | 5 |
| capturer unseen when we moved (b) | 4 |
| other | 4 |
| capturer unseen when we moved, piece had just moved there (p) | 4 |
| capturer visible when we moved (p) | 3 |
| capturer unseen when we moved (p) | 3 |
| capturer visible when we moved (n) | 3 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
| capturer visible when we moved (b) | 1 |
| capturer visible when we moved, piece had just moved there (r) | 1 |
| capturer visible when we moved (r) | 1 |

## What worked: v35's wins and draws against the top six

| id | opponent | us | result | plies | reason |
| --- | --- | --- | --- | --- | --- |
| ol5e72pm | duck | B | win | 97 | King capturable |
| 61bzys3l | Instructors | W | win | 98 | King capturable |
| c5cnjewf | Strongly Invisible | W | win | 124 | King capturable |
| h2u89knk | Instructors | B | win | 113 | King capturable |
| gt1mghiq | Instructors | W | win | 80 | King capturable |
| tlaqq2oz | Strongly Invisible | W | win | 120 | King capturable |
| dwyhzuvv | Instructors | W | win | 48 | King capturable |
| 9dlc0mgv | Knight Vision | W | win | 76 | King capturable |
| sjvstkmq | Knight Vision | B | win | 65 | King capturable |
| whx4qqln | Greek Gift | B | win | 111 | King capturable |
| 1b9cgn8c | Knight Vision | B | win | 67 | King capturable |
| p4ki6f81 | duck | W | win | 54 | King capturable |
| ypy8cnxv | duck | B | win | 99 | King capturable |
| kxkm3ewh | Strongly Invisible | B | win | 67 | King capturable |
| 0yc4k7zr | Greek Gift | W | win | 88 | King capturable |
| llxllazf | Decent Chess Bot | W | win | 60 | King capturable |
| f3qhsn1p | Strongly Invisible | W | win | 88 | King capturable |
| hqk1jhep | duck | W | win | 68 | King capturable |
| 9fwegd4g | Instructors | W | win | 70 | King capturable |
| va6pv7uf | Strongly Invisible | B | win | 97 | King capturable |
| 8x4m9ds3 | Decent Chess Bot | W | win | 68 | King capturable |
| 81ad7fm9 | duck | W | win | 86 | King capturable |
| gt4i6a6q | duck | B | win | 95 | King capturable |
| 3gswuuyj | Strongly Invisible | W | win | 76 | King capturable |
| p9ff21uk | Decent Chess Bot | B | draw | 114 | Threefold repetition |
| i4fx2fc5 | Knight Vision | B | win | 67 | King capturable |
| em1o8ynh | duck | B | win | 79 | King capturable |
| 0oaoht7a | Decent Chess Bot | B | win | 47 | King capturable |
| dak540m5 | Decent Chess Bot | W | win | 140 | King capturable |
| c8blbwsd | duck | W | win | 104 | King capturable |
| n5thcux1 | Decent Chess Bot | W | win | 148 | King capturable |
| sa74ct2b | Decent Chess Bot | B | win | 149 | King capturable |
| 91y36gm2 | Knight Vision | B | win | 61 | King capturable |
| cvlwe3jy | Instructors | W | win | 80 | King capturable |
| em6c5ypk | Knight Vision | B | win | 59 | King capturable |
| 6d37j0ih | Greek Gift | B | win | 129 | King capturable |
| gyilqvmx | Knight Vision | B | win | 69 | King capturable |
| 9n1kzsz2 | Knight Vision | W | win | 106 | King capturable |
| j3uxv19m | Knight Vision | W | win | 44 | King capturable |
| 7hivhp9l | Instructors | W | win | 82 | King capturable |
| fhkdqnwa | Knight Vision | W | win | 78 | King capturable |
| ansdqn1x | Instructors | W | win | 110 | King capturable |
| dt7hlk6l | Greek Gift | W | draw | 64 | Threefold repetition |
| 36q11are | Decent Chess Bot | W | win | 96 | King capturable |
| 7dq0e86p | Decent Chess Bot | B | win | 131 | King capturable |
| spm7agay | duck | W | win | 112 | King capturable |
| g728j51o | duck | W | win | 84 | King capturable |
| hjjjnibq | duck | W | win | 94 | King capturable |
| kp8ob155 | duck | B | win | 139 | King capturable |
| ipioxd1s | Strongly Invisible | W | win | 50 | King capturable |
| ie7lqaeu | Knight Vision | W | win | 74 | King capturable |
| qdj87mkg | Instructors | W | win | 98 | King capturable |
| 8plkbxg7 | Knight Vision | B | win | 61 | King capturable |
| tf4nvgyh | Strongly Invisible | W | win | 70 | King capturable |
