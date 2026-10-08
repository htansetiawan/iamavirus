# 014 — Fable, night of 2026-10-08 (01:30–04:10 UTC): clock schedule, queen-loss corpus, model lanes, recommendation

For the user and Astra. Everything below is measured; the commands and files are named so it can be re-run.

## 1. Recommendation for the morning

Upload `fable-submissions/iamavirus-v11-candidate-caution-r10c-hybrid.zip` (sha `2ae7ee3c6cce`) as the next arena version and activate it. It replaces the cleared v14 candidate (`93f4ccdf03d5`): same engine, same v1 model, one change — the opening book samples among the strongest teams' moves by frequency instead of playing one fixed ten-ply line as each colour.

Evidence chain: caution engine vs v13 bytes 12–1–3 over 16 (paired 0.781); the v14 bytes' smoke vs v13 2.5/4; r10c vs the v14 bytes 5–0–3 over 8 (paired 0.625, 0.25–1.0), games 68–166 plies, no overruns, final clocks ≥ 31 s. After upload: rename the file to the arena number and update the map in `fable-submissions/README.md`; one upload per ~40 games.

## 2. Arena and the clock

- v13 finished 47–7–58 after 112 games; the user reactivated v10 at about 03:15 UTC (v10 now 80–2–73).
- The arena control is 180 s + 2 s. v13's real spend per decision matches the engine's `TimeBudget` with `increment_share` 0.8 to within 0.1 s, so clock schedules can be simulated exactly.
- v13 reached a clock of 15 s or less in 20 of 107 games (v10: 0 of 144); its win rate by length vs v10: under 60 plies 82% / 79%, 60–89 36% / 28%, 90–119 22% / 32%, 120+ 25% / 22% — the long-game gap is inside noise at these counts.
- A two-phase schedule (cap 7 / divisor 20 for 20 decisions, then cap 5 / divisor 30) was implemented (`85169e1`) and withdrawn before its smoke: with the book answering five decisions it banks clock without buying late thinking (budget at decision 45 is 3.4 s either way; decisions 21–40 lose ~15 s). Root keeps it off (`166da52`, `late_move = 0`). The floor of any schedule here is reserve + 0.4 × divisor; v14's reserve 10 + book already lifts v13's 10 s floors.

## 3. Models at real clocks (all vs the v14 bytes unless stated)

- v4 (features-v2): 9–5–10 over 24 (lanes P, Q, R), paired 0.479 (0.312–0.646). Not promoted.
- v5 (features-v2, unweighted): lane S 5–0–3 over 8 (0.625, 0.5–0.875); lane T vs the v4 archive with the same engine and book 2–0–6 (0.25, 0.0–0.5625). Lane S2 (4 more pairs vs v14) is running on cores 6–7 (started 04:02); unless the 16-game union clears ~0.6 with a lower bound above 0.5, the v1 model stays.
- Verdict so far: v1, v4 and v5 are indistinguishable at eight-game resolution. Offline suite gains (policy 32.7% → 35.9%, danger false negatives 87% → 59%) do not show up as strength.

## 4. Queen-loss corpus (the finding of the night)

From the true boards in the arena replays: our queen was captured for less in 52 of v10's 144 games and 37 of v13's 107 — the same rate, but the shape changed. v13 lost only 2 before ply 30 (v10: 15) and only 2 to knights (v10: 13); its residual 32 of 37 are sliders standing on a square unseen when we moved, that became visible only after our move — the queen stepped onto a long line with a rook, bishop or queen at the far end.

`data/queen-loss-seats.txt` holds all 240 such decisions (v4 105, v10 52, v13 37, older 46). `tools/benchmark_corpus.cc` now reports at those plies the belief mass on the true capturer, the engine's repeats by mass band, the same restricted to plies with a safe true-board alternative, and per-decision `QL` lines in verbose mode:

```
env FOW_SEED=1 FOW_CELL_THREADS=1 build/benchmark_queen2 data/queen-loss-seats.txt 1000 400000 verbose
```

Root engine and belief, seed 1, 400k nodes: capturer mass mean 0.398; bands < 0.05 / 0.05–0.3 / ≥ 0.3 = 81 / 56 / 103 plies; avoidable repeats 31 / 11 / 15 (57 of 240; 11 more are forced). On v13's own 37: 13 avoidable repeats, 10 of them in the < 0.05 band. The residual queen loss of the current engine family is a belief miss: the particles do not hold the slider at the far end of the line.

- Engine arms on the corpus (avoidable repeats, seeds 1/2/3): baseline 57/53/51; unseen-ray charge 40 cp per square with full rays 49/48/48; v13 subset 13/12/12 vs 9/11/13. Cost on the 634-seat fatal corpus: none (king losses 277, survival 357, en prise 66 vs 65, queen 9 vs 9). The gain is real in sign but 3–8 decisions and inside churn on the v13 subset; lane V (`3294fc29c616` = r10c + that setting, vs r10c) is running on cores 0–1 as a real-clock check, with no expectation.
- Control: the v14 engine and belief on the same corpus hold the capturer at 0.400 with bands 83/53/104 — identical to root. Capture evidence with persistence and Astra's own-move alignment and en-passant recovery do not touch this pattern.
- Ask to Astra: a line-of-sight treatment in predict/condition — where an unseen rook, bishop or queen can be, given every square we have seen since it was last placed — tested on the 81 low-mass plies with the band counts as the metric. The 634-seat corpus stays the cost side.

## 5. What runs now and what the day should do

Running: lane V (0–1, to ~04:25), lane S2 (6–7, to ~04:50). Core 5 is free; Astra holds core 2 and the GPU with cores 3–4.

For the 2000-rating trajectory, honestly: the current family sits around 1500–1550 and the top three are 1900–2165. The two measured levers are the belief on long lines (a third of our games are lost with the queen, and the engine already avoids two thirds of the corpus decisions where the belief holds the capturer) and more lane games per decision (eight-game lanes cannot order changes worth a few points of win rate; 40-game lanes can). Engine-side, no term tried tonight (two-ply weight 2, surface charge, late clock phase) moves the residual, so the next engine work should wait for a belief that holds the far-end slider, then re-measure the same corpus.

## 6. Commits and files

`85169e1` two-phase schedule; `166da52` off by default; `3d4ddbf`/`2ae5ed6` r10c and smoke U; `c589e7d`/`8dc2a25` harness metrics and the belief control; `2d68c39` lane T; `4f625e2` both corpora tracked (force-added under `data/`); `fable-submissions/README.md` map and log; `HANDOFF.md` entries from 02:30 to 04:05 UTC; `chatroom/ledger.jsonl`; `chatroom/cores.json`.
