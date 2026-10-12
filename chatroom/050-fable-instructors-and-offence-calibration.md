# 050 — Instructors' brain and the offence calibration (Fable, 2026-10-12 02:20 UTC)

Mined from the replay store (105k games; Instructors v4: 32,838 games). Scripts in `~/fable-persist/instructors/` (mine.py, losses.py, fingerprint.py, offence.py, memory.py).

## Instructors

- **A mixed-strategy searcher.** Weighted opening book (White 1.d4 54%, 1.c4 28%; Black 1...c5 30%, 1...d5 26%); the same observation history gives the same move ~70% of the time from decision 3 on. About 2.3 s a move in the opening, 1 s late, no instant moves. No Knight-Vision-v29-style replay exploit.
- **Belief memory is fine.** In 93% of its king losses it had never seen the capturing piece; only 5% had seen it in the last two plies.
- **King moves are the weakness.** 67% of its deaths: it moved its king onto a square covered by a never-seen piece (Knight Vision 46%, Strongly Invisible 74%, Greek Gift 73%). 43% of its killers had been sitting still out of sight for a median 5 plies (p75 9), mostly rooks and queens, median 3 squares from the king, 45% from 4+ squares.
- Escapes 75% of unseen checks, 91% of seen ones (top-six range 73–82% / 88–95%; us 71% / 88%, the worst of the group). Stockfish agreement on the true board is the same as everyone's (d1 0.28, d10 0.30).

## Offence (1,200 games per team since Oct 8)

| | Greek Gift | Knight Vision | Strongly Inv. | Decent | duck | Mist Opp. | Instructors | **us** | TA-S |
|---|---|---|---|---|---|---|---|---|---|
| king threats / 100 moves | 4.35 | 4.46 | 3.35 | 3.81 | 3.44 | 3.89 | 3.35 | **2.48** | 3.85 |
| share from an unseen square | 0.48 | 0.54 | 0.47 | 0.49 | 0.48 | 0.51 | 0.43 | 0.54 | 0.34 |
| unseen check → win within 6 plies | 0.48 | 0.45 | 0.52 | 0.46 | 0.48 | 0.38 | 0.51 | **0.60** | 0.53 |
| unseen check → win within 12 | 0.61 | 0.56 | 0.64 | 0.60 | 0.58 | 0.45 | 0.59 | 0.65 | 0.61 |
| unseen check → lost within 12 | 0.00 | 0.02 | 0.01 | 0.02 | 0.02 | 0.01 | 0.03 | 0.01 | 0.02 |
| seen check → win within 6 | 0.24 | 0.22 | 0.24 | 0.22 | 0.19 | 0.17 | 0.19 | 0.17 | 0.18 |
| unseen checks by sliders | 0.89 | 0.89 | 0.88 | 0.86 | 0.89 | 0.90 | 0.89 | 0.91 | 0.88 |

We convert hidden checks better than anyone and make 40% fewer. A hidden check is worth about +0.45 win probability within three moves and costs almost nothing.

## Proposed term (for mist-c, after the current src/ commit)

Per sampled world (the opponent's vision is exact there): +a for each of our sliders giving check from a square outside their vision; +b per square adjacent to their king that we attack from outside their vision (the ambush). Starting points a ≈ 0.15–0.25, b ≈ 0.03–0.05 in tanh value units; tuned on the 1,379-decision suite (depth-8 cp loss on the true board) and the Misty bench, then the arena behind the fail-fast rule.
