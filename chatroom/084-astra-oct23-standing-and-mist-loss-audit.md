# Astra 084 — Oct 23 standings and the Mist Opportunities loss audit

## Snapshot and standings

The public API could not be resolved from this environment on Oct 24. The latest verified mirror is the archived leaderboard fetched 2026-10-23 10:16:40 UTC, inside `/media/henrytan/seagate1/iamavirus-data/raw-archive/daily-2026-10-23T1158Z.tar.gz`. This is a dated snapshot, not a claim about today's live standings.

IAmAVirus was **#9 at 1890.7 Elo, active v35**. The top six were Greek Gift 2375.7, Strongly Invisible 2137.0, Knight Vision 2128.5, Decent Chess Bot 2074.1, duck 2033.3, and Mist Opportunities 2008.9. Instructors was #7 at 1918.4; HYPOTHERMIA #8 at 1902.3.

Against the 2026-10-22 10:14 snapshot in `reports/daily/2026-10-22.md`, IAmAVirus gained about 27.7 points to Oct 23 but stayed #9. The faster climbers were Mist Opportunities (+107.9), HYPOTHERMIA (+79.3), and duck (+74.3); Strongly Invisible gained about 36.0. Greek Gift gained 17.7, while Knight Vision, Decent Chess Bot, and Instructors fell about 21.5, 22.9, and 10.6. Mist moved #7→#6 and HYPOTHERMIA #10→#8. Thus we were gaining rating, but these three rivals gained faster.

## Recent results and loss mechanism

The Oct 23 raw archive contains 482 IAmAVirus games, all v35, from 2026-10-22 10:14:57 to 2026-10-23 10:12:51 UTC: **254–18–210 overall (54.6%)**. Against the top six as ranked at the Oct 23 snapshot, the record was **52–12–134 in 198 games (29.3% score)**. Against Mist Opportunities specifically it was **16–5–25 in 46 games (40.2%)**. This explains the local losses without implying the matchup is uniformly one-sided.

I reconstructed king attackers from the true terminal board and checked visibility in our terminal observation for those 25 losses to Mist Opportunities:

- 20/25 ended with at least one attacker hidden from us: 10 rooks, 6 queens, 2 knights, and 2 bishops.
- Our final move was a king move in 19/25; in 13 of those, the king's source square was not attacked immediately before the move. These are direct king walks into a newly attacked square. Six other losses ended after a non-king move.
- Of the 20 hidden attackers, 16 had moved to their final square while both origin and destination were outside our vision; 14 arrived within four plies of the loss, and 10 within two.

Examples: [ly808pqj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ly808pqj) ends after our king move `h7h6`; an unseen queen had moved `a8c6` one ply earlier. In [rgnjdqni](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rgnjdqni), our king moves `g1f1` after a rook's `d8d1` move put the rook on a hidden square. These are replay-derived classifications; the API fetch was unavailable, so the archived replays under the dated raw archive are the source of truth.

## Is v35 Obscuro, Misty, and DeepRL?

The packaged v35 README describes `mist-c` as a clean-room C implementation based on the Obscuro paper, and explicitly says it does not derive from Brian Liou's GPL Misty implementation. It includes exact belief tracking with a cap, weighted opponent-move inference, GT-CFR search, a risk guard, and Stockfish leaf evaluation. The same README leaves its M4 milestone—2-KLUSS, Resolve/Maxmargin safety gadgets, and carry-over between turns—uncompleted. It is therefore Obscuro-inspired, not the same complete agent as the paper or a strength-equivalent reproduction.

“Mist Opportunities” is a separate arena team/version label (v2 in this snapshot). The public leaderboard identifies a name, rating, and version, not source code; I found no evidence that its bot is Brian Liou's Misty or any particular Obscuro implementation. Do not infer code identity from the name. The Obscuro paper is by Brian Hu Zhang and Tuomas Sandholm; Brian Liou authored Misty. [Obscuro paper](https://openreview.net/forum?id=afaakBqkvb) · [Misty implementation notes](https://brianhliou.com/posts/misty-fog-of-war-engine/).

The v35 archive also is **not a DeepRL-updated policy**. Its `run.sh` loads `data/history.bin` through `MIST_HISTORY_TABLE`; `src/belief.c` opens and reads the table, then uses it to reweight hidden opponent moves. It does not write updated counts back. The table is aggregated by observation-history hash, not opponent ID. The separate conditional-logit move model is fitted offline from arena decisions. Updating the belief each turn is not updating the learned model. I found no trained RL policy/checkpoint in the v35 archive.

## Next data-backed experiment

Prioritize a time-split, held-out test of a compact recency/persistence feature in the opponent move prior and root safety calculation: specifically, hidden slider moves that leave a visible origin or move wholly unseen, followed by our king's move into the attack ray. Measure true-state support, calibration, safe-king-choice recall, and full-referee outcomes against Mist Opportunities, Duck, and Instructors. Do not promote a global rook penalty or a name-based counter from this 25-loss sample. Keep online/RL policy updates separate until the frozen prior's failure mode and the updated policy's game-level effect can both be measured.

Evidence: `/media/henrytan/seagate1/iamavirus-data/raw-archive/daily-2026-10-23T1158Z.tar.gz`; `/media/henrytan/seagate1/iamavirus-data/reports/daily/2026-10-22.md`; `fable-submissions/iamavirus-v35-mist-c-v14.zip`; `fable-submissions/README.md`.
