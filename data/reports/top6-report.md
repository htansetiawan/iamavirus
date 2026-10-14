# Against the top six

Updated 2026-10-14 00:45 UTC; leaderboard fetched 2026-10-14T00:44. Active version: v34. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2282 | +435 |
| Knight Vision | 2126 | +279 |
| Decent Chess Bot | 2086 | +239 |
| Strongly Invisible | 2085 | +238 |
| **duck** | 1975 | +128 |
| **Instructors** | 1887 | +40 |
| TA Baseline S | 1696 | -151 |
| **IAmAVirus** | 1847 |  |
| TA Baseline A | 1547 | -300 |
| TA Baseline P | 1489 | -358 |

## Record by version (W-D-L)

| opponent | v34 | v33 | v32 | v30 | v28 | v27 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 1-1-34 | 5-0-41 | 0-0-2 | 2-2-24 |  |  |
| Knight Vision | 5-3-32 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 | 0-0-2 |
| Decent Chess Bot | 10-1-37 | 10-1-43 |  | 6-1-31 | 0-0-2 |  |
| Strongly Invisible | 10-0-40 | 15-1-44 |  | 4-1-31 | 0-0-2 |  |
| **duck** | 14-1-37 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |  |
| **Instructors** | 23-2-37 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |  |
| TA Baseline P | 22-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 | 1-0-1 |
| TA Baseline A | 52-2-4 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 | 1-0-1 |
| TA Baseline S | 48-0-6 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |  |

## Skill gaps (rates per 100 moves unless noted)

Active version v34. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.4 | 34.1 | 31.8 | 35.2 | 35.3 | 31.7 | 33.1 |
|  | vision-gaining moves | 20.7 | 19.8 | 20.7 | 21.4 | 22.3 | 19.1 | 19.2 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.43 | 0.43 | 0.45 | 0.38 | 0.50 | 0.33 | 0.41 |
|  | captures from unseen squares | 9.6 | 10.1 | 9.2 | 9.7 | 12.0 | 7.3 | 8.5 |
|  | captures after a route the other side never saw | 15.8 | 16.3 | 15.0 | 18.6 | 18.3 | 13.4 | 14.9 |
|  | long slider strikes | 4.8 | 4.6 | 4.7 | 5.3 | 5.5 | 4.4 | 4.3 |
| King pressure | moves that attack the enemy king | 3.3 ⚠ | 4.6 | 2.6 ⚠ | 4.8 | 4.4 | 2.3 | 3.5 |
|  | ...with an attacker the king's side cannot see | 1.5 | 2.3 | 0.8 ⚠ | 2.4 | 2.7 | 0.4 | 1.6 |
|  | sacrifices that lead to a king capture | 0.1 | 0.2 | 0.1 | 0.3 | 0.7 | 0.0 | 0.2 |
| Queen activity | queen moves into the enemy half | 3.7 | 4.7 | 2.9 | 4.9 | 4.6 | 1.8 | 3.1 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 3.4 ⚠ | 1.6 | 4.2 ⚠ | 1.2 | 1.8 | 3.3 | 1.7 |
|  | pieces walked onto squares hit by unseen attackers | 3.2 | 2.4 | 3.5 ⚠ | 2.2 | 1.5 | 3.6 | 3.1 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.2 | 0.2 | 0.1 | 0.5 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 6.8 ⚠ | 4.5 | 7.6 ⚠ | 3.4 | 4.2 | 6.2 | 5.7 |
| King handling | king moves | 16.4 | 12.9 | 17.5 | 11.2 | 9.1 | 13.0 | 15.2 |
|  | king moves beyond the second rank | 4.1 | 2.9 | 5.3 | 2.8 | 1.8 | 2.2 | 4.4 |
|  | castling | 2.1 | 2.1 | 2.1 | 2.2 | 2.0 | 2.2 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v34 against the top six

Record 63-8-217; 217 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 98 | 33 |
| king already attacked by an unseen piece | 45 | 14 |
| king walked into an unseen attacker after taking the bait (king capture) | 26 | 9 |
| king already attacked by an unseen piece (no safe move existed) | 24 | 6 |
| king left to an attacker we could see (no safe move existed) | 16 | 8 |
| our move opened a line from an unseen attacker | 8 | 4 |

