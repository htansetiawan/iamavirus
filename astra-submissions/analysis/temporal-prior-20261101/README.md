# Temporal opponent policy: positive predictive result, not a submission

1 November 2026. **Recent own-action context improves prediction of ambiguous
hidden moves and passes the pre-recorded predictive gate.** The next gate is
the actual capped belief update. No posterior, guard, search or Elo improvement
has yet been demonstrated, and no ZIP is produced.

## What was learned

The static control uses the current 39 move/visibility features and from/to
piece-square tables. The new model adds 52 features describing the previous
own action: piece-type transitions, whether this is the same piece, whether
that piece previously captured, reversal to its earlier square, continued
repeated-piece moves, consecutive captures and previous capture value.
These are fitted coefficients, not hand-set bonuses or opponent-name rules.

Both conditional-logit models were fitted from zero on the same 77,654 moves
from 1,200 games. The loss normalizes over every legal action. L2=1e-4 and the
optimizer limit were fixed before fitting. GPU optimization took 3.42 seconds
for the static control and 3.47 seconds for the temporal model; feature
extraction, I/O, validation and reporting are additional work. Gradient bounds
in `predictive-audit.json` show the small remaining optimization error cannot
explain the observed predictive gain. No large teacher or GPU inference is
required for this model.

## Held-out results

| Measure | Static | Temporal | Improvement |
|---|---:|---:|---:|
| Validation ambiguous conditional NLL | See fit/validation.json | See fit/validation.json | 0.02893 nats |
| Test all-move NLL, 34,510 moves | 2.47393 | 2.44275 | 0.03117 nats |
| Test ambiguous conditional NLL, 21,032 moves | 2.09354 | 2.06468 | 0.02886 nats |

Lower NLL is better. Whole-game bootstrap over 600 test games gives a 95%
interval of **0.02073–0.03775 nats** for ambiguous conditional improvement.
The pooled Instructors/duck/HYPOTHERMIA improvement is **0.02816 nats**.
Parameters were hashed before validation or test scoring; validation passed
the declared 0.02-nat threshold and test was scored once. Per-decision scores
are retained, and `audit.py` independently recomputes the comparison and gate.

| Opponent | Ambiguous moves | Conditional improvement, nats |
|---|---:|---:|
| Greek Gift | 1,599 | 0.01385 |
| Knight Vision | 2,294 | 0.01226 |
| Strongly Invisible | 3,077 | 0.01146 |
| Decent Chess Bot | 2,282 | 0.03727 |
| Crimson Fog | 1,772 | -0.00071 |
| Instructors | 2,546 | 0.00959 |
| Mist Opportunities | 2,972 | 0.08061 |
| duck | 2,367 | 0.02797 |
| HYPOTHERMIA | 2,123 | 0.05065 |

These opponent slices are descriptive, without individual confidence claims.
The result does not establish universal persistence after a capture: some
fitted terms favour moving or returning with the same piece. It would be
wrong to replace this fit with a fixed "capturer stays put" rule.

## Data and information contract

`data-v2/manifest.json` pins 1,200/300/600 whole games from Oct20–27 / Oct28–29 /
Oct30–31. Selection uses a fixed ID hash and no outcomes. Complete move
sequences are deduplicated across all splits. The older 140-game king-risk
calibration corpus is excluded by both ID and sequence. The initial manifest
had seven overlapping validation/test games; it was superseded before any
fit or scoring. Its receipts remain, and its training input is identical.

The native extractor validates 182,233 recorded boards and both player views.
It produces 4,088,874 legal-action rows. Compatibility with the other player's
next view is an evaluation label only, never a feature or the training
normalizer. Conditional metrics include only nonterminal actual moves with
at least two compatible alternatives. Training includes singleton decisions
and terminal mistakes in its ordinary all-action likelihood.

This is conditional on a **known true parent and known past trajectory**.
That is valid supervised data, but not an online bot's knowledge. The future
engine must retain the recent action separately for each hypothesized path;
it cannot read the true replay's hidden moves. Rebuilds need unknown context,
and merging different contexts must preserve a mixture or explicitly measure
the approximation. More accurate predictions with supplied true histories
do not prove more accurate reconstructed histories.

## Native inference

The exported model has **859 float32 parameters, 3,436 bytes**. Its temporal
part is sparse: at most seven terms contribute per move, so inference uses
direct indexed additions instead of scanning all 52 extra columns.

On 17,755 validation positions / 578,765 legal actions, dense and sparse
temporal scoring agree within 1.70e-7. Python float64 and native float32
played-move log probabilities agree within 1.95e-6. The isolated CPU benchmark
took 0.1698 seconds for static scoring and 0.1731 for temporal scoring, about
2% more. This is a single microbenchmark, not a runtime guarantee for belief
expansion or a full-game clock test. `native-parity.json` pins the header and
binary hashes.

Feature invariants pass optimized and ASan/UBSan checks for both colours,
history isolation, repeated pieces, en passant, promotion, castling and
captures. Three likelihood tests check finite-difference gradients, all-action
normalization, conditional-probability factorization and static ablation.

## Next gate

Integrate a small recent-action context into an isolated belief implementation.
The required state fits in a uint32: last Move16, post-promotion type3,
captured value4, known1 and continued1. Compare the static model with ordinary
board merging, static with context retained, and temporal with context
retained. This separates a memory/merging effect from a learned-prior effect.
Measure truth support, event probabilities, diversity, rebuilds and runtime
under the same cap and seed before any policy/strength gate. Full fitted
models are used for this first diagnostic; the deployed cheap-model fallback
and empirical history blending require separate checks afterward.

## Reproduce

Source: `astra-submissions/experiments/temporal-prior-20261101/`.

```
PYTHONPATH=astra-submissions/experiments/temporal-prior-20261101 .venv/bin/python -m unittest discover -s astra-submissions/experiments/temporal-prior-20261101 -p test_fit.py -v
.venv/bin/python astra-submissions/experiments/temporal-prior-20261101/audit.py astra-submissions/analysis/temporal-prior-20261101
```

For new fits, use a new output directory and the frozen `data-v2` inputs.
The compact compressed replay inputs and model/score artifacts are tracked.
The approximately 103 MB of regenerated feature files are ignored locally;
`prepare.py` reproduces them from the input traces and pinned native source.
