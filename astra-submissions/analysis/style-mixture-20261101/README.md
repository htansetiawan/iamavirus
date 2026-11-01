# Stationary style mixture: development gate failed

1 November 2026. **No belief-filter integration, fresh-test evaluation or
candidate ZIP.** The observation-adapted mixture improved average move
prediction, but not enough of the uncertainty that remains after an
observation. This rejects the frozen configuration; it does not reject all
opponent modelling. The taxonomy reveals a useful tradeoff to preserve.

## What was implemented

Three persistent latent experts, each with 39 residual coefficients over a
shared static39 + piece-square base. The type is shared across one game-side;
training marginalizes it rather than using team identities. All actions enter
the normalization. A one-expert residual control uses the same features and
regularizer. The proposed eventual filter would store three joint type
masses per physical board, merging histories componentwise instead of
consuming the board cap with separate action-context entries. That filter
was deliberately not implemented before the predictive gate.

The frozen source/contract was published at `df886e9` before fitting. Data:
1,200 training games, 77,654 positions / 2,423,970 legal actions / 1,736 game-
side sequences. Development validation reuses 300 games from the previous
temporal study: 17,755 positions, 10,855 with ambiguous observations. These
are NOT an untouched confirmatory set. We did not score the previous test
or select a new test after the gate failed.

All predictive diagnostics know the true parent board. The observation-
history arm adapts using earlier observation classes, while the true-move-
history arm uses earlier actual actions as an explicit oracle. The current
observation is used only after scoring, never to select current mixture
weights. No arm is a deployable posterior or a policy benchmark.

## Measured prediction

Lower NLL is better. Conditional likelihood renormalizes over legal actions
consistent with the same next observation, excluding terminal actual moves.

| Predictor | All-move NLL | Ambiguous conditional NLL | Conditional gain vs static |
|---|---:|---:|---:|
| static | 2.534034 | 2.116788 | +0.000000 |
| pooled_residual | 2.533939 | 2.116686 | +0.000102 |
| mixture_reset | 2.533443 | 2.113864 | +0.002924 |
| mixture_view_history | 2.523635 | 2.115175 | +0.001613 |
| mixture_true_move_history | 2.520483 | 2.107386 | +0.009402 |

The primary observation-adapted arm gains **0.001613 nats** over static and
**0.001511** over the one-expert control, below the predeclared **0.05** gate.
Its all-move NLL improves by 0.010400, and its reference-team conditional gain
is +0.004425 (Instructors/duck/HYPOTHERMIA). Those safeguards pass, but they
do not replace the primary gate. The true-action oracle gains only 0.009402
on the same ambiguous metric; it cannot be substituted for the primary arm.

Adapting from observations is slightly worse on ambiguous choices than
resetting the learned mixture each move. The all-move improvement therefore
does not establish better discrimination among the hidden alternatives the
belief must retain. Posterior calibration and playing strength remain
unmeasured.

## What the taxonomy adds

All 19 taxonomy slices are reported in `taxonomy-audit.json`; selected
strategically relevant rows below are descriptive development results. These
labels can use the true board and future moves; none enters the predictor.

| Tag | Ambiguous moves | Conditional gain vs static |
|---|---:|---:|
| king_threat_unseen | 262 | +0.075230 |
| queen_raid | 238 | +0.038242 |
| queen_exposed_unseen | 6 | +0.013975 |
| capture_unseen | 250 | +0.005090 |
| king_move | 1724 | -0.016315 |
| sacrifice | 72 | +0.014038 |

The +0.075230 gain on 262 ambiguous unseen-king-threat moves is worth keeping
as a research clue. King-move prediction worsens by 0.016315 on 1,724 ambiguous
moves. These are overlapping, correlated, post-fit subgroups, with no claim
of statistical confirmation or improved king safety. In particular, six
ambiguous unseen-queen-exposure examples cannot establish queen-guard quality.
Do not relax the failed gate or choose a new coefficient configuration from
these slices. A future targeted hypothesis needs its own frozen design and
fresh evidence, not retroactive promotion of this fit.

## Correctness, resources and artifacts

- Three numerical tests passed: independent action/objective calculations,
  finite-difference gradients, sequence/online likelihood identity, chronology,
  separate colours, ignored team IDs, identical-expert reduction.
- Baseline scores match the previous independent loader/scorer on all 17,755
  validation decisions, maximum error **3.55e-15**. All 300 replay hashes match.
- Both fitted model hashes were written before validation and rechecked
  afterward. `fit/` holds parameters, priors, optimizer traces and hashes;
  `validation-scores.jsonl.gz` preserves every prediction, not only summaries.
- Both optimizers stopped before their iteration cap: pooled 38 iterations,
  mixture 80; maximum mixture gradient 2.25e-6. No restart or hyperparameter
  search. `execution.json` records terminal exit zero, 396 seconds wall time.
- CPU only, two low-priority threads on cores 0–1. Occupied GPU and unrelated
  services were untouched. Resource contention affects timing, not this claim
  about deterministic fitted scores. Our reservation is released.

Separately, public ingestion listed 60 recent all-team games, fetched and
accepted 56, reused four cached replays, with zero quarantines/errors. These
new games were not inserted into the frozen training/validation data. Receipt:
`arena-refresh.json`.

The exact commands and pinned files are in `plan.json` and `execution.json`.
Use a new output directory for a reproduction; do not overwrite this evidence.
