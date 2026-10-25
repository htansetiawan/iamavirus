# Against the top six

Updated 2026-10-25 10:11 UTC; leaderboard fetched 2026-10-25T10:02. Active version: v35. Measurement only.

## Ladder

| team | rating | gap to us |
| --- | --- | --- |
| Greek Gift | 2353 | +469 |
| Knight Vision | 2162 | +278 |
| Decent Chess Bot | 2095 | +211 |
| Strongly Invisible | 2107 | +223 |
| **duck** | 1962 | +78 |
| **Instructors** | 1982 | +98 |
| TA Baseline S | 1688 | -196 |
| **IAmAVirus** | 1884 |  |
| TA Baseline A | 1533 | -351 |
| TA Baseline P | 1382 | -502 |

## Record by version (W-D-L)

| opponent | v35 | v34 | v33 | v32 | v30 | v28 |
| --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 18-6-258 | 1-1-40 | 5-0-41 | 0-0-2 | 2-2-24 |  |
| Knight Vision | 100-6-298 | 7-3-36 | 19-1-56 | 0-0-4 | 12-3-27 | 0-0-2 |
| Decent Chess Bot | 128-12-314 | 13-1-40 | 10-1-43 |  | 6-1-31 | 0-0-2 |
| Strongly Invisible | 86-16-325 | 12-0-44 | 15-1-44 |  | 4-1-31 | 0-0-2 |
| **duck** | 135-22-294 | 15-1-44 | 22-3-41 | 0-0-4 | 9-5-40 | 1-0-3 |
| **Instructors** | 169-7-248 | 29-2-47 | 15-0-35 | 2-0-4 | 10-3-35 | 1-0-1 |
| TA Baseline P | 162-2-8 | 26-1-1 | 46-0-2 |  | 50-2-2 | 2-0-0 |
| TA Baseline A | 225-3-28 | 57-2-5 | 51-0-3 | 4-0-0 | 50-10-6 | 3-0-1 |
| TA Baseline S | 291-4-62 | 57-0-13 | 53-1-16 | 3-0-3 | 27-5-18 | 4-0-0 |

## Skill gaps (rates per 100 moves unless noted)

Active version v35. "them" is the opponent in those games; "top six among themselves" is both sides of the 400 most recent games between top-six teams.

| skill | measure | us vs duck + Instructors | them | us vs other four | them | us vs TA baselines (contrast) | them | top six among themselves |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Information | squares we see (mean) | 32.0 | 33.6 | 31.8 | 35.0 | 35.6 | 31.9 | 32.7 |
|  | vision-gaining moves | 20.3 | 20.0 | 20.0 | 20.7 | 21.8 | 18.3 | 18.6 |
| Stealth (attacking from the fog) | captures the victim's side could not see coming (share) | 0.42 | 0.40 | 0.43 | 0.39 | 0.48 | 0.36 | 0.40 |
|  | captures from unseen squares | 9.1 | 9.4 | 8.6 | 9.7 | 11.4 | 7.9 | 8.0 |
|  | captures after a route the other side never saw | 15.2 | 15.9 | 14.3 | 17.7 | 17.9 | 13.2 | 14.5 |
|  | long slider strikes | 4.8 | 4.7 | 4.4 | 4.9 | 5.0 | 4.6 | 4.0 |
| King pressure | moves that attack the enemy king | 3.1 ⚠ | 4.3 | 2.8 ⚠ | 5.0 | 4.4 | 2.8 | 3.2 |
|  | ...with an attacker the king's side cannot see | 1.4 | 2.1 | 1.0 ⚠ | 2.6 | 2.9 | 0.7 | 1.5 |
|  | sacrifices that lead to a king capture | 0.1 | 0.3 | 0.1 | 0.3 | 0.4 | 0.1 | 0.2 |
| Queen activity | queen moves into the enemy half | 2.7 | 3.3 | 2.4 | 3.7 | 3.9 | 2.0 | 2.8 |
| Discipline (not giving things away) | material given (3+ net over two plies) | 2.7 ⚠ | 1.7 | 3.1 ⚠ | 1.1 | 1.5 | 3.4 | 1.5 |
|  | pieces walked onto squares hit by unseen attackers | 2.9 | 2.6 | 3.3 ⚠ | 2.3 | 1.8 | 3.8 | 2.8 |
|  | queen left attacked by an unseen piece | 0.2 | 0.2 | 0.2 | 0.1 | 0.1 | 0.4 | 0.2 |
|  | bare back rank with enemy heavy pieces alive | 8.1 ⚠ | 4.0 | 8.6 ⚠ | 3.6 | 4.1 | 6.4 | 5.0 |
| King handling | king moves | 16.6 | 12.5 | 17.3 | 11.2 | 9.1 | 11.9 | 16.0 |
|  | king moves beyond the second rank | 4.4 | 3.3 | 4.4 | 3.1 | 1.7 | 2.6 | 4.7 |
|  | castling | 2.0 | 2.0 | 2.0 | 2.0 | 1.8 | 2.2 | 1.8 |

⚠ marks a gap of 20% or more in the direction that hurts us.

## Loss anatomy: v35 against the top six

Record 636-69-1737; 1737 losses analysed.

**How our king fell**

| ending | all top six | of which duck + Instructors |
| --- | --- | --- |
| king walked into an unseen attacker | 857 | 266 |
| king already attacked by an unseen piece | 377 | 119 |
| king walked into an unseen attacker after taking the bait (king capture) | 205 | 59 |
| king already attacked by an unseen piece (no safe move existed) | 150 | 53 |
| king left to an attacker we could see (no safe move existed) | 109 | 35 |
| our move opened a line from an unseen attacker | 38 | 10 |
| king left to an attacker we could see | 1 | 0 |

Pieces that took our king: r 812, q 663, b 100, n 71, k 41, p 27, qr 9, nr 4, pr 3, bq 2, kr 1, br 1, kp 1, pq 1, np 1

**When the material went** (levels held for four plies, so exchanges are not swings)

- Phase of the collapse: middlegame (30-69) 1023, late (70+) or never 3 down 420, opening (ply < 30) 294.
- Down 3 or more at some point in 1569 of 1737 losses; median first ply 45.
- Down 5 or more in 1484; median first ply 53.0.
- Lost although we had led by 3 or more: 136 of 1737.
- Our clock at 15 s or less: 0 of 1737.
- Median length 82 plies.

