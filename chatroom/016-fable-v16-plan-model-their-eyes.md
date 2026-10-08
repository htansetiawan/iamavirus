# 016 — The v16 plan: model their eyes

For the user and Astra. Written 2026-10-08 ~08:00 UTC from the measurements in notes 014 and 015. Nothing here is built yet; the observation window on v15 runs to about 07:15 UTC on 2026-10-09.

## 1. The one insight

Every capability we lack is the same missing object. The engine models what **we** see (the particle belief) and prices what can happen to **us** (king loss, exposure, hidden threats). It has no model of what **they** see. The top six do: they keep pieces where we cannot look, route them through our blind squares, strike the king from there, raid with the queen along lines we do not watch, and never put a piece where we can take it for free. Their fingerprints are ordinary chess plus a model of the opponent's eyes.

We can build that model cheaply: every particle is a full hypothesis of their position, so `RenderObservation(hypothesis, their_side)` gives their view under that hypothesis, and the population gives the probability that each of our squares is seen by them. That one function turns four capability gaps into evaluation terms: unseen king threats (C1), fog routing (C2), vision economy (C6), queen activity (C7). It also closes the mirror-image failure in our discipline: the squares they cannot see are where our pieces are safe from directed attack; the long lines into our own fog are where they are not.

## 2. What the numbers say the plan must respect

- Winners over 4,735 decisive games: king threats 5.2 per 100 moves (losers 2.3), unseen king threats 2.9 (0.5), giveaways 1.1 (3.9), queen raids 4.5 (1.9), king moves 8.8 (16.9). A side above the median in king threats wins 70%.
- Our drift: v10 to v14 halved activity (long strikes 4.8 to 2.4, king threats 3.0 to 1.5, queen raids 2.8 to 1.8) with no discipline gain (giveaways 3.4 to 4.7). Every post-v10 term bought caution with activity; TA Baseline P went from 14-0-2 to 17-2-13.
- Gym baselines for the current engine: strike from the fog found in 39% of the top six's positions; their fog routes started one time in nine; 28% of our giveaways repeated; belief mass on the queen's capturer below 5% in a third of the queen-loss decisions.
- Lanes against our own archives cannot see activity loss, because both sides share it. Any gate must include a different style of opponent and the taxonomy rates.

## 3. The plan

**v16 — engine: their eyes, and activity restored.** Two days including gates.
1. `OpponentVision` in the engine: per particle, their view; aggregate into `seen_by_them[square]` (probability) and `their_king_attackers_unseen` after each candidate move. Cost: one observation render per particle per candidate on the shortlist, or on a particle stride, like the surface term did.
2. Three evaluation terms on the shortlist, priced in centipawns and tuned on the gym: (a) **strike**: a bonus for a candidate that attacks their king (or a piece worth 3+) from a square they probably cannot see; (b) **stealth**: a small bonus per our piece on a square they probably cannot see, larger for the queen; (c) **exposure, their side**: a piece of ours that they can see and attack is priced at full value, not at the particle mean. The existing caution terms stay but are re-weighted against the taxonomy so activity returns to v10's level: long strikes ≥ 4.5, king threats ≥ 4, queen raids ≥ 3.5, with giveaways ≤ 2.
3. Gates, in order: strike corpus 39% → 55% and route corpus 20% → 25%; giveaway corpus 28% → 15%; our pieces visible to the top six 22% → 17% (note 015, 8f); 634-seat fatal corpus survival not below baseline; taxonomy rates in 40 self-play games against v15 and against v10 (the active style we lost); real-clock lanes of 16 games against v15 and 16 against v10; then one arena upload.

**v17 — belief: line of sight and natural moves.** Astra's side, in assistant mode until the window closes: (a) a line-of-sight prior in predict and recovery for unseen sliders at the far end of open lines, measured by the queen-corpus capturer mass (0.38 → 0.50 on the 81 low-mass plies); (b) an opening and middlegame move prior fitted on the 4,902 games with a game-disjoint split, measured by top-4 hit rate on the top six (the natural-move blindness of zqcr3ewx); (c) the book stays gated by the king filter, which v15 already has.

**v18 — learning on move kinds, not on all moves.** Fine-tune the policy head on the top two bots' strike and route moves (the corpora, grown to thousands by the same cutter) and the danger head on the giveaway corpus; evaluate on the gym corpora and the taxonomy, not on generic policy accuracy, which never translated. Self-play reward shaping with the winner profile (unseen king threats positive, giveaways negative) is the follow-up once the engine terms exist to produce such moves.

**Fixes that remain band-aids but still worth it:** the forcing-sequence exploit (we recapture mechanically; swqjm4aj) gets a check that the king's recapture square is not attacked under any particle; the back-rank-bare pattern (ozw0u83h) gets a structural penalty when their rook or queen is alive.

## 4. What changes in how we work

- The gym runs on every candidate before any lane: taxonomy rates in self-play, the three corpora, the queen corpus, the fatal corpus. Numbers go in the README log with the archive hash.
- Lanes always include a style opponent (v10 bytes as the active style; a greedy archive when we have one), not only the current bytes.
- The arena record per opponent is the final judge; one upload per ~40 games; the taxonomy report per version (`learning/arena_watch.py`, extended with the taxonomy rates) is the dashboard.
