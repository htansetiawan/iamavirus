# 030 — Why we lose to duck (Fable, 2026-10-10 00:20 UTC)

**Short answer.** duck beats us the same way it beats the TA baselines, and the top five beat duck the same way duck beats us. Our king dies to a queen or rook we cannot see. By then duck's queen is in our half and the pawns in front of our king are broken. Against duck we are **passive** (half the top five's attacks on duck's king) and **leaky** (twice the material given away).

## The record

- 142 games against duck since v4: **11 W, 5 D, 126 L**.
- The current engine, v20 + v21 (same bytes): 4–3–17 (score 0.23). v18 went 0–0–4.
- duck against everyone (3,431 games in our mirror):
  - Against the TA baselines it scores 0.79 to 0.93, and against us 0.90. So against duck we play like a TA baseline.
  - Against the top five it scores far less: Greek Gift 0.16, Knight Vision 0.29, Strongly Invisible 0.32, Decent Chess Bot 0.33, Instructors 0.44.

## How our king falls (all 126 losses to duck)

| ending | losses |
| --- | --- |
| our king walked onto a square an unseen piece attacks | 43 |
| ...by capturing a piece offered next to it (bait) | 30 |
| king already attacked by an unseen piece | 41 |
| a visible attacker, no escape | 8 |
| our own move opened a line | 4 |

- Pieces that took our king: queen 51, rook 36, bishop 24, knight 9.
- The pawns in front of our king just before the end: broken in 77 losses (one gone, open file, or pushed). The king had walked out in 24. Intact or central in 25.

## What the top five do against duck that we do not

Rates are per 100 moves. "Us" is 28 games from v18 to v21; "top five" is 300 recent games.

| | us vs duck | top five vs duck | duck vs us | duck vs top five |
| --- | --- | --- | --- | --- |
| moves that attack the enemy king | **2.2** | **4.1** | 3.7 | 3.1 |
| ...from a square the king's side cannot see | 1.3 | 2.0 | 2.1 | 1.4 |
| queen moves into the enemy half | **1.4** | 3.8 | **5.8** | 2.8 |
| material given away (3+ net) | **2.7** | 1.4 | 1.6 | 2.2 |
| pieces walked onto squares an unseen piece attacks | 3.5 | 2.3 | 2.1 | 3.3 |
| queen left to an unseen attacker | 0.39 | 0.22 | 0.24 | 0.10 |
| captures from unseen squares | 7.4 | 8.8 | 10.5 | 8.5 |

- duck's queen raids our half four times as often as our queen raids its half. Against the top five it raids only half as often as against us.
- duck's own king dies the same way. In its 1,528 losses the killer was the queen in 50% and a rook in 34%, and 80% were attackers duck could not see.
- So the top five beat duck with the very weapon duck uses on us.

## The engine-level leak (v20 to v23: 388 games, 189 losses)

- **79% of our losses end on our own king move.**
- Our king steps, with no visible attacker, onto a square with 2 or more open lines into the fog. It is captured on the next ply **93 times in 850 (10.9%)**. With 1 open line: 4 in 255. With none: 0 in 637.
- At those final moves the engine already rated every move 6–90% risky (gym, note 020). The king was really lost a few moves earlier, when the shelter broke and duck's queen got into our half. **The fix is upstream, not a veto on the last move.**

## Four replays

- **`dosrwd6j` (v20).** duck sacrifices its queen, Qxf7+. Our king takes it (+9). The rook on f1, behind an f-file we cannot see at all, takes our king.
- **`ixkh3osi` (v21).** We were 7 points up. At ply 28 we had moved our king to f8. duck's knight takes on h6, which uncovers its hidden queen on f3 along the open f-file.
- **`hsao7413` (v21).** Even endgame. duck sacrifices a rook on b8 to deflect ours (we take, Rxb8). A passed pawn on a7 that we cannot see promotes, axb8=Q, and the new queen hunts our king.
- **v23's loss to Instructors (`9m7i1b0d`).** The same bait. Our king took the h2 pawn while a hidden bishop on d6 covered h2; Kg1 was safe.

Also: **the local duck replica overrates us.** v20 scored 0.77 against it but 0.23 against the real duck. Our gates cannot see duck's traps.

## What to do (cheapest first)

1. **Track the queen.** King fusion found the hidden enemy king 3x better than the particles. Run the same fusion for the enemy queen, measuring with `belief_eval` first (minutes).
2. **Close the lines early.** Add an evaluation term for open lines from the fog into our king's zone, scaled by the enemy sliders still alive. That way we keep the pawn shelter and the f-file closed before the king is trapped.
3. **The bait rule.** Our king capturing a piece that just arrived next to it, with an open fog line onto that square, dies 26–36% of the time. Charge it that rate unless every alternative is worse.
4. **Take the initiative.** Against duck the top five attack the king twice as often as we do and raid with the queen. duck's king falls to those strikes from the fog just as ours does.
5. **A real duck gate.** Replay positions from the 126 real duck losses, not the replica.
