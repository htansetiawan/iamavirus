# First representation and precision pilots — 2026-10-07

These are allocation experiments, not arena releases or Elo measurements. Source
is in `../../learning_experiments`; the experiment specs are in `../../specs`.

## Matched CNN versus attention

Same v3 split, seed 253, 1,000 updates, batch 4, window 32, task/player weights,
and **62,083 training decision presentations per arm**. Validation covers 64
whole games, both colors, **5,179 distinct decisions** with complete histories.

| Metric | CNN | Attention | Interpretation |
| --- | ---: | ---: | --- |
| Policy NLL | 2.6022 | 2.6667 | Worse; paired game 95% delta +0.0363 to +0.0920 |
| Policy top-1 accuracy | 28.06% | 28.35% | Inconclusive; paired interval crosses zero |
| Hidden-enemy NLL | 1.4508 | 1.4220 | Small improvement; interval barely excludes zero |
| Danger Brier | 0.04380 | 0.04115 | Improvement on this split |
| Danger recall at empirical 5% FPR | 17.71% | 38.74% | Better ranking, not a calibrated operating point |
| Value MSE | 0.9596 | 0.8925 | Lower; value is not a deployed search evaluator |
| Parameters | 1,872,394 | 1,631,826 | Attention has fewer parameters here |
| Time through final update | 227 s | 290 s | Attention trains more slowly in this implementation |

The intervals resample paired games; they do not cover training-seed variation.
Both danger heads miss every positive at the arbitrary 0.5 threshold after this
short pilot. Neither is ready to act as a veto. These checkpoints have far less
training than Fable's v3 model and must not replace it based on this table.

Decision: keep attention as a promising danger/representation hypothesis, with
the policy-likelihood regression explicitly open. Next comparisons are SSL
initialization and richer observation-derived belief inputs. Compression and
larger teachers remain separate axes; no combined change has been promoted.

See `cnn-vs-attention-1000.json` for exact denominators and intervals. Full runs
are under `/media/henrytan/seagate/iamavirus/astra/representations/v3-seed253/`.

## Inference engineering

All three untrained encoders (CNN, attention, compressed attention) match their
FP32 ONNX exports for varying batch and candidate counts. The compressed arm
has 730,994 parameters and a 512-element intermediate latent. This is a
capacity/graph check, not evidence that the bottleneck preserves trained skill.

The trained attention checkpoint also passes complete-history ONNX parity:
567 decisions, no failures, worst absolute output difference 3.10e-6.
See `attention-trained-export.json`. Fifteen focused correctness checks pass;
see `correctness.json`. The three-update CPU runs in `cpu-smokes.json` prove
optimizer/checkpoint plumbing only. Their SSL losses predate the masking fix.

## INT8 on Fable's trained v3 weights

16 validation games, 32 player histories, 1,108 decisions; each runtime feeds
back its own hidden state. Only constant-weight MatMul/Gemm operations are
quantized. Convolutions and unsupported operations stay FP32.

| Arm | Graph bytes | Top-1 agreement with FP32 | New / saved policy fatalities | Host p95 observe + score |
| --- | ---: | ---: | ---: | ---: |
| FP32 | 7,508,085 | — | Reference: 32 fatal proposals | ~1.00 ms |
| Partial INT8 | 2,867,695 | 98.29% | 1 / 0 | 0.729 ms |
| INT8 with FP32 GRU | 4,038,061 | 98.38% | 1 / 0 | 0.794 ms |

Timing is a shared-host diagnostic, not an arena guarantee. The policy's top
proposal is not the hybrid engine's final move. Keeping the GRU in float reduces
maximum state drift from 0.302 to 0.099 but does not remove the extra fatal
proposal. Both precision arms remain unpromoted. A slightly better average
danger Brier concealed the changed fatal proposal, demonstrating why the
tactical gate is necessary.

The first attempt at selective precision was invalid: ORT renamed Gemm nodes
before applying exclusions, producing the same graph hashes as broad INT8.
The corrected tool includes the rewritten names and asserts both recurrent
weight matrices are actually FLOAT. The invalid artifact is retained under
`build/astra-int8-v3-recurrent-fp32-audit/INVALID.md`; the reported corrected arm
is `int8-v3-recurrent-fp32.json`.

## SSL masking defect caught and corrected

The initial SSL pilot trusted the documented current-view channel layout.
Inspection of its metrics showed that every masked observed square was a
piece: visible empties were omitted. Both existing feature implementations
encode fog and visible empty in current plane 12, leaving plane 13 unused.
Other history channels retain visibility information; this is not proof that
the shipped model lacks all distinction between fog and visible empties.

That SSL run was interrupted and marked invalid for the intended objective
(`ssl-first-run-invalid.json`). Self-targets now come directly from literal
actor observation symbols, rank-reflected for Black, never from true boards or
outcomes. Regression tests include the actual existing feature builder. The
corrected run is `attention-ssl-pilot-v2`; it must finish and pass downstream
fine-tuning comparisons before any useful-representation claim.

The paired supervised CNN/attention comparison uses the same existing feature
contract on both sides and is unaffected by the SSL masking error. Production
features and weights have not been changed by this experiment.
