# 016 — The v16 plan: model their eyes, then their mind

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

**v17 — belief: line of sight and natural moves.** Fable's side (user decision 08:10 UTC: Astra stays assistant; Fable owns the belief and the game-theory layer): (a) a line-of-sight prior in predict and recovery for unseen sliders at the far end of open lines, measured by the queen-corpus capturer mass (0.38 → 0.50 on the 81 low-mass plies); (b) an opening and middlegame move prior fitted on the 4,902 games with a game-disjoint split, measured by top-4 hit rate on the top six (the natural-move blindness of zqcr3ewx); (c) the book stays gated by the king filter, which v15 already has.

**v18 — learning on move kinds, not on all moves.** Fine-tune the policy head on the top two bots' strike and route moves (the corpora, grown to thousands by the same cutter) and the danger head on the giveaway corpus; evaluate on the gym corpora and the taxonomy, not on generic policy accuracy, which never translated. Self-play reward shaping with the winner profile (unseen king threats positive, giveaways negative) is the follow-up once the engine terms exist to produce such moves.

**Fixes that remain band-aids but still worth it:** the forcing-sequence exploit (we recapture mechanically; swqjm4aj) gets a check that the king's recapture square is not attacked under any particle; the back-rank-bare pattern (ozw0u83h) gets a structural penalty when their rook or queen is alive.

## 4. What changes in how we work

- The gym runs on every candidate before any lane: taxonomy rates in self-play, the three corpora, the queen corpus, the fatal corpus. Numbers go in the README log with the archive hash.
- Lanes always include a style opponent (v10 bytes as the active style; a greedy archive when we have one), not only the current bytes.
- The arena record per opponent is the final judge; one upload per ~40 games; the taxonomy report per version (`learning/arena_watch.py`, extended with the taxonomy rates) is the dashboard.

## 5. The layer the first draft lacked: how they think about how we think (added 08:15 UTC)

The user's objection (08:10 UTC) is right. Sections 1–3 model their **eyes**; a strong opponent also has a **mind**: a belief about where our pieces are, a policy that acts on that belief, and a model of what we will do. Our engine has none of the three today — its prior over their moves scores each move on the hypothesised true board, as if they knew it, and its matrix game plays against a distribution of boards, not against an opponent choosing under uncertainty.

What this looks like in our architecture, from cheapest to deepest:

