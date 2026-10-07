# 011 — Two-day plan toward 2000 (Fable, 2026-10-07 21:30 UTC)

The arena stays on v10 (rank 8, rating ~1525) until a candidate beats it in our own gates. Targets below are measurable; each item names its metric and its gate.

## What the evidence says costs us the most

1. **The queen.** v10 lost the queen for less in 55 of 69 arena games: 48 to a capturer we could not see, 44 by moving her onto the square. Rooks and bishops on open lines, knights from the fog. The particle terms only see an attacker the population holds; these are the cases where it did not.
2. **Kings walking into unseen pieces** (long diagonals, unseen queen moves, endgame kings): the fatal plies the engine still loses, plus the belief scatter cases (qyzsbfdc, xidde3fz, dlhy2zfg).
3. **Thinking time**: every decision stopped at a 4 s cap with a median 121 s unused, and one arena core idle. Fixed in the full candidate (gates tonight).
4. **Draws we should win**: no repetition awareness. Fixed (`repetition_penalty`, on).

## Day 1 (tonight → tomorrow midday)

| item | lane | metric and gate |
|---|---|---|
| Unseen attack surface charge (`surface_charge`) and two-ply king threat (`hidden_king_threat_weight`) | Fable | benchmark: queen left en prise (engine vs real), king losses, survival, en prise; arms 0/10/20/40 and 0.3/0.6 running; then 16 real-clock games vs the full candidate |
| Clock + second core (full candidate) | Fable | lanes F/G vs the two-ply archive tonight; must not be worse, no overruns |
| Belief exactness: continuation evidence, bounded history for unseen pieces, endgame king mobility in the prior | Astra | true attacker held at the fatal ply 0.228 → ≥ 0.35; full-view consistency 100%; the three traced games |
| Policy refresh (stage A on all games to date, top-team weighted) when the GPU frees | Fable | model suite (policy top-k, danger calibration) ≥ v1; hybrid archive with the new model vs the same engine with v1, 16 games |
| Arena discipline | both | one upload per ~40 arena games; every candidate: offline gates + ≥16 real-clock games vs the current best first |

## Day 2

| item | lane | metric and gate |
|---|---|---|
| Opening book: the top teams' first 6–8 plies by colour, from the corpus (18 of 55 queen losses were before ply 30) | Fable | queen losses before ply 30 in the arena; benchmark early-ply en prise |
| Deliberate bait against greedy opponents (piece attacked but defended from a square they cannot see), weighted by the opponent prior's greed | Astra | benchmark on TA-A/TA-S/Apricot seats; real-clock lane |
| Engine strength per hypothesis: measure our perfect-information strength at fixed nodes; evaluation terms (king safety, mobility) or deeper search | Fable | fixed-node self-play Elo; then the fog gates |
| Decide the external-engine question (rules and licence) | user | — |

## Expected trajectory, honestly

Fixing the queen and king walks is worth the most and is the cheapest; with belief exactness and the clock, TA Baseline S level (~1700–1800) in two days is realistic. 2000 needs the engine-strength lever on top; that is the multi-day item, and the external-engine decision is the fork in that road.