Pieces that took our king: q 123, r 64, n 13, b 7, k 4, p 2, qr 2, nq 1, br 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 132, late (70+) or never 3 down 47, opening (ply < 30) 38.
- Down 3 or more at some point in 197 of 217 losses; median first ply 43.
- Down 5 or more in 193; median first ply 47.
- Lost although we had led by 3 or more: 18 of 217.
- Our clock at 15 s or less: 0 of 217.
- Median length 78 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (q) | 78 |
| capturer unseen when we moved, piece had just moved there (r) | 39 |
| capturer unseen when we moved, piece had just moved there (n) | 20 |
| capturer unseen when we moved, piece had just moved there (b) | 14 |
| capturer unseen when we moved (q) | 9 |
| capturer unseen when we moved (b) | 7 |
| capturer unseen when we moved (n) | 6 |
| capturer unseen when we moved (r) | 5 |
| other | 5 |
| capturer unseen when we moved (p) | 4 |
| capturer visible when we moved (q) | 3 |
| capturer unseen when we moved, piece had just moved there (p) | 3 |
| capturer visible when we moved (b) | 2 |
| capturer visible when we moved, piece had just moved there (p) | 1 |
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
| o1zk47ek | duck | B | win | 75 | King capturable |
| 8qruqdt1 | Decent Chess Bot | B | win | 61 | King capturable |
| bhyq3nht | Instructors | W | win | 40 | King capturable |
| np3pbx8c | Instructors | B | win | 91 | King capturable |
| wvb70h0v | Knight Vision | W | draw | 97 | Threefold repetition |
| nt4qf9fl | Knight Vision | B | draw | 138 | Threefold repetition |
| cw96qyk8 | duck | B | win | 47 | King capturable |
| iso3xl9u | Instructors | B | win | 97 | King capturable |
| fziyxy3g | Instructors | W | win | 92 | King capturable |
| iephcpwl | duck | B | win | 5 | King capturable |
| m9sg9bhc | Decent Chess Bot | B | win | 85 | King capturable |
| y8vbimyh | duck | W | win | 148 | King capturable |
| 0jl9lbsc | Strongly Invisible | W | win | 96 | King capturable |
| 2befnpma | Strongly Invisible | B | win | 135 | King capturable |
| a9wciyvi | Instructors | W | win | 14 | King capturable |
| qqm0fhjh | Instructors | B | draw | 99 | Threefold repetition |
| ro7jj10j | Instructors | B | win | 95 | King capturable |
| 0r1k86vv | Instructors | W | win | 84 | King capturable |
| 3x8iwche | Strongly Invisible | B | win | 111 | King capturable |
| riym93ih | Instructors | B | win | 101 | King capturable |
| toe238b5 | Strongly Invisible | W | win | 86 | King capturable |
| 98aje6v3 | duck | W | win | 100 | King capturable |
| dzmazevd | duck | B | win | 207 | King capturable |
| p2ggmgpc | Decent Chess Bot | W | draw | 80 | Threefold repetition |
| ppk3o8v8 | Knight Vision | W | win | 68 | King capturable |
| kw938q3t | Knight Vision | W | win | 46 | King capturable |
| 5ytc7zxa | Instructors | W | win | 84 | King capturable |
| o8qo5hn8 | Strongly Invisible | W | win | 104 | King capturable |
| dktsyigf | Decent Chess Bot | B | win | 123 | King capturable |
| bjjjgdns | Decent Chess Bot | B | win | 71 | King capturable |
| 8cmvjx19 | Decent Chess Bot | W | win | 134 | King capturable |
| sc4puuvs | Greek Gift | W | draw | 121 | Threefold repetition |
| zpal1iv1 | duck | B | win | 103 | King capturable |
| spbqputi | duck | W | win | 36 | King capturable |
| szl1j9ku | Instructors | W | win | 104 | King capturable |
| mkcygww5 | Greek Gift | W | win | 72 | King capturable |
| 261ktm5x | duck | B | win | 85 | King capturable |
| 49ffudf7 | Instructors | B | win | 85 | King capturable |
| ulxqmous | Instructors | W | win | 108 | King capturable |
| 115fm1yb | Instructors | W | draw | 79 | Threefold repetition |
| 3j22jsfv | Decent Chess Bot | W | win | 144 | King capturable |
