# Is the belief under-confident about fog attackers? Yes, by 2 to 7 times, and a guard still cannot use it

30 October 2026. Tool: mist-c `tools/hazard_calib.c` + `hazard_calib.py` (merged to main). It
replays 300 v35 arena games through the engine's belief (cap 200,000, v35's history table) and,
at each of our 12,174 decisions, scores every knight, bishop, rook or queen move the view allows
(239,815 candidates) by the belief's probability that the destination is attacked from an
unseen square, under three weightings of the worlds: fitted (the belief's own), sharp (the
temperature-2 weighting the guards use) and uniform. The same test on the true board is the
label. Two further labels: attacked and undefended (no piece of ours covers the square), and
the realised outcome of the played move (taken next reply; still 3+ down after our next move).
Full tables in `tables.md`.

## Calibration (played moves, event: destination attacked from the fog and undefended)

| belief says | fitted weighting: realised | sharp weighting (the guards'): realised |
|---|---|---|
| under 1% | 0.1% | 0.4% |
| 1 to 3% | 7.6% (4.1x) | 13.6% (7.5x) |
| 3 to 10% | 14.9% (2.5x) | 24.2% (4.2x) |
| 10 to 30% | 32.7% (1.8x) | 41.0% (2.2x) |
| 30% and up | 86.4% | 86.8% |

The same shape holds for the plain attacked event, for plies 1 to 30 only, for captures (worse:
fitted 3 to 10% realised 24.5%, sharp 44.9%) and for quiet moves. The belief's estimate of a
fog attacker in the range where the guard margins live (1 to 30%) is 2 to 7 times too low
under the guards' weighting, and 2 to 4 times too low under the fitted one. The sharpening
that helps the king guard against near-certain threats makes the piece-hazard estimate worse.
Brier scores: fitted 0.026, sharp 0.028, base rate 0.092; every weighting beats the base rate
by a wide margin, so the belief carries the information, at the wrong level.

## Support failure is absent

Among the 1,688 played moves whose destination really was fog-attacked, none had a predicted
probability of exactly zero under the fitted or uniform weighting, and 0.5% (fitted) to 2.5%
(sharp) fell at or below 1%. Over all 77,253 attacked candidates, 11 had exactly zero under
the sharp weighting. The attacker is in the belief's worlds; it is under-weighted, not missing.
A monotone calibration map would fix the level.

## But the event a guard needs is not the one the belief estimates

Of the 535 played piece moves in plies 1 to 30 whose destination was fog-attacked on the true
board, 19 (4%) became clean losses (taken, and still 3+ down after our next move); 359 (67%)
were exchanges and 157 (29%) were not taken. Moves the belief itself rated at 30% or more
clean-loss risk (one-exchange estimate) and that we played anyway: 238 in plies 1 to 30, of
which 3 (1.3%) were clean losses. Those are deliberate trades the search understood.

The 166 played moves that did lose a piece to an unseen capturer (0.024 of 6,813 played piece
moves, 143 of them clean on the true board) are spread across the guards' own risk estimate:
22% under 1%, 7% at 1 to 3%, 13% at 3 to 10%, 12% at 10 to 30%, 46% at 30% and up. A
threshold on that estimate at any level either misses most losses or vetoes the trades. This is
why the v20 piece guard (a margin on this estimate) lost in play: the static one-exchange label
cannot separate a loss from a trade; only the search's look-ahead can, and the search weights
the worlds in which the trade fails at the belief's under-confident level (median truth share
on those 166 decisions: 0.0019).

## Reading

1. The belief is measurably and consistently under-confident about unseen attackers, by a
   factor the data gives per bin, with no support failure.
2. A guard cannot use that fact: the decision event is a clean loss after look-ahead, not a
   static attack.
3. The place to apply the correction is therefore the worlds the search sees, not a veto:
   re-weight the sampled worlds toward those in which our pieces are attacked from the fog, by
   the measured calibration ratio (fitted weighting: about 4x in the 1 to 3% range, 2.5x at 3
   to 10%, 1.8x at 10 to 30%; sharp: 7.5x, 4.2x, 2.2x). That is a calibration of the belief,
   not a rule, and it is testable offline with this same tool (do the re-weighted estimates
   become calibrated, does the truth's share rise on the 166 loss decisions) before any game.
4. Astra's horizon (down 2+ after our next turn) counts 27 of 239 risky moves on 124 recent
   games; this tool's stricter 3+ label counts 19 of 535 fog-attacked moves in 300 games. The
   event is rare per move (under 1% of piece moves in plies 1 to 30), common per game (one in
   three to one in five games), and decisive when it happens.

Files: `tables.md` (every table), mist-c `tools/hazard_calib.c`, `tools/hazard_calib.py`, raw rows at
`{storage}/iamavirus-data/hazard/calib4-300.tsv` (240k candidate rows), run 2,524 s on one core.
