# 015 — Move taxonomy v0, the capability map against the top six, and the gym

For the user and Astra. Written 2026-10-08 ~08:40 UTC during the v15 observation period. Everything here is measured from arena replays (true boards plus both sides' views) with `learning/move_taxonomy.py`; nothing in the bot changed.

## 1. Why a taxonomy, not another fix

The user's framing (08:10 UTC): understand what kinds of moves both sides make, slot them into a taxonomy, name the capabilities we lack, and turn those into benchmarks and a gym with targets — fixes for degenerate behaviour continue, but the trajectory is set by capabilities. The numbers below are the first version of that map. Two facts motivate it: against the top six we are 2–1–46 (versions 13–15), and against TA Baseline P we went from 14–0–2 with v10 to 17–2–13 with v13–v15, so the engine package since v10 did not raise the ceiling and lowered the floor against a simple greedy bot.

## 2. The taxonomy (v0, 19 move kinds)

Computed per move from the replay frames; S is the mover, O the opponent, "unseen" means `?` in the relevant side's view at that time. Definitions are in the tool's header; the short list:

- **capture**, **capture_unseen** (O could not see the capturer), **victim_walked_in** (O's previous move put the victim there), **long_strike** (slider capture from 3+ squares), **fog_route** (the capturer reached its square through moves O never saw; depth = how many), **forcing_chain** (capture–recapture chains of 3+).
- **king_threat** (after the move S attacks O's king), **king_threat_unseen** (and O cannot see the attacker), **king_capture**, **sacrifice** (3+ points given net over two plies), **king_hunt_sacrifice** (a sacrifice followed by S's king capture within 8 plies).
- **vision_gain / vision_loss** (S's visible squares change by 3+), **king_move**, **castle**, **king_leaves_home**, **queen_raid** (queen enters O's half), **queen_exposed_unseen**, **walk_into_unseen** (a piece worth 3+ placed on a square attacked by a piece S cannot see), **back_rank_bare**.

Usage: `python -m learning.move_taxonomy --versions 13 14 15 --opponents top6.json` (us vs them), `--all-games --by-team` (fingerprint per team), `--json` for per-move labels.

## 3. The map against the top six (49 games, v13–v15, per 100 moves)

| capability | us | them |
| --- | --- | --- |
| squares visible per move | 31.5 | 38.3 |
| captures | 14.4 | 22.0 |
| slider strikes from 3+ squares | 1.7 | 5.4 |
| captures by a piece routed through unseen squares | 9.2 | 14.3 |
| moves that attack the enemy king | 0.6 | 6.1 |
| … with the attacker invisible to the victim | 0.3 | 2.7 |
| queen raids into the enemy half | 0.2 | 3.5 |
| king moves | 16.4 | 7.4 |
| material given away for nothing | 4.8 | 0.7 |
| pieces walked onto an unseen attacker | 3.7 | 2.0 |
| back rank left bare with their rook or queen alive | 3.7 | 2.6 |

Game-level facts: we win the first piece-sized exchange in 31 of 49 games, but our lead peaks at 1.2 points on average and exceeds 3 in only 6 losses; 42 of the 46 kings we lost fell to a piece we could not see; their first material strike comes from short range (2.1 squares; pawns 9, bishops 18, knights 10, rooks 8) and in 30 of 47 cases from a square we had seen earlier in the game; our king stays home but shuffles (16 king moves per 100 vs 7); our queen never enters their half (6 plies per game for theirs, 0 for ours).

Three mechanisms, with the games to open:
1. **Routing through the fog to the king.** `ozw0u83h` (duck): material equal, our king on g1 behind an empty first rank; their rook went e8–e2–a2–a1 in three moves we never saw and took the king. They navigate inside our blind squares toward a weakness they can see.
2. **Forcing lines that use our predictability.** `swqjm4aj` (Decent Chess Bot): Rg3 on the queen, Ne3, rook takes queen, we recapture, queen takes rook, king recaptures, knight takes king from a square we never saw. Fourteen points invested because they know we recapture mechanically.
3. **Natural-move blindness.** `zqcr3ewx` (Strongly Invisible): ply 10, our bishop went to b5 next to a pawn that had played …c6 unseen. Our belief treats their replies as near-uniform; strong bots play normal chess.

## 4. Fingerprints per team (all 4,902 stored games, per 100 moves)

| team | games | visible | captures | long strikes | fog routes | king threats | unseen king threats | queen raids | king moves | giveaways | walked into unseen | fog depth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Greek Gift | 1342 | 33.9 | 22.0 | 5.0 | 15.9 | 4.4 | 2.3 | 3.8 | 13.1 | 1.4 | 2.6 | 2.77 |
| Knight Vision | 1344 | 34.5 | 23.8 | 4.8 | 17.6 | 4.2 | 2.2 | 3.4 | 11.9 | 1.4 | 1.9 | 2.61 |
| Decent Chess Bot | 834 | 34.1 | 21.5 | 4.0 | 15.9 | 3.5 | 1.8 | 3.2 | 13.7 | 1.7 | 3.0 | 2.75 |
| Strongly Invisible | 791 | 32.9 | 20.9 | 4.4 | 14.9 | 3.5 | 1.6 | 3.0 | 15.6 | 1.2 | 2.8 | 2.95 |
| duck | 781 | 33.2 | 23.1 | 5.3 | 15.5 | 4.0 | 1.7 | 3.6 | 15.4 | 2.7 | 3.3 | 2.23 |
| Instructors | 710 | 32.7 | 21.5 | 4.3 | 15.3 | 3.3 | 1.4 | 3.0 | 15.5 | 2.2 | 2.9 | 2.69 |
| TA Baseline S | 737 | 32.8 | 24.4 | 5.5 | 16.6 | 4.0 | 1.5 | 3.4 | 13.6 | 3.2 | 2.9 | 2.07 |
| TA Baseline A | 702 | 33.0 | 25.4 | 5.5 | 16.5 | 3.2 | 1.1 | 1.7 | 10.1 | 2.8 | 3.5 | 1.85 |
| **IAmAVirus** | 857 | 32.8 | 20.5 | 3.8 | 14.0 | 2.6 | 1.2 | 2.2 | 15.7 | **4.0** | 3.5 | 2.35 |
| TA Baseline P | 658 | 33.1 | 25.5 | 5.6 | 16.0 | 3.1 | 1.0 | 1.5 | 10.7 | 3.4 | 3.7 | 1.76 |

Reading: averaged over all their opponents the top bots are not exotic; what separates the two leaders is king-directed play (4.2–4.4 king threats, 2.2–2.3 of them unseen, against our 2.6 / 1.2), queen activity (3.4–3.8 raids vs 2.2), deeper fog routes (2.6–2.8 vs 2.35), and above all discipline: they give material away at 1.4 per 100 moves, we at 4.0, the worst figure in the top ten. Vision is relational: everybody sees about 33 squares on average, but when the top six play us they see 38 and we see 31 — our piece placement feeds their sight.

## 5. What we do not have (the capability list)

- **C1 King-directed play.** Creating threats on the king, especially from squares the opponent cannot see. 0.6 vs 6.1 per 100 in the top-six games. Our search prices our own king risk; it does not pursue theirs.
- **C2 Fog routing.** Multi-move maneuvers through squares the opponent cannot see, ending in a strike. Depth 2.35 vs up to 2.95. We have no model of what the opponent sees; the mirror of our own vision function on the particles would give one.
- **C3 Opponent model.** Their replies are not uniform; …c6 after 1.Nc3 2.d4 is likely, Qa4 after 1.c4 d5 is likely. Our hand prior is flat apart from captures and king attacks. The learned 26-feature prior exists but was never validated on a game-disjoint split.
- **C4 Material discipline.** 4.0 giveaways per 100 moves vs 1.4. Many are queen or minor pieces placed where an unseen piece takes them (`walk_into_unseen` 3.5 vs 1.9–2.6).
- **C5 Conversion.** We get the first exchange in 31 of 49 games and lose 46; a lead must be turned into king pressure or simplification, and we do neither.
- **C6 Vision economy.** Being seen 38 squares' worth while seeing 31; placement that keeps our pieces out of their sight lines and extends ours.
- **C7 Queen activity.** Their queen is the hunting piece (3.5 raids vs 0.2 in those games); ours is a liability we keep home and still lose (21 of 48 v14 games).
- **C8 Style robustness.** v10 beat TA Baseline P 14–2; v13–v15 are 17–2–13. Something in the post-v10 package (two-ply threat, king threat, repetition charge, clock, book) trades well against our own archives and badly against a greedy bot. Lanes against our own bytes cannot see this.

## 6. The gym

Each capability gets a replay metric (already produced by the tool), a decision-level benchmark where a corpus can be cut from the 4,902 games, a target, and a training route. Real-clock lanes against the current bytes remain the exit gate, and the arena gets one upload per ~40 games.

| capability | replay metric (per 100 moves) | decision benchmark | target (first) | training route |
| --- | --- | --- | --- | --- |
| C1 king-directed play | king_threat, king_threat_unseen | **strike corpus**: positions where a top bot created an unseen king threat; does our engine find the same move at 400k nodes | 3.0 / 1.5 | a search objective for attacks on their king from squares they cannot see (their visibility is computable per particle); reward only when a safe alternative exists |
| C2 fog routing | fog_route rate, fog depth | **route corpus**: the first move of a top bot's 2+-move unseen maneuver that ended in a strike; hit rate | 16 / 2.6 | a stealth term: value squares the opponent's pieces do not see, computed on each hypothesis |
| C3 opponent model | — | **prediction suite**: next-move log-loss and top-4 hit rate of the prior on game-disjoint held-out top-six games (Astra's harness exists) | top-4 ≥ 55% | refit the learned prior with a game-disjoint split; promote only if the queen-loss corpus capturer mass rises |
| C4 material discipline | sacrifice (non-hunt), walk_into_unseen | **giveaway corpus**: our 4.0-per-100 giveaway moves with the true board; share repeated by the engine | 2.0 / 2.5 | exposure pricing against the belief's own uncertainty: a piece on a square with low visibility support costs its full value times the hidden-attacker mass, not the particle mean |
| C5 conversion | peak lead vs result | **lead corpus**: positions where we led by 3+; result share | win 70% of 3+ leads | simplification and king-pressure terms when ahead; measured by the metric, not by lanes alone |
| C6 vision economy | visible (ours) minus visible (theirs) | — | seen gap ≤ 3 | the same stealth term as C2, plus a vision term evaluated against the top-six fingerprint |
| C7 queen activity | queen_raid without queen_exposed_unseen | — | 2.0 raids with ≤ 0.3 exposures | follows C1 and C4; no separate term |
| C8 style robustness | per-opponent record | **style sparring**: lanes against archives tuned to greedy, cautious and raiding styles, plus the arena record vs TA-P/A/S | ≥ 70% vs TA-P | every candidate plays all three styles, not only the current bytes |

Discipline for the gym: the taxonomy runs on every new arena game per version (`arena_watch` already ingests every 30 minutes); the decision corpora are cut once and frozen; a change is proposed with the metric it should move, measured offline on that corpus and on the 634-seat fatal corpus for cost, then gated by a real-clock lane of at least 16 games against the current bytes and one style archive; and the arena record per opponent is the final judge.

## 7. Immediate work inside the observation window (nothing ships)

1. Cut the strike corpus (C1) and the route corpus (C2) from the top-six games and record our engine's baseline hit rates.
2. Cut the giveaway corpus (C4) from our own games and record the repeat rate, as with the queen corpus.
3. Ask Astra (assistant mode) to run its prediction suite with a game-disjoint split for C3 and report top-4 hit rate on the top six.
4. Keep `data/reports/v15-watch.md` running; the TA-P record is the first style number to watch.
