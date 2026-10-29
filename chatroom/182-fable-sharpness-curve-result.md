# 182 (Fable): sharpness curve result: the truth needs a fifth of the belief

The curve from 181 is complete (80 games, 0 failed, no forfeit, every dose verified on the
oracle side, no leak to v35). Score against frozen v35 by the true world's share of the
sampling weight on each of our decisions:

| share | natural (median 0.003) | 0.05 | 0.2 | 0.5 | 1.0 (179 oracle) |
|---|---|---|---|---|---|
| W-D-L | 6-1-13 | 11-1-8 | 16-0-4 | 20-0-0 | 40-0-0 |
| score | 0.325 | 0.575 | 0.800 | 1.000 | 1.000 |
| pair bootstrap 95% | 0.13 to 0.55 | 0.40 to 0.75 | 0.65 to 0.95 | 1.00 | 1.00 |

Target share: 0.2 is the lowest lane at the bar (point estimate exactly 0.8; exact lower
bound 0.60 at 20 games, so a floor, not a confirmed bound). 0.5 is the first lane whose
lower bound (0.86) clears the bar on its own. Call it 0.2 as the floor and 0.5 as the
comfortable figure.

The natural belief: the truth was in the belief on 552 of 558 logged decisions (lost once,
at the 200,000 cap), but its weight has median 0.003, is below 0.01 on 61% of decisions and
below 0.001 on 41%; it sits only 1.7 times above uniform over the live worlds at the median
and below uniform on 47% of decisions. Coverage is fine; weight is the whole gap, a factor
of about 60 at the median. The natural lane scored 0.325 against v35 with the same bytes,
within 20-game noise of 0.5 (Black 1.5 of 10).

For the belief build: the piece-square move-model refit (×1.9 on the truth's share over the
v35 traces) is an order of magnitude short and continues as the pipeline check only. The
leverage is in per-move sharpness, which compounds over the opponent's unobserved moves:
an opponent-specific model (fixed programs, 176k named games, the bot knows its opponent)
and a model conditioned on what the opponent can see. The natural lane
(`MIST_ORACLE_SHARE=0`) is now the yardstick for any belief: read its truth-share
distribution before any bench; a distribution matching the 0.2 dose predicts about 0.8.

Caveats in the result: the forcing persists through the belief update, so the forced
lanes' logged "natural" shares are post-dose (the dose itself is exact each decision); the
replay stderr excerpt covers the first ~27 decisions of 17 or 18 games per lane.

Full write-up `fable-submissions/analysis/oracle-share-20261029/result.md`, `readout.json`.
Cores 2 to 5 released.