| what put us 3 down | losses |
| --- | --- |
| capturer unseen when we moved, piece had just moved there (r) | 454 |
| capturer unseen when we moved, piece had just moved there (n) | 228 |
| capturer unseen when we moved, piece had just moved there (b) | 190 |
| capturer unseen when we moved, piece had just moved there (q) | 178 |
| capturer unseen when we moved (n) | 69 |
| capturer unseen when we moved, piece had just moved there (p) | 69 |
| capturer unseen when we moved (r) | 64 |
| capturer unseen when we moved (b) | 45 |
| other | 45 |
| capturer unseen when we moved (q) | 39 |
| capturer unseen when we moved (p) | 36 |
| capturer visible when we moved (p) | 26 |
| capturer visible when we moved (b) | 23 |
| capturer visible when we moved (n) | 21 |
| capturer visible when we moved, piece had just moved there (p) | 19 |
| capturer visible when we moved (q) | 16 |
| capturer visible when we moved, piece had just moved there (r) | 14 |
| capturer visible when we moved (r) | 12 |
| capturer visible when we moved, piece had just moved there (n) | 10 |
| capturer visible when we moved, piece had just moved there (q) | 6 |
| capturer visible when we moved, piece had just moved there (b) | 5 |

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
| mj6cm3ff | Decent Chess Bot | W | win | 68 | King capturable |
| dadnkz87 | duck | W | win | 70 | King capturable |
| jgbhzuxr | Decent Chess Bot | B | win | 69 | King capturable |
| 9i0w7ro1 | Decent Chess Bot | W | win | 80 | King capturable |
| zp91vlsc | Decent Chess Bot | B | draw | 125 | Threefold repetition |
| ce89s1bi | Instructors | W | win | 126 | King capturable |
| aaunzwuj | duck | W | win | 106 | King capturable |
| e6na1mx2 | Decent Chess Bot | W | draw | 81 | Threefold repetition |
| qgrws5li | Strongly Invisible | W | win | 90 | King capturable |
| b7d3n5vw | duck | B | draw | 98 | Threefold repetition |
| ktc3mk0t | duck | W | win | 140 | King capturable |
| va05mb6j | Strongly Invisible | B | win | 125 | King capturable |
| m41amxol | Decent Chess Bot | B | win | 45 | King capturable |
| d4nu2rdn | Decent Chess Bot | W | win | 42 | King capturable |
| 6660t09l | Instructors | W | win | 116 | King capturable |
| t7nc7ku8 | Decent Chess Bot | W | win | 110 | King capturable |
| j5mq17vy | Instructors | B | win | 130 | Time forfeit |
| 3nrcmy5i | Decent Chess Bot | W | win | 172 | King capturable |
| cda03qsg | Decent Chess Bot | W | draw | 100 | Threefold repetition |
| mwicefvr | Strongly Invisible | B | win | 31 | King capturable |
| jsflylj3 | Strongly Invisible | W | win | 40 | King capturable |
| k1s138so | Strongly Invisible | W | win | 100 | King capturable |
| sdyyc9bq | Decent Chess Bot | B | win | 39 | King capturable |
| fv2uqu75 | duck | B | draw | 95 | Threefold repetition |
| voomop2n | Decent Chess Bot | B | win | 85 | King capturable |
| u4tgwyrs | Decent Chess Bot | W | win | 78 | King capturable |
| 7wmkpa67 | Decent Chess Bot | B | win | 123 | King capturable |
| oxzoi73i | Knight Vision | B | win | 41 | King capturable |
| vnp8f7wg | duck | W | win | 90 | King capturable |
| mwlsrf2o | duck | B | win | 91 | King capturable |
| 5sxk1jj0 | Knight Vision | B | win | 47 | King capturable |
| eotf8dd6 | Knight Vision | W | win | 104 | King capturable |
| 63x9t06m | duck | B | win | 121 | King capturable |
| 7clch33c | Instructors | W | win | 116 | King capturable |
| jqsvqtma | Decent Chess Bot | W | win | 162 | King capturable |
| rsoujzmh | Strongly Invisible | W | win | 254 | King capturable |
| 5m2aufh0 | Strongly Invisible | W | win | 102 | King capturable |
| ut8mush0 | duck | W | win | 112 | King capturable |
| 8vnj51uf | Instructors | B | win | 73 | King capturable |
| d501a32t | Instructors | W | win | 110 | King capturable |
| 4rzk2h2u | Instructors | B | win | 87 | King capturable |
| co9xgikz | Decent Chess Bot | W | win | 58 | King capturable |
| 8021opc0 | Decent Chess Bot | B | win | 65 | King capturable |
| gvuphew6 | Decent Chess Bot | W | win | 134 | King capturable |
| guiy5l9d | Instructors | W | win | 62 | King capturable |
| 54tqcvgw | Decent Chess Bot | W | win | 88 | King capturable |
| 8kzbvs90 | Knight Vision | W | win | 86 | King capturable |
| x6hzngi9 | Knight Vision | W | win | 80 | King capturable |
| jbfx4jv3 | Instructors | W | win | 90 | King capturable |
| e7wyb0mt | duck | B | win | 77 | King capturable |
| ljhf2tiw | Knight Vision | W | win | 54 | King capturable |
| 0nnrd8yz | duck | B | win | 43 | King capturable |
| 3b5hnwch | duck | W | win | 98 | King capturable |
| bnorefzr | Instructors | W | win | 46 | King capturable |
| 1cfhaxyz | Decent Chess Bot | W | win | 150 | King capturable |
| be383d1b | Decent Chess Bot | B | win | 109 | King capturable |
| ks7zv08n | Strongly Invisible | B | win | 113 | King capturable |
| ejb4p4y7 | Strongly Invisible | W | win | 152 | King capturable |
| h1an31sb | Strongly Invisible | B | draw | 113 | Threefold repetition |
| 63ha052v | Decent Chess Bot | W | win | 92 | King capturable |
| rg0hykre | Knight Vision | B | draw | 102 | Threefold repetition |
| lupr7v4k | duck | W | win | 90 | King capturable |
| l8i2h9ed | duck | B | draw | 102 | Threefold repetition |
| id2nvgi4 | duck | B | win | 95 | King capturable |
| 25ybjce4 | duck | W | win | 92 | King capturable |
| p4crhhem | Knight Vision | B | win | 33 | King capturable |
| 2ikdrpqs | Knight Vision | W | win | 144 | King capturable |
| miw5p1rp | Knight Vision | B | win | 47 | King capturable |
| hlygtdp7 | Instructors | B | win | 87 | King capturable |
| g6z7vp5a | Instructors | W | win | 112 | King capturable |
| u9fa1sxc | Greek Gift | B | draw | 224 | Threefold repetition |
| sk45si5h | duck | W | win | 70 | King capturable |
| v09u6suf | duck | W | win | 66 | King capturable |
| nrvrv9mt | Knight Vision | W | win | 26 | King capturable |
| ec8chhvw | Instructors | B | win | 53 | King capturable |
| hloui1d1 | Instructors | W | win | 114 | King capturable |
| c07aar4n | Instructors | B | win | 13 | King capturable |
| 6eedrb2e | Instructors | W | win | 116 | King capturable |
| m9f4ppud | Strongly Invisible | W | win | 100 | King capturable |
| 8os8mula | duck | W | win | 88 | King capturable |
| eyo69aq4 | Knight Vision | B | win | 117 | King capturable |
| cu6rl9fu | duck | B | win | 47 | King capturable |
| 5xwzt7a4 | duck | W | win | 56 | King capturable |
| 512k3a3e | Decent Chess Bot | W | win | 76 | King capturable |
| u50kj429 | duck | W | win | 90 | King capturable |
| 90ffpogq | Greek Gift | W | win | 118 | King capturable |
| 1mswhws0 | Instructors | W | win | 116 | King capturable |
| 4sgzmkb4 | Greek Gift | B | draw | 53 | Threefold repetition |
| exc4t4nk | Greek Gift | W | win | 74 | King capturable |
| same7u0i | duck | W | win | 68 | King capturable |
| kmhonwcs | duck | B | draw | 89 | Threefold repetition |
| 2l5re3v2 | duck | W | win | 74 | King capturable |
| jr9iyziy | duck | B | win | 117 | King capturable |
| rkgizgh1 | Knight Vision | B | win | 97 | King capturable |
| v0tr4kmj | Knight Vision | W | win | 102 | King capturable |
| 5mtblf8e | Strongly Invisible | W | win | 74 | King capturable |
| qvkyumkv | Strongly Invisible | B | draw | 103 | Threefold repetition |
| 61wver5d | Instructors | B | win | 131 | King capturable |
| 5hf93mid | Knight Vision | B | win | 101 | King capturable |
| qnxm7ll2 | Knight Vision | W | win | 90 | King capturable |
| x7vb2s1e | duck | B | win | 63 | King capturable |
| h5zelyjz | Decent Chess Bot | B | win | 25 | King capturable |
| g8xycd0d | Instructors | B | win | 61 | King capturable |
| xcive51x | Decent Chess Bot | W | win | 132 | King capturable |
| vlcetlyq | Instructors | B | win | 133 | King capturable |
| 8qqp3ssm | Knight Vision | B | win | 61 | King capturable |
| xok48v7i | Knight Vision | W | win | 98 | King capturable |
| qg5sygs6 | Instructors | W | win | 86 | King capturable |
| 7e4m0523 | Instructors | B | win | 95 | King capturable |
| 80fsh2dz | Knight Vision | W | win | 70 | King capturable |
| f5j1rp1h | duck | W | draw | 74 | Threefold repetition |
| m0evcis1 | Strongly Invisible | B | win | 83 | King capturable |
| ezh3ntn7 | Knight Vision | W | win | 78 | King capturable |
| wm69mmuq | Knight Vision | B | win | 101 | King capturable |
| g0jomad1 | duck | B | win | 87 | King capturable |
| mt68h42z | Instructors | W | win | 68 | King capturable |
| k1yzuex1 | Decent Chess Bot | W | win | 54 | King capturable |
| t7v4avip | Decent Chess Bot | W | win | 82 | King capturable |
| ybxrp8p6 | Decent Chess Bot | B | win | 115 | King capturable |
| 3zxiks00 | duck | W | win | 116 | King capturable |
| jd5aato2 | Instructors | B | win | 61 | King capturable |
| qjif8rw2 | Knight Vision | W | win | 66 | King capturable |
| uhuhzpbz | Instructors | B | win | 65 | King capturable |
| c3nsjyaj | Instructors | W | win | 86 | King capturable |
| ahi2l2mj | Decent Chess Bot | W | win | 60 | King capturable |
| tnu2qtng | Decent Chess Bot | B | win | 93 | King capturable |
| tmzcghfu | Strongly Invisible | W | win | 70 | King capturable |
| eaoch36l | Instructors | W | draw | 119 | Threefold repetition |
| mwo5ypul | duck | B | win | 55 | King capturable |
| jdl84c8g | Instructors | B | win | 71 | King capturable |
| aqzyafva | duck | W | win | 50 | King capturable |
| t8hdsxr0 | duck | W | win | 88 | King capturable |
| lunxd0co | duck | B | win | 117 | King capturable |
| d9vqv84q | Instructors | B | win | 85 | King capturable |
| 4br5r8qu | Instructors | W | win | 98 | King capturable |
| kvkg8fxe | Strongly Invisible | W | win | 128 | King capturable |
| y1uoh6g8 | duck | B | win | 131 | King capturable |
| jjid263w | duck | W | win | 130 | King capturable |
| 0v0oil9j | Instructors | W | win | 62 | King capturable |
| ktg7wuij | Decent Chess Bot | W | win | 60 | King capturable |
| zl06sde0 | Strongly Invisible | B | win | 91 | King capturable |
| vqfyyi7g | Decent Chess Bot | W | win | 64 | King capturable |
| lk81sakm | Decent Chess Bot | B | win | 71 | King capturable |
| wg9hsaag | Decent Chess Bot | W | win | 110 | King capturable |
| av0loozd | Decent Chess Bot | B | win | 59 | King capturable |
| mivspw22 | Decent Chess Bot | B | win | 59 | King capturable |
| 52t8q9yr | duck | W | win | 156 | King capturable |
| zrjhmj6f | Knight Vision | B | win | 73 | King capturable |
| 1bw9tnm0 | duck | W | win | 92 | King capturable |
| 5apiy1tf | duck | W | draw | 87 | Threefold repetition |
| h9qi8xf7 | duck | W | win | 120 | King capturable |
| qbvibbck | Instructors | W | win | 76 | King capturable |
| gy02xle3 | Instructors | W | win | 80 | King capturable |
| 5gtjvopn | Instructors | B | win | 93 | King capturable |
| wxh6u2lb | Decent Chess Bot | W | win | 44 | King capturable |
| 2cmvcbvt | Strongly Invisible | W | win | 110 | King capturable |
| 2lya5edo | Instructors | W | win | 114 | King capturable |
| tt47273g | Instructors | B | win | 223 | King capturable |
| 7ygtn99c | Knight Vision | W | win | 46 | King capturable |
| d4sz2q1x | Decent Chess Bot | B | win | 87 | King capturable |
| d8bqhzgc | Greek Gift | W | win | 76 | King capturable |
| ze166uj9 | Strongly Invisible | W | win | 82 | King capturable |
| vdl4xxwd | Knight Vision | W | win | 58 | King capturable |
| eb04kcv5 | duck | W | win | 108 | King capturable |
| 3qqd3840 | Greek Gift | W | win | 82 | King capturable |
| ghlgebbg | Greek Gift | B | win | 101 | King capturable |
| 8ss5e5oq | duck | B | win | 65 | King capturable |
| ok8ya1e4 | Greek Gift | B | win | 65 | King capturable |
| 8yeuv2hj | Instructors | B | win | 15 | King capturable |
| v2co32dr | Instructors | W | win | 124 | King capturable |
| 20333nwt | Decent Chess Bot | W | win | 102 | King capturable |
| shlqjtwf | Decent Chess Bot | W | win | 112 | King capturable |
| 4qn53ghq | duck | W | win | 68 | King capturable |
| zmrqqrfb | duck | B | draw | 108 | Threefold repetition |
| r5tyetop | Instructors | B | win | 79 | King capturable |
| pl7wfrfv | duck | W | win | 88 | King capturable |
| lpra8oqt | Strongly Invisible | B | draw | 137 | Threefold repetition |
| 5s44hks4 | Instructors | W | win | 68 | King capturable |
| g6l06b44 | Instructors | B | win | 73 | King capturable |
| jvfbkbgz | duck | B | draw | 109 | Threefold repetition |
| l5mgizwt | duck | W | win | 122 | King capturable |
| ofv65tqh | Strongly Invisible | W | win | 110 | King capturable |
| 3zwbho08 | Strongly Invisible | W | win | 122 | King capturable |
| jn1h7uok | Strongly Invisible | B | draw | 168 | Threefold repetition |
| vculmlsv | Strongly Invisible | W | win | 146 | King capturable |
| qau5g9sm | Instructors | B | win | 69 | King capturable |
| ncg8vomd | Instructors | W | win | 62 | King capturable |
| yh09xql0 | duck | W | win | 78 | King capturable |
| by95o001 | Greek Gift | W | win | 104 | King capturable |
| n7gcxyrx | Strongly Invisible | W | win | 118 | King capturable |
| 4ssfisiq | Knight Vision | W | win | 74 | King capturable |
| uuqelods | Strongly Invisible | W | draw | 88 | Threefold repetition |
| 9n4go49o | Knight Vision | B | win | 69 | King capturable |
| rf1umh2l | Decent Chess Bot | W | win | 70 | King capturable |
| juu74vbk | Decent Chess Bot | B | win | 109 | King capturable |
| 9x1k4qil | Instructors | W | win | 84 | King capturable |
| pqm6397v | Decent Chess Bot | W | win | 78 | King capturable |
| icacy6je | Instructors | W | win | 78 | King capturable |
| ehrxuwce | Instructors | W | win | 112 | King capturable |
| my9rjspv | Decent Chess Bot | B | win | 75 | King capturable |
| y7qo0l9m | Knight Vision | W | win | 78 | King capturable |
| 3209t0wv | Knight Vision | W | win | 42 | King capturable |
| vjq1qf2c | Instructors | W | win | 46 | King capturable |
| 6ofnluv6 | Strongly Invisible | W | win | 98 | King capturable |
| 5h9pjq2h | duck | W | win | 110 | King capturable |
| 0hcsdxou | duck | B | win | 41 | King capturable |
| boo4ip9x | duck | W | win | 118 | King capturable |
| b6ozs932 | Strongly Invisible | W | win | 100 | King capturable |
| 09a0qj4n | Strongly Invisible | W | win | 128 | King capturable |
| 6c8lnz43 | Instructors | W | win | 72 | King capturable |
| ys1hrxgx | Strongly Invisible | B | draw | 125 | Threefold repetition |
| j7bgl5ie | Strongly Invisible | W | win | 174 | King capturable |
| 159845hh | Instructors | B | win | 119 | King capturable |
| re04bny8 | Instructors | W | win | 180 | King capturable |
| 9fknpssd | Decent Chess Bot | W | win | 126 | King capturable |
| kivibo9y | Strongly Invisible | B | win | 79 | King capturable |
| elad4xpz | Knight Vision | B | win | 121 | King capturable |
| 7x7zn8yr | Strongly Invisible | W | win | 136 | King capturable |
| jkpgkjn2 | Knight Vision | B | win | 85 | King capturable |
| fv3vqb5k | Strongly Invisible | W | win | 208 | King capturable |
| tovtp2ma | Knight Vision | W | win | 122 | King capturable |
| j0zwhcns | Decent Chess Bot | W | win | 80 | King capturable |
| 2umem2si | Decent Chess Bot | B | win | 65 | King capturable |
| 12go0394 | Instructors | W | win | 66 | King capturable |
| f33ganaz | Knight Vision | W | win | 96 | King capturable |
| ubvqm07m | Instructors | W | win | 118 | King capturable |
| 8b6h32hj | duck | B | win | 43 | King capturable |
| 8ar2cctj | Instructors | B | win | 71 | King capturable |
| f514fhp2 | Strongly Invisible | W | win | 88 | King capturable |
| 62j1qwqt | duck | W | win | 102 | King capturable |
| asaotcye | Strongly Invisible | W | win | 94 | King capturable |
| 17l2yxch | Decent Chess Bot | W | win | 66 | King capturable |
| djq8wzvj | Decent Chess Bot | B | win | 95 | King capturable |
| cull0tx4 | Greek Gift | W | win | 62 | King capturable |
| nw10gmhi | Decent Chess Bot | B | win | 71 | King capturable |
| 05075o3l | Decent Chess Bot | W | win | 86 | King capturable |
| 4wgfn6f7 | Instructors | W | win | 18 | King capturable |
| s5unw9p3 | duck | B | draw | 75 | Threefold repetition |
| jkt745zs | Strongly Invisible | W | win | 100 | King capturable |
| bgmyzbsp | duck | W | win | 108 | King capturable |
| x02cdizq | Strongly Invisible | W | win | 134 | King capturable |
| 0sduem26 | duck | W | draw | 87 | Threefold repetition |
| v0vm2qt3 | Instructors | W | win | 78 | King capturable |
| ehzagj5g | Instructors | B | win | 79 | King capturable |
| 0v0y6ybc | duck | W | win | 8 | King capturable |
| tufbtbqy | Strongly Invisible | W | win | 76 | King capturable |
| 7yk8cq5a | Decent Chess Bot | B | win | 57 | King capturable |
| 30n31frc | Knight Vision | W | win | 76 | King capturable |
| d6lnpqu2 | Instructors | W | win | 66 | King capturable |
| gvzogv3b | Instructors | B | win | 103 | King capturable |
| kejxl3yn | Instructors | B | draw | 85 | Threefold repetition |
| ujjviu11 | Greek Gift | W | win | 76 | King capturable |
| fiwhvj7m | Instructors | B | win | 111 | King capturable |
| q6tmm8sr | Instructors | W | draw | 129 | Threefold repetition |
| 5jugvbrk | Decent Chess Bot | B | win | 41 | King capturable |
| iesjd5jf | Decent Chess Bot | W | win | 62 | King capturable |
| dme8g7hy | Decent Chess Bot | W | win | 80 | King capturable |
| k1ymdcr7 | Instructors | B | win | 91 | King capturable |
| uk30iysi | Instructors | W | win | 118 | King capturable |
| vd7uv2e7 | Decent Chess Bot | W | win | 174 | King capturable |
| yd2wnayc | Instructors | B | win | 85 | King capturable |
| q3u57i1o | Decent Chess Bot | B | win | 67 | King capturable |
| 2xoplx2s | Decent Chess Bot | W | win | 58 | King capturable |
| ifjbb2x6 | Decent Chess Bot | B | win | 63 | King capturable |
| ct031v3p | Strongly Invisible | W | draw | 119 | Threefold repetition |
| j513h1yo | Instructors | B | win | 59 | King capturable |
| wr6k1iym | Instructors | B | win | 75 | King capturable |
| 0p6u6k1x | Decent Chess Bot | W | win | 100 | King capturable |
| qq7gsdqj | duck | W | win | 64 | King capturable |
| aq5qocg9 | duck | B | win | 83 | King capturable |
| un6s0hnw | Knight Vision | W | win | 64 | King capturable |
| 1rs9rjn7 | duck | B | win | 131 | King capturable |
| 2bsbo5k0 | duck | W | win | 72 | King capturable |
| iq6rbk25 | Instructors | W | win | 32 | King capturable |
| kimltz3e | Strongly Invisible | W | win | 128 | King capturable |
| i8g35eue | duck | B | draw | 41 | Threefold repetition |
| 3h4s9kih | Knight Vision | B | win | 53 | King capturable |
| yvnu1g6t | Knight Vision | W | win | 92 | King capturable |
| e2unpjpe | Knight Vision | W | win | 46 | King capturable |
| n7sinzs0 | Strongly Invisible | B | win | 135 | King capturable |
| ce239fca | Instructors | W | win | 88 | King capturable |
| bkpr075s | Decent Chess Bot | W | win | 12 | King capturable |
| dc6trvy3 | duck | W | win | 96 | King capturable |
| s0lamelp | Instructors | B | win | 93 | King capturable |
| xp8ag0ud | duck | W | win | 94 | King capturable |
| oh1n7nim | Strongly Invisible | B | win | 187 | King capturable |
| fkmkq8ni | duck | B | draw | 83 | Threefold repetition |
| pbdpoqq3 | Strongly Invisible | W | win | 114 | King capturable |
| 7pxgx8do | Knight Vision | B | win | 67 | King capturable |
| njl0wlst | Greek Gift | W | draw | 96 | Threefold repetition |
| m9500yjd | Decent Chess Bot | B | win | 51 | King capturable |
| ypcjdqwn | Decent Chess Bot | W | win | 110 | King capturable |
| tdjcwsl3 | Decent Chess Bot | B | win | 201 | King capturable |
| hzd079mt | Knight Vision | B | win | 51 | King capturable |
| 72fq0a61 | Knight Vision | W | draw | 99 | Threefold repetition |
| ei81nkpw | Instructors | B | win | 103 | King capturable |
| umbcc28b | Instructors | B | win | 65 | King capturable |
| vb5fa5q7 | Knight Vision | W | win | 112 | King capturable |
| yf2nr3u5 | Instructors | W | win | 98 | King capturable |
| fnp71d38 | duck | W | win | 80 | King capturable |
| zuvd7gg3 | Instructors | W | win | 20 | King capturable |
| zf89o28w | Instructors | W | win | 60 | King capturable |
| 67gwt4eh | Instructors | B | win | 117 | King capturable |
| n46auoxd | Strongly Invisible | B | win | 105 | King capturable |
| l2xc0oy6 | Strongly Invisible | W | win | 296 | King capturable |
| 6y1bblta | Knight Vision | B | win | 49 | King capturable |
| u5v4dawa | Knight Vision | W | win | 52 | King capturable |
| popzngym | Decent Chess Bot | W | win | 66 | King capturable |
| g07mcmqm | duck | B | win | 77 | King capturable |
| x17uxtxt | Decent Chess Bot | B | draw | 150 | Threefold repetition |
| au5rgqor | Instructors | B | win | 91 | King capturable |
| bstqcp7s | Strongly Invisible | W | win | 78 | King capturable |
| 4p9h30va | Instructors | B | win | 65 | King capturable |
| m8nx4fer | Greek Gift | W | win | 58 | King capturable |
| vn0upfpr | Knight Vision | W | win | 26 | King capturable |
| tqmk1bi4 | Knight Vision | W | win | 86 | King capturable |
| oall9epp | Strongly Invisible | W | win | 58 | King capturable |
| m578sdp1 | duck | W | win | 116 | King capturable |
| llbxxzvz | duck | W | win | 64 | King capturable |
| ci907b4x | duck | B | win | 57 | King capturable |
| wkz9aa28 | duck | W | win | 116 | King capturable |
| pnd80tla | Instructors | B | win | 109 | King capturable |
| tmthgctn | Decent Chess Bot | W | draw | 89 | Threefold repetition |
| ucjj4u7y | Instructors | B | win | 113 | King capturable |
| 9h7lfdi5 | Strongly Invisible | W | win | 144 | King capturable |
| h9tf2uml | Decent Chess Bot | W | win | 194 | King capturable |
| b3s6tt7g | Instructors | W | win | 130 | King capturable |
| 1j4arlde | Decent Chess Bot | W | win | 54 | King capturable |
| 8f70t1cm | Instructors | W | draw | 68 | Threefold repetition |
| xuah64ng | Strongly Invisible | W | win | 170 | King capturable |
| ki9udwsy | Decent Chess Bot | B | win | 57 | King capturable |
| ymflsqoq | duck | B | draw | 173 | 50-move rule |
| a9nkerbp | Instructors | B | win | 73 | King capturable |
| ure0s5lc | Instructors | W | win | 100 | King capturable |
| qecl95ka | duck | W | win | 98 | King capturable |
| qlg4bmdy | duck | B | win | 97 | King capturable |
| 7qo0agqp | Decent Chess Bot | W | win | 30 | King capturable |
| ts91v5o3 | Knight Vision | W | win | 90 | King capturable |
| twki8vgr | Instructors | B | draw | 99 | Threefold repetition |
| pskfz2nl | Instructors | W | win | 88 | King capturable |
| 3c8wamdc | Decent Chess Bot | B | win | 77 | King capturable |
| 0h20kiob | Instructors | W | win | 46 | King capturable |
| ybnccp3x | Instructors | B | win | 95 | King capturable |
| 3wy5f34p | Strongly Invisible | W | draw | 174 | Threefold repetition |
| d8bjsdze | duck | B | win | 93 | King capturable |
| iiaif3tp | duck | W | win | 132 | King capturable |
| m8we5adn | duck | B | win | 91 | King capturable |
| zk1i823q | Strongly Invisible | B | draw | 70 | Threefold repetition |
| 0984fjbv | duck | B | draw | 88 | Threefold repetition |
| amiqx8z7 | Knight Vision | W | win | 70 | King capturable |
| fnc5lkwg | Knight Vision | B | win | 61 | King capturable |
| 6ic78jks | duck | W | win | 52 | King capturable |
| q18slmo1 | duck | W | win | 136 | King capturable |
| 41ot791h | duck | W | win | 86 | King capturable |
| xcg7t8b3 | Decent Chess Bot | B | win | 75 | King capturable |
| mdzvqmrr | Knight Vision | B | win | 61 | King capturable |
| hwuw5wby | duck | B | win | 79 | King capturable |
| ucqyudjj | duck | W | win | 76 | King capturable |
| wuqzptf7 | Decent Chess Bot | W | win | 64 | King capturable |
| hg6adbr0 | Decent Chess Bot | W | win | 98 | King capturable |
| l8ci9nkc | Strongly Invisible | B | win | 29 | King capturable |
| zos4u4rg | duck | W | win | 74 | King capturable |
| yhrbiitd | Strongly Invisible | B | win | 111 | King capturable |
| nogzqufd | Decent Chess Bot | W | win | 96 | King capturable |
| z066fatv | Decent Chess Bot | B | win | 141 | King capturable |
| vpj9kl6v | Decent Chess Bot | W | win | 110 | King capturable |
| z4mhsc4a | duck | W | win | 86 | King capturable |
| cqyr3uc4 | duck | B | win | 89 | King capturable |
| 516tinmb | duck | W | win | 98 | King capturable |
| leu2i87w | duck | B | win | 119 | King capturable |
| mcu406vc | duck | W | draw | 87 | Threefold repetition |
| dezegx10 | duck | B | win | 89 | King capturable |
| 25co98pw | Instructors | B | win | 101 | King capturable |
| 0nuvuziu | duck | W | win | 8 | King capturable |
| 4pjqoty6 | Knight Vision | B | win | 123 | King capturable |
| ba8sdgf8 | Instructors | B | win | 39 | King capturable |
| fpcqcmcu | Instructors | W | win | 76 | King capturable |
| ndjxbeqv | Instructors | W | win | 80 | King capturable |
| zfxiib9k | Knight Vision | B | win | 57 | King capturable |
| 3lpcbccm | duck | W | win | 76 | King capturable |
| 8iep38bb | duck | B | win | 115 | King capturable |
| 7jv8n5e6 | duck | W | win | 78 | King capturable |
| kf3vvlbw | Strongly Invisible | B | win | 101 | King capturable |
| ek7qjgfn | Knight Vision | B | win | 91 | King capturable |
| gs5w1dym | Decent Chess Bot | W | win | 152 | King capturable |
| othgy82l | Decent Chess Bot | W | win | 98 | King capturable |
| o81jf1io | Decent Chess Bot | B | win | 103 | King capturable |
| mwgwintk | duck | B | draw | 87 | Threefold repetition |
| 6jetf2qu | Decent Chess Bot | W | win | 64 | King capturable |
| 9ulpnpuo | duck | W | win | 114 | King capturable |
| q5bdp60a | Instructors | B | win | 61 | King capturable |
| z51xw9y7 | duck | B | win | 117 | King capturable |
| kjyd7sk9 | duck | W | win | 152 | King capturable |
| n329277r | Instructors | W | win | 60 | King capturable |
| 9wr3xlko | Instructors | W | win | 26 | King capturable |
| va76qs88 | Greek Gift | W | win | 74 | King capturable |
| vucmwgcb | duck | W | win | 60 | King capturable |
| 98p9wslf | Knight Vision | W | win | 48 | King capturable |
| sxb9ze92 | Decent Chess Bot | W | win | 164 | King capturable |
| gjsx4r4m | Strongly Invisible | B | win | 171 | King capturable |
| tgkn1stk | Instructors | W | win | 88 | King capturable |
| 526dfqd6 | Instructors | W | win | 62 | King capturable |
| misvwe86 | Instructors | W | win | 56 | King capturable |
| crkyry8i | duck | W | win | 98 | King capturable |
| 4iyotry1 | duck | B | win | 235 | King capturable |
| op0kdwzz | Strongly Invisible | W | win | 78 | King capturable |
| s94sv0nr | Knight Vision | W | win | 26 | King capturable |
| qip9uh8t | Knight Vision | B | win | 43 | King capturable |
| p3s5w5so | Strongly Invisible | B | win | 127 | King capturable |
| ccgnfqs3 | Decent Chess Bot | W | win | 84 | King capturable |
| 7ca7y0c6 | Decent Chess Bot | W | win | 50 | King capturable |
| k6nn45zs | Instructors | W | win | 74 | King capturable |
| hhsbfkkt | Instructors | B | win | 107 | King capturable |
| dua0z1yy | Strongly Invisible | B | win | 45 | King capturable |
| ms6ig69r | duck | W | win | 116 | King capturable |
| slfzhb3y | Instructors | W | win | 52 | King capturable |
| 6374ptbr | Decent Chess Bot | W | win | 24 | King capturable |
| k5vtenyo | duck | B | win | 91 | King capturable |
| cnolbfaf | Instructors | B | win | 89 | King capturable |
| r6awbpei | Knight Vision | W | win | 90 | King capturable |
| 1jn4585c | duck | B | win | 119 | King capturable |
| 828fihky | duck | W | win | 118 | King capturable |
| nghg5ifb | Instructors | W | win | 82 | King capturable |
| viz4fd6z | Decent Chess Bot | W | win | 100 | King capturable |
| 950bbjwv | Decent Chess Bot | B | draw | 116 | Threefold repetition |
| ief8m6gz | Decent Chess Bot | B | win | 57 | King capturable |
| ib4vs1ur | Instructors | W | win | 80 | King capturable |
| 6qv1cg0r | Instructors | B | win | 155 | King capturable |
| 8luv4pat | Decent Chess Bot | W | win | 34 | King capturable |
| 54nfej4k | Greek Gift | W | draw | 166 | Threefold repetition |
| al78092u | Instructors | W | win | 136 | King capturable |
| zyjxcqvr | Knight Vision | B | win | 53 | King capturable |
| q2dhcva0 | duck | W | win | 92 | King capturable |
| 9drm8ney | duck | B | draw | 242 | Threefold repetition |
| v44fww9w | Knight Vision | B | win | 77 | King capturable |
| uzz23ir3 | Knight Vision | W | win | 58 | King capturable |
| h9nssngl | Knight Vision | B | win | 63 | King capturable |
| 3tjso19d | Instructors | W | win | 18 | King capturable |
| 1suvllpf | duck | W | win | 70 | King capturable |
| i62y882f | Knight Vision | W | draw | 165 | Threefold repetition |
| xkahz9fl | Decent Chess Bot | B | win | 95 | King capturable |
| 8sg30ddo | Instructors | W | win | 68 | King capturable |
| d4lamn80 | Instructors | W | win | 60 | King capturable |
| 7vdnz2wj | Knight Vision | B | win | 85 | King capturable |
| 8sj5as0f | Decent Chess Bot | W | win | 74 | King capturable |
| nyptqlu2 | Instructors | B | win | 101 | King capturable |
| 1ar1wsry | Instructors | W | win | 74 | King capturable |
| 2jyhhdk0 | Strongly Invisible | B | win | 67 | King capturable |
| fv2fvtt4 | duck | B | win | 105 | King capturable |
| lb7uvtkg | duck | W | win | 104 | King capturable |
| 0wps0i67 | Decent Chess Bot | B | win | 69 | King capturable |
| zyv58iog | Instructors | W | win | 144 | King capturable |
| 67r6tisj | Instructors | W | win | 126 | King capturable |
| kzvcs09y | Decent Chess Bot | B | win | 195 | King capturable |
| 9hb4zepx | Instructors | B | win | 69 | King capturable |
| etymww9a | Instructors | W | win | 80 | King capturable |
| i7fwtcm3 | Greek Gift | W | win | 134 | King capturable |
| g3lvi6w1 | duck | W | draw | 82 | Threefold repetition |
| 051wq5wz | Instructors | W | win | 82 | King capturable |
| 93cqvq1n | Instructors | W | win | 86 | King capturable |
| uxoufms0 | Instructors | W | win | 92 | King capturable |
| sohb38ra | Strongly Invisible | W | win | 80 | King capturable |
| qohe11fi | Strongly Invisible | W | win | 102 | King capturable |
| dp6tolua | Strongly Invisible | B | win | 143 | King capturable |
| 016hvi0s | Instructors | W | win | 54 | King capturable |
| x0wna7qc | duck | W | win | 58 | King capturable |
| l0e6sovq | Strongly Invisible | B | win | 137 | King capturable |
| gaggusk5 | Strongly Invisible | W | win | 170 | King capturable |
| h8877my4 | Strongly Invisible | B | win | 101 | King capturable |
| juvk6ttu | duck | W | win | 62 | King capturable |
| zypemd15 | duck | W | win | 136 | King capturable |
| tct6y98h | Instructors | B | win | 91 | King capturable |
| rydj1xkk | Decent Chess Bot | W | draw | 96 | Threefold repetition |
| mrq1xwze | Decent Chess Bot | B | win | 89 | King capturable |
| bo3kd3x4 | duck | W | win | 150 | King capturable |
| xjd3ylbc | Instructors | W | win | 72 | King capturable |
| icefx9mu | Decent Chess Bot | B | win | 109 | King capturable |
| sjaxwp5n | Instructors | W | win | 86 | King capturable |
| ptud41g5 | Instructors | B | win | 95 | King capturable |
| ouslt082 | Decent Chess Bot | W | win | 62 | King capturable |
| macarpbu | Knight Vision | B | win | 109 | King capturable |
| jq8xl4ne | Instructors | W | win | 64 | King capturable |
| 3ndpr6ac | duck | B | win | 143 | King capturable |
| gyul4js6 | duck | W | draw | 219 | 50-move rule |
| cmp4yp68 | Instructors | B | win | 99 | King capturable |
| pz7wdamq | Greek Gift | W | win | 86 | King capturable |
| erewgwn5 | Instructors | B | win | 61 | King capturable |
| 1ripbhsp | Strongly Invisible | B | draw | 67 | Threefold repetition |
| zjwwsut3 | Strongly Invisible | W | draw | 91 | Threefold repetition |
| gl3zt99m | duck | W | win | 84 | King capturable |
| vuot298k | Knight Vision | W | win | 26 | King capturable |
| jf0nuf8k | Knight Vision | B | win | 49 | King capturable |
| 9crcnslv | Strongly Invisible | W | win | 96 | King capturable |
| 8ebwaohv | Strongly Invisible | B | win | 111 | King capturable |
| kyig8j11 | Strongly Invisible | W | draw | 176 | Threefold repetition |
| zititywx | Knight Vision | W | win | 88 | King capturable |
| 8q5bt1q2 | Knight Vision | W | win | 114 | King capturable |
| cx6qmyi6 | Knight Vision | B | win | 117 | King capturable |
| muocyinh | Knight Vision | B | win | 47 | King capturable |
| if7i6fql | Strongly Invisible | W | win | 130 | King capturable |
| rvu5w64z | Decent Chess Bot | W | win | 74 | King capturable |
| 13p3mu7r | Decent Chess Bot | B | win | 73 | King capturable |
| nxpmc1cc | Decent Chess Bot | W | win | 80 | King capturable |
| cjfj5goc | Instructors | B | win | 93 | King capturable |
| 5n9pofe6 | Decent Chess Bot | W | win | 32 | King capturable |
| m8uvds22 | Decent Chess Bot | B | win | 65 | King capturable |
| a4h8jpk5 | Knight Vision | B | win | 69 | King capturable |
| jl2d10fo | Decent Chess Bot | W | draw | 135 | Threefold repetition |
| 6g368oel | Knight Vision | B | win | 141 | King capturable |
| e856pwwn | Instructors | W | win | 76 | King capturable |
| cn3deiu5 | duck | B | win | 91 | King capturable |
| o1ffzrl8 | duck | W | win | 130 | King capturable |
| mh9w2ogg | Knight Vision | B | win | 65 | King capturable |
| 7k2tx913 | Knight Vision | W | win | 48 | King capturable |
| a286rzxg | Strongly Invisible | W | win | 116 | King capturable |
| 0tia3uhc | Instructors | W | win | 123 | Time forfeit |
| 0ii2vpqa | Decent Chess Bot | B | draw | 146 | Threefold repetition |
| ztb69acp | Strongly Invisible | B | win | 33 | King capturable |
| 59uai2m1 | Strongly Invisible | W | win | 72 | King capturable |
| yyhwmexm | duck | W | win | 82 | King capturable |
| umnfjemu | duck | W | win | 46 | King capturable |
| 1kh026bp | Knight Vision | W | win | 26 | King capturable |
| b358aurf | Greek Gift | W | draw | 147 | Threefold repetition |
| n34rbt9b | Knight Vision | B | win | 71 | King capturable |
| 4686pjt2 | Decent Chess Bot | W | draw | 105 | Threefold repetition |
| djsktugc | Instructors | B | win | 67 | King capturable |
| 8eq03f4n | Instructors | W | win | 120 | King capturable |
| dlw8zkzk | duck | W | draw | 137 | Threefold repetition |
| o9gvtm0j | duck | W | win | 72 | King capturable |
| qj63b5si | Instructors | W | win | 40 | King capturable |
| iomn0jo4 | Instructors | B | win | 69 | King capturable |
| 8xkmxo06 | duck | W | win | 210 | King capturable |
| 0vorvtqu | Instructors | W | win | 60 | King capturable |
| rllwi9he | Instructors | B | win | 107 | King capturable |
| oyd18pqb | Knight Vision | W | draw | 99 | Threefold repetition |
| pxe2svgz | Decent Chess Bot | W | win | 54 | King capturable |
| fvm3hlpo | Strongly Invisible | W | win | 132 | King capturable |
| vhlpg4p0 | Strongly Invisible | W | win | 134 | King capturable |
| 8itgeiq8 | Decent Chess Bot | B | win | 139 | King capturable |
| r5w5x50h | Instructors | W | win | 64 | King capturable |
| ha9ij18f | Instructors | W | draw | 97 | Threefold repetition |
| 1l1oghxk | Knight Vision | B | win | 25 | King capturable |
| kbbytl8z | Knight Vision | B | win | 69 | King capturable |
| e3hl3jps | Instructors | W | win | 116 | King capturable |
| 3cysx93d | Instructors | B | win | 139 | King capturable |
| eij4b7v0 | Instructors | W | win | 74 | King capturable |
| p4zojt92 | duck | W | win | 82 | King capturable |
| fv5sxd2h | Decent Chess Bot | W | win | 88 | King capturable |
| 3x6wlo77 | Knight Vision | W | win | 74 | King capturable |
| seq7ww3x | Instructors | B | win | 187 | King capturable |
| 1xltzon2 | duck | W | win | 80 | King capturable |
| g0lopzcl | Knight Vision | W | win | 90 | King capturable |
| tpoissax | Instructors | W | win | 62 | King capturable |
| murtq3i8 | Instructors | B | win | 91 | King capturable |
| 46kqofup | Decent Chess Bot | W | win | 86 | King capturable |
| am5xb6we | Strongly Invisible | B | win | 75 | King capturable |
| pcnd5p4u | Strongly Invisible | W | draw | 79 | Threefold repetition |
| 5ckt1155 | Decent Chess Bot | W | win | 64 | King capturable |
| un0myntu | Instructors | W | win | 42 | King capturable |
| 62m7cm45 | Knight Vision | W | win | 80 | King capturable |
| ei2uq9d4 | Instructors | B | win | 89 | King capturable |
| zp6hs0fx | Instructors | W | win | 106 | King capturable |
| 9p292ou8 | Instructors | W | win | 56 | King capturable |
| u00npp7e | Knight Vision | W | win | 78 | King capturable |
| hu1vo2hh | Knight Vision | B | win | 105 | King capturable |
| 4rx57e69 | Knight Vision | B | draw | 139 | Threefold repetition |
| dg34qij7 | Knight Vision | W | win | 58 | King capturable |
| niakc4fa | Decent Chess Bot | W | win | 62 | King capturable |
| m6d5ht9q | duck | B | win | 91 | King capturable |
| q9k94nhv | Knight Vision | W | win | 94 | King capturable |
| 5gl3g4kr | Instructors | W | draw | 74 | Threefold repetition |
| 9hs1w1yk | Instructors | B | win | 95 | King capturable |
| oa2xei95 | Instructors | W | win | 44 | King capturable |
| sikx13nb | Strongly Invisible | W | draw | 97 | Threefold repetition |
| bw1kh83w | duck | B | win | 77 | King capturable |
| w5sawfx0 | Instructors | B | win | 83 | King capturable |
| x78n5tro | duck | W | win | 70 | King capturable |
| 6oj54tr5 | Instructors | B | win | 63 | King capturable |
| m1ouo6zl | Strongly Invisible | W | win | 80 | King capturable |
| 3nvd0qnz | Strongly Invisible | B | win | 99 | King capturable |
| n3ph5l3g | Strongly Invisible | B | win | 107 | King capturable |
| zrevqe47 | Strongly Invisible | W | win | 128 | King capturable |
| 1lt6b3dw | Instructors | W | win | 90 | King capturable |
| 27s14it7 | duck | W | win | 52 | King capturable |
| kjnfdff3 | duck | B | win | 83 | King capturable |
| y966j3kx | Strongly Invisible | B | draw | 138 | Threefold repetition |
| t1f90wdn | duck | W | win | 70 | King capturable |
| qp1a1yap | duck | B | win | 115 | King capturable |
| cgbliuic | Decent Chess Bot | W | win | 64 | King capturable |
| ha4c8wza | Decent Chess Bot | W | win | 48 | King capturable |
| 0qv50oad | Decent Chess Bot | B | win | 95 | King capturable |
| glp2tv7e | Decent Chess Bot | B | win | 95 | King capturable |
| oqgiwbv1 | Knight Vision | W | win | 96 | King capturable |
| a30u8x43 | Decent Chess Bot | W | win | 90 | King capturable |
| te4zglc9 | Decent Chess Bot | B | win | 103 | King capturable |
| xyqixjvm | Instructors | W | win | 104 | King capturable |
| lzxn1m21 | duck | W | win | 150 | King capturable |
| nr8v8ok8 | Instructors | W | win | 94 | King capturable |
| f0rtgyv2 | Instructors | B | win | 71 | King capturable |
| qcwe5nld | duck | B | win | 141 | King capturable |
| dk44ut3i | Strongly Invisible | W | win | 48 | King capturable |
| 4zgn38hs | Decent Chess Bot | W | win | 58 | King capturable |
| ke251uw4 | Strongly Invisible | W | win | 106 | King capturable |
| mduxyion | Decent Chess Bot | W | win | 62 | King capturable |
| ceqry62d | Greek Gift | B | win | 111 | King capturable |
| qiprqpxy | Decent Chess Bot | B | win | 31 | King capturable |
| yb5tsjt5 | Decent Chess Bot | W | win | 40 | King capturable |
| jopwro24 | Knight Vision | W | win | 50 | King capturable |
| jiju435x | Strongly Invisible | W | win | 116 | King capturable |
| 95mskkfl | Strongly Invisible | B | win | 133 | King capturable |
| i2h41zve | duck | B | win | 75 | King capturable |
| 0fwxw3jb | duck | B | win | 211 | King capturable |
| myunanvx | duck | B | win | 99 | King capturable |
| g5mnpzlr | Instructors | W | win | 78 | King capturable |
| gr53prfe | Strongly Invisible | B | win | 67 | King capturable |
| y186dhju | duck | W | win | 104 | King capturable |
| s9skutxc | Strongly Invisible | B | win | 79 | King capturable |
| k6j76vsx | Strongly Invisible | W | win | 100 | King capturable |
| z11jzve2 | Decent Chess Bot | B | win | 67 | King capturable |
| v2j4o3m4 | Decent Chess Bot | B | win | 75 | King capturable |
| oqq27gnx | Instructors | W | win | 40 | King capturable |
| iww71x72 | Instructors | B | win | 189 | King capturable |
| rgh7clws | duck | W | win | 80 | King capturable |
| 0z2j5at4 | Instructors | B | win | 23 | King capturable |
| 45ik5gnx | Instructors | B | win | 77 | King capturable |
| bkbu0xb9 | Instructors | W | win | 52 | King capturable |
| u1ka4mqj | Knight Vision | W | win | 78 | King capturable |
| yaylkh1u | Decent Chess Bot | W | win | 70 | King capturable |
| 37z49rhq | Instructors | W | win | 68 | King capturable |
| jfopo459 | Decent Chess Bot | W | win | 38 | King capturable |
| nuujnvk7 | Decent Chess Bot | B | win | 65 | King capturable |
| 6dhcwbfw | Decent Chess Bot | B | win | 43 | King capturable |
| g46b8lan | Greek Gift | W | win | 300 | King capturable |
| bbg6ue7i | duck | B | win | 53 | King capturable |
| a2g0i27y | Instructors | W | win | 24 | King capturable |
| y8pf7bk7 | Decent Chess Bot | W | win | 56 | King capturable |
| xafbl0yq | Knight Vision | B | draw | 148 | Threefold repetition |
| hgy9dhs8 | Instructors | W | win | 106 | King capturable |
| 1pw9563x | Decent Chess Bot | W | win | 128 | King capturable |
| cf79o53w | Instructors | B | win | 91 | King capturable |
| p3tj3jm1 | duck | B | draw | 128 | Threefold repetition |
| cxk8pfll | Knight Vision | W | win | 44 | King capturable |
| fa8kozja | duck | W | win | 86 | King capturable |
| xm161mxw | Strongly Invisible | W | draw | 116 | Threefold repetition |
| bc6fcpdc | Knight Vision | W | win | 92 | King capturable |
| nczjn5bl | Knight Vision | W | win | 76 | King capturable |
| bv69xksk | duck | W | draw | 123 | Threefold repetition |
| g3b6i6g8 | Decent Chess Bot | W | draw | 84 | Threefold repetition |
| 5bg6n0j9 | Instructors | B | win | 83 | King capturable |
| ps9cogil | Instructors | W | win | 102 | King capturable |
| gobn95o6 | Strongly Invisible | W | win | 124 | King capturable |
