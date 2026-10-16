# The month plan: 16 October to 15 November 2026

*Written at v35, eighth at 1912, 20 rating points behind sixth. The goal is a bot that beats the top six on method, not on patches, and a contribution worth writing up. Every item below names its evidence, its measurement and its contribution. Order matters: the first two weeks fix the evaluation the search trusts, the second two change how the search spends its budget.*

[TOC]

## Where the data says the gap is

From 1,446 arena games of v33 to v35 against the top seven and the daily taxonomy over 11,925 games of all teams:

- **Every loss is a king capture**, 672 of 672 in the last three days against the teams above us. No forfeits, no draws lost.
- **Our king walks.** We move the king 16.6 times per 100 moves against their 11.6, and 13.2 in the endgame against Greek Gift's 1.8. Mist Opportunities, the other Obscuro engine, walks its king as much as we do and sits just above us.
- **Walking into the fog is what kills.** Right after our move, with the opponent still holding heavy pieces, the king is captured within four plies 1.8% of the time with no open line into unseen squares, 7.3% with one, 17.3% with two, 36.1% with three or more. In the endgame the rates are 1.7, 4.3, 7.8 and 12.0%.
- **We give material away twice as often**, 3.4 against 1.6 per 100 moves, and they threaten our king from unseen squares twice as often as we threaten theirs, 2.4 against 1.4.
- **The queen guard (v35) halved outright queen losses** against the top six, 43% to 23% of games, and moved nothing else: the games became queen trades lost later on material.

The common cause: **Stockfish scores every leaf as if both sides saw the board.** Its centipawns are the right chess evaluation and the wrong Fog of War one. A king on an open file is "active" to Stockfish and a target to duck. Our guards are patches on that mismatch, one piece at a time. The month is about fixing the mismatch itself and then spending the search budget where the hidden information is.

## Week 1 (16 to 22 October): a Fog of War value, measured not guessed

**1. Fog hazard in the leaf value** (started 16 October, `MIST_FOG_HAZARD`). Subtract from each leaf the measured capture rate for its king's open lines into unseen squares, phase-aware, on the [-1, 1] scale; optionally add the same for the opponent's king. This is a calibrated correction, not a heuristic weight: the table is the arena's own four-ply capture rates. Measure: regression suite (fatal and material kinds), then 40 games against the v35 bytes. Contribution: an empirically calibrated hazard term for a perfect-information evaluator used under imperfect information.

**2. Fit, don't tune.** Replace the hand table with a fitted one: for every position after our move in the 119,000-game corpus, regress "king captured within four plies" and "material lost within four plies" on fog features (open lines by direction, unseen knight squares, enemy heavy material, phase, whether the king has moved). A logistic model of a dozen features, fitted on all teams' games so it is not our own habits. Shipped as a small table in `data/`, read at start, no runtime cost. Contribution: the first data-fitted evaluation correction for Fog of War chess that we know of; Obscuro and Misty use Stockfish raw.

**3. Loss suite v2.** Rebuild the regression suite from v34 and v35 losses with two new kinds: "opened a line to the king" and "king walked into the fog". The 8-ply losses to HYPOTHERMIA and Lost Signal are the first entries. Measure every week-1 change on it.

Gate to week 2: fatal kind and the new kinds improve with material unchanged; the bench against v35 is not worse as either colour.

## Week 2 (23 to 29 October): the opponent, modelled from 119,000 games

**4. Retrain the opponent move model on all teams.** The conditional logit was fitted on 2,029 games; the corpus is now 119,405 with every top-six bot's current version. Fit per opponent class (search bots, sortie bots like HYPOTHERMIA, baselines) and select the class online from the first ten plies, the way the hybrid era's classifier did (AUC 0.94). The two 8-ply losses had the true board at weight 0.0006 and 0.0004 because the model called an early queen sortie implausible; HYPOTHERMIA does it in 78% of its games. Measure: held-out log-likelihood per class, then the truth's share in the belief on the suite (`--truth`). Contribution: opponent-class-conditional belief weighting in Obscuro-style search.

**5. The queen guard's rule for every piece, from the same fit.** Instead of a rook guard and a minor guard, the fitted "material lost within four plies" model gives one risk per move; fold it into the combined risk with its value weight. Measure on the material kind, which already punished the one-ply guard.

Gate to week 3: the truth's median share in the belief on hidden-check decisions rises from 0.0076; the bench holds.

## Week 3 (30 October to 5 November): spend the search where the fog is

**6. Information-aware sampling.** The search samples 32 worlds by weight. Sample instead by weight times disagreement: worlds whose best reply to our candidate differs from the modal world's are the ones that can change the decision. Astra's "threat-stratified root sampling" (note 077) is the prior art inside the team; this makes it the default with a measurement. Contribution: a variance-reduction scheme for GT-CFR world sampling.

**7. Depth where it matters.** Two-ply king guard: for the top candidates, the risk of a forced king capture after the opponent's best reply, on all of the belief, the class of the Sausage and Ne5 losses. Cheap because it reuses the guard's strided pass.

**8. Engineering budget.** The main thread still waits on Stockfish; profile v35 in the arena-sized box (2 cores, 1.9 times slower) with `MIST_TIMING` and make the belief update, the guards and the leaf scoring share the second core without oversubscription. Target: 30% more expansions per decision at the same clock, measured as paired runs. Candidates: batching guard passes over the belief in one traversal (king, queen, material risk in one loop instead of three), a compact belief representation (positions as 32-byte packed boards with incremental hashing instead of the current struct), and MultiPV capped at the moves the search will actually expand. Contribution: an engineering note on Obscuro-style search on two cores.

## Week 4 (6 to 15 November): learn the policy, keep the search

**9. Search distillation.** Train the existing CNN-GRU on mist-c's root policies and belief-weighted values from 50,000 self-play and arena decisions (the pipeline, the encoder and the trainer exist from the hybrid era), and use it as the root prior and the fresh-information-set initialiser in GT-CFR instead of "start on the best child". The arena is offline, so the network must be small; 1.87M parameters ran in 0.14 ms. Measure: suite, then bench. Contribution: an amortised policy inside imperfect-information search, which is the research question behind the Jev discussion, done with a local model.

**10. Write-up.** Methods, the fitted hazard, the class-conditional opponent model, the sampling scheme, the engineering numbers, with the negative results (the material guard, v13, v16) kept. The docs site holds it.

## How each week is judged

Every change ships only through the same three gates: the suite, paired against the current bytes; 40 games against the current bytes at 180+2, both colours, no forfeit; the arena with a written prediction and the fail-fast rule. Checkpoints are daily from the systemd report, not every 20 minutes.

| milestone | number that must move |
| --- | --- |
| week 1 | king-capture-within-4-plies rate after our moves with 2+ fog lines, from 17% towards 10%; bench vs v35 above 0.50 |
| week 2 | truth's median share in the belief on hidden-check decisions, from 0.8% towards 5%; outright queen losses vs the top six under 15% |
| week 3 | expansions per decision +30% at the same clock; two-ply mate class fixed on the suite |
| week 4 | top six above 0.33 in the arena over 200 games; rating above Instructors |

## What is deliberately not on the list

Opening books and opponent-specific replay lines, which won in the hybrid era against one deterministic bot and lost everywhere else; margin tuning of the existing guards beyond what the fitted model gives; and anything that needs a network at arena time.
