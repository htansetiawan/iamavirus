# Neural risk as a calibrated complement to particle risk

## Result, 2026-10-11

The actor-only experiment from `neural-risk-integration.md` is complete on its
preselected development-validation split. The test shard remained unread. One
attention-small model and one particle-filter seed were used; the model and
particle risk did not affect the recorded actors' moves.

| Evaluation signal | Decision-weighted Brier ↓ | Decision-weighted log loss ↓ |
| --- | ---: | ---: |
| Raw particle risk | 0.01861 | 0.10500 |
| Calibrated particle only | 0.01736 | 0.06822 |
| Calibrated neural only | 0.03991 | 0.14333 |
| Calibrated particle + neural | **0.01676** | **0.06325** |

Fused minus calibrated-particle-only deltas, bootstrapped over the 64 evaluation
games (10,000 paired resamples): Brier −0.000600, 95% interval
[−0.001186, +0.000017]; log loss −0.004976, interval
[−0.007230, −0.002655]. The neural head alone is materially worse, but its
nonnegative fitted coefficient adds a small amount of complementary predictive
information when combined with particle risk. At calibration-selected 5% FPR,
evaluation recall is 89.9% fused vs 86.6% particle-only, with actual evaluation
FPR 6.44% vs 6.51%. At 1% target FPR, recall is 74.3% vs 72.2%, with actual
FPR 1.14% vs 1.12%.

The usable conclusion is limited to immediate king-capturable labels. It does
not show a stronger move policy, lower game-loss rate, improved Elo, or a
well-calibrated multi-ply danger estimate. The slight Brier interval overlap
with zero and FPR drift matter. This merits a separate, log-only engine
integration arm with an untouched game split; it does not justify making the
head a veto or changing a release.

## Data and reproduction

The calibration and evaluation partitions are each 64 full games, both colors,
every fourth own decision, with each decision contributing unit total weight
divided among its legal candidates. The collector receives observation and
past-own-action streams only. Replay truth is joined only after prediction.
The exact game/trajectory partitions were already frozen in
[`partitions.json`](partitions.json) and match the collector output.

Run receipts and joined actor-only rows are retained in
[`run-20261011`](run-20261011/). The model checkpoint SHA-256 is
`2e0af1ccd8e1f05f3beadac96151099342c0ede691e331e8272ba327f19addaf`; the
collector receipt records hashes for the dataset shards, model graphs, probe,
and all outputs. The analysis is reproduced by:

```sh
python3 astra-submissions/tools/analyze_neural_risk.py \
  --calibration astra-submissions/analysis/neural-risk/run-20261011/calibration.jsonl.gz \
  --evaluation astra-submissions/analysis/neural-risk/run-20261011/evaluation.jsonl.gz \
  --collection-state astra-submissions/analysis/neural-risk/run-20261011/state.json \
  --design astra-submissions/analysis/neural-risk/design.json \
  --output /tmp/neural-risk-evaluation.json --bootstrap 10000
```

The JSON report contains the fitted nonnegative coefficients, calibration-only
FPR thresholds and evaluation operating points, paired game-bootstrap
intervals, subgroup diagnostics, input hashes, and caveats. The numerical
implementation has dependency-free tests in
[`test_analyze_neural_risk.py`](../../tools/test_analyze_neural_risk.py).

## Fixed-history choice ablation

An isolated copy of the frozen engine was then run twice on the same 64
evaluation actor histories: once with its existing particle-risk safety gate,
and once with the fitted fused score substituted at that same gate. Candidate
sets, policy outputs, neural logits, particle estimates, observations and
recorded action prefixes matched exactly between arms. The choice changed on
231/1,393 decisions (16.6%). Selected immediate king-loss labels fell from
23/1,393 to 18/1,393 (1.65% → 1.29%); 8 changed choices moved from fatal to
safe, while 3 moved from safe to fatal. The game-clustered delta is −0.36
percentage points, 95% interval [−0.77, +0.06], so zero remains plausible.

This is a more direct signal than candidate calibration, but still a small,
retrospective policy effect. Every changed move is followed by the original
game's recorded continuation; the line is not re-simulated after that change.
It does not estimate win rate or Elo. The validation result supports a
separate shadow/arena gate, but the fusion remains experimental and the sealed
test remains unread. Choice logs, build coefficients and the comparison report
are retained under [`run-20261011`](run-20261011/); see
[`choice-ablation-20261011.json`](choice-ablation-20261011.json).
