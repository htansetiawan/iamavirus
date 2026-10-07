# v5 — plausibility prior over opponent moves (candidate, not submitted)

## What v4's failure taught

Two attempts to fix the Greek Gift trap with a better decision rule both failed,
measured over 15 seed/population combinations:

| approach | bait declined |
|---|---|
| v4: hard threshold 0.04 + fallback band | 7 / 15 |
| continuous price, 30,000 cp per unit risk | 3 / 15 |
| **plausibility prior over opponent moves** | **13 / 15** (10/10 at ≥2048 particles) |

Instrumenting the second attempt showed why both failed. The penalty *was*
applied, 1596–3332 cp, and the bait still won at p=1.000, because the safest
available move also measured 70–92 permille. **Every** move in that position
carried ~8% risk, so the penalty was near-uniform across candidates, cancelled,
and material decided.

The decision rule was never the problem. **The belief assigned ~8% to something
that was 100% true** — the knight was on e5, and only 0.4% of hypotheses placed it
there. No decision rule can repair a posterior that wrong.

What actually refutes `Kxf7` is the question a human asks instantly: *why is he
giving me a bishop?*

## Implemented

The particle filter previously weighted the opponent's moves **uniformly**. That
is its most consequential modelling assumption and it is weakest exactly where it
matters most: roughly twenty of their thirty moves are observationally identical
to us, so for those the prior alone determines the posterior.

Replaced with a crude plausibility model, as multipliers:

| situation | factor |
|---|---|
| leaves a piece where we can take it for less than its worth | **×0.06** |
| is a capture | ×2.5 |
| attacks our king | ×3.0 |

Mechanically: under a uniform prior the "he just blundered a bishop" hypotheses
outnumber the "it is defended" ones, so the bait looks free. Weighted by
plausibility, giving away a bishop for nothing is rare, so the mass moves onto the
defended hypotheses — which is the truth.

Also in this version:

- King risk priced continuously (`king_risk_price`, default 30,000 cp) rather than
  thresholded, and charged on every matrix cell so no later stage is blind to it.
- **Node-limited search** (`FOW_NODE_BUDGET`). A time-limited engine's strength
  depends on machine load, which made the number of parallel games a hidden
  variable in every earlier A/B. Node limits make a decision reproducible —
  verified identical node count and identical move across runs — and 20× faster.
- Ablation knobs for every judgement call (`FOW_OPPONENT_PRIOR`,
  `FOW_KING_RISK_PRICE`, `FOW_SPECULATIVE_WIN`, and others), with malformed values
  reported rather than silently ignored.

## Results

| measurement | value |
|---|---|
| Greek Gift trap, 15 seed/population combinations | 13 / 15 declined (was 3 / 15) |
| aggregate king-blunder rate, 209 real decisions | 8.13% → 9.09% |
| real losing positions survived | 40% → 44% |

**The targeted exploit is robustly closed. The aggregate blunder rate did not
improve.** 8.13% vs 9.09% against ±2% error is unchanged, and if anything points
the wrong way. Three king-safety configurations were then compared and all were
statistically indistinguishable (9.09%, 10.05%, 8.61%).

That is why this version is a candidate and not a submission: every tuning
decision in it was made below the resolution of the instrument measuring it. A
larger corpus sweep is in progress.

## Hand-tuned constants in this version

`0.06`, `2.5`, `3.0`, `30000`, `0.20`. All five are estimating quantities that
could be learned from the 3.9 M real decisions available through the public API.
Hand-fitting them by eye, with an instrument too coarse to tell whether the fit is
good, does not scale. That is the argument for the learning work.