- **Level 1 — their information (v16, section 3).** Their view under each hypothesis. Already planned; it gives stealth and strikes.
- **Level 2 — their belief and their policy.** Under each hypothesis we know their pieces, and we always know ours, so we can replay their views along the whole game and keep, per hypothesis, *what they have seen of us and when*: the last-seen square of each of our pieces from their side, and whether we moved it unseen since. That is their belief about us in a form the engine can use at move time. Their policy is then scored on **their** board (what they believe) instead of the true one: a capture they cannot know about is not plausible, an attack on the square where they last saw our queen is, a check on our king where they last saw it is. This replaces the flat hand prior and is the natural-move model the queen trap and the b5 bishop asked for. Measurement: the top-4 hit rate on the top six's actual moves, which the gym can compute exactly because the true history is in every replay. Baseline today (note 015, 9b): the hand prior ranks their real move in its top 4 36% of the time, log-loss 3.11 against 3.39 for uniform. Target for v17: top-4 ≥ 50%. First candidate: the stage A policy network run from their seat under each hypothesis, which reaches about 55% top-4 from a mover's own view.
- **Level 2, used offensively — deception and ambush.** If their belief has our queen on d8 but she left unseen, their attack on d8 is a move we can predict and punish: our candidate moves are scored not only for safety but for what they will do next under their belief. Bait (a piece shown then withdrawn, the YouTube guide's word), ambush (a route that ends where their predicted move walks in), and feints become searchable because their predicted reply is a function we can evaluate.
- **Level 3 — their model of us.** They know we recapture, they know our book, they know we retreat from visible threats; the forcing-sequence losses (swqjm4aj) are level-3 play against us. We know our own policy exactly, so the cheapest level-3 move is to detect when our predictable reply is the one they are steering toward: before any recapture of a queen or rook, or any book move, ask whether the position after our expected reply is one where a piece they can place unseen wins the king, and if so deviate. Later, the matrix game's columns stop being boards and become their best responses computed on their belief, which is the proper game-theoretic payoff for a candidate move.

Evidence on where the top six sit: they do not attack stale squares more or less often than we do (1.4% of moves aim at a square where our piece was last seen but is gone, for both), and they hide pieces only slightly more consistently than we do (moves that vanish from our sight minus moves that enter it: −2.0 per 100 for them, −3.1 for us, −7.9 for the TA bots). Their edge is not a crude ghost model; it is the strike, route and discipline rates of note 015, which are level-2 behaviours — they act where our belief is weak and avoid where ours is strong. That is what the level-2 prior and the deception terms are for.

Gym additions for this layer: **opponent-move prediction** (top-4 hit rate and log-loss of our predictor on the top six's moves, conditioned on their reconstructed belief; today's hand prior is the baseline), **ambush corpus** (positions where a top bot's move punished a predictable reply; does our engine deviate), and **deception events** in the taxonomy (a piece withdrawn unseen followed by an enemy move toward its old square).

Order of work, all Fable: v16 level 1 and activity (two days with gates), then level-2 belief and prior (v17), then the offensive use of level 2 and the level-3 recapture check (v18, with the learning on move kinds moved behind it). Astra: monitoring, reviews, and the read-only prior evaluation when asked.

## 6. Implementation notes for v16 (added 08:50 UTC; no code changed)

Where it plugs in: `Engine::ChooseMove` assembles `risk[row]` per shortlist row (engine.cc around lines 1037–1100): king-loss probability × `king_risk_price`, exposure × `piece_risk_weight`, the two-ply hidden threats, the repetition charge, then the surface and vision terms (both off). The new terms join that block, each behind an option in `EngineOptions` with a `FOW_*` override, default off until the gym says otherwise.

Primitive: `VisibleSquares(position, color)` (observation.h) returns the bitboard a side sees, far cheaper than the string `RenderObservation`. For a candidate move and a particle: apply the move to the hypothesis, take `VisibleSquares(hypothesis, enemy)`, and read three things off it. Stride over the population as `surface_stride` does (every 4th particle is enough for a probability).

Terms, all in centipawns on `risk[row]` (negative = bonus):
- **strike** (`FOW_STRIKE`): `− w × P(our attackers of their king include a square they cannot see)`; the same for attacks on their queen or rook at a lower weight. Needs the king-risk filter to stay in front, so a strike never costs the king.
- **stealth** (`FOW_STEALTH`): `− w × Σ over our non-king pieces of value × P(the piece's square is not in their visible set)`, counted after the move; the queen weighted highest. This is what keeps the queen off their lines without a hand-written line rule.
- **seen exposure** (`FOW_SEEN_EXPOSURE`): for each of our pieces that is both visible to them and capturable on the hypothesis, the full net capture value × P(both), replacing the particle-mean exposure for that piece. A gift they can see is priced as a gift, not as an expectation.

Cost: the shortlist is 12 rows, the stride gives 512 particles, each needing one move application and one `VisibleSquares` (a few hundred nanoseconds): well under a millisecond per decision.

Activity re-tune: run the taxonomy on 40 self-play games per setting against the v10 bytes and the v15 bytes for the weight grid `{hidden_threat_weight, hidden_king_threat_weight, repetition_penalty} × {strike, stealth, seen exposure}`; accept the setting whose rates are closest to the winner row of note 015 (king threats ≥ 4, long strikes ≥ 4.5, queen raids ≥ 3.5, giveaways ≤ 2, walk-ins ≤ 2.5) and whose fatal-corpus survival is not below baseline.

Tests to add with the terms: a position where the strike bonus prefers the unseen attack over an equal seen one; a position where stealth keeps the queen off a line into the fog; a position where seen exposure refuses a visible gift that the particle mean would accept.

Gate sequence, unchanged: strike corpus 39% → 55%, route 20% → 25%, giveaway repeat 28% → 15%, our visible share vs the top six 22% → 17%, fatal corpus, taxonomy in self-play vs v10 and v15, 16-game lanes vs each, one upload.
