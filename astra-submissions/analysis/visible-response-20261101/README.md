# Visible response policy: predictive result and native implementation

1 November 2026. The attention-teacher / distilled-student experiment passes
its frozen predictive gate. The student has a checked native C implementation.
It has **not** been integrated into search or belief updates, tested in complete
games, or packaged as an arena submission.

## What was learned

Predict an opponent's next action from its current 64-square observation and
legal candidates reconstructed from permitted private history. No true hidden
pieces, opposing observation, team identity, outcome or future move is an input.
The recorded action is the supervised target. This is a memoryless policy,
not a complete remembered information state. Distillation uses the teacher's
distribution on training examples; this is supervised imitation, not self-play
reinforcement learning or self-supervised representation training.

The frozen chronological split is 4,000 training games (October 20–27), 600
validation games (October 28–29), and 1,000 test games (October 30–31), selected
without outcomes and deduplicated by complete move sequence. Training contains
266,724 target decisions. All 499,429 replay frames across the splits passed
validation, with zero actor-derived legal-set mismatches. See
[the design](../../experiments/visible-response-20261101/README.md),
[manifest](manifest.json), and [data receipts](data-receipts.json).

The 300,737-parameter attention teacher uses two transformer blocks with four
heads and width 128. Its 68,417-parameter student uses two small board layers
and an action scorer. The baseline is a fitted 795-parameter observable linear
move scorer. **It is not v37's full-board move model:** outperforming this
baseline does not establish an improvement over the deployed engine.

Model choice and hashes were frozen using validation results before test
evaluation. The distilled student was selected. There was one training seed
and no architecture sweep.

| Test after own move eight, 47,010 decisions | Negative log likelihood, lower is better | Top-1 accuracy |
|---|---:|---:|
| Linear baseline | 2.86564 | 23.21% |
| Direct student | 2.75187 | 25.30% |
| Attention teacher | 2.69167 | 26.04% |
| Distilled student | 2.72440 | 25.42% |

The chosen student's paired gain is **0.14124 nats**, with a whole-game
bootstrap 95% interval of **0.13371–0.14900** (986 test games with eligible
decisions). The Instructors/duck/HYPOTHERMIA subset improves by 0.14625 nats
on 17,218 decisions. Both meet the pre-recorded predictive screen. These
probability scores are not estimates of win rate or Elo.

Of the post-eight test inputs, 45,260/47,010 (96.28%) were not present in
training as an identical current-view/legal-set pair. Their gain is 0.13414
nats. See [test results](test-results.json), [decision](decision.json), and
[the post-fit audit](postfit-audit.json). Compact per-decision score arrays
and all four models are preserved under `scores/` and `models/`.

## What the taxonomy reveals

The 19 taxonomy labels were joined **after** model selection and scoring, for
diagnosis. They were not inputs, training targets or sample weights in this
experiment. Positive numbers below mean better likelihood than the linear
baseline; groups overlap and these are descriptive post-fit comparisons.

| Recorded move category after own move eight | Decisions | NLL gain |
|---|---:|---:|
| Unseen king threat | 1,120 | +0.24601 |
| Queen entering the opponent's half | 2,073 | +0.29746 |
| King move | 7,167 | +0.15580 |
| Capture by a piece hidden from its victim before the move | 4,804 | **−0.06667** |
| Queen exposed to an unseen attacker | 72 | +0.01941 |

The surprise-capture regression matters despite the positive aggregate score.
Distillation also worsens that category relative to the direct student by
0.04219 nats. This is evidence to inspect before decision-level integration,
not a reason to switch the frozen model after seeing test labels. The 72
queen-exposure decisions do not measure a queen guard's missed-loss or
false-rejection rate. No subgroup result changes the recorded gate.

## Runtime and correctness

The exported FP32 student occupies **273,684 bytes**. Native inference uses
sparse one-hot gathers and shares the board contribution across candidates;
it requires no GPU or BLAS. Across 1,024 validation queries, maximum native
versus PyTorch FP32 probability error is 8.89e-7. Median single-core latency
is 25.64 microseconds and p95 is 30.52 microseconds, including Python/ctypes
overhead (median 33 candidates). This is a local kernel measurement, not
whole-engine or arena throughput.

Five model/input tests pass, including removal of true-board/opponent-view
data, label exclusion, Black canonicalization, action-order invariance and
the distillation loss. Native AddressSanitizer/UndefinedBehaviorSanitizer
tests pass for loading, truncated files, action bounds, normalization and
invalid inputs. See [native parity](native-parity.json),
[sanitizers](native-sanitizer.json), and [preflight](preflight.json).

The native weight SHA-256 is
`45a41cf4ecaae9324472ae93a81b349d597cec20364a7c73ef66e513df077c97`.
Source is under
[`experiments/visible-response-20261101/`](../../experiments/visible-response-20261101/).

Training initially waited for an existing video-generation job without touching it.
The fit started after two free-GPU checks and completed in 226.87 seconds,
using 400,734,720 bytes of peak PyTorch GPU allocation. Training and audits
are complete; Astra's associated GPU/core reservation is released. The
52 MB packed dataset and temporary checkpoints remain in the ignored local
build directory while the external drive is unmounted.

## Boundary before promotion

This result earns a native prototype, which now exists. A separately frozen
decision experiment must test integration into data-biased CFR, including
coverage, surprise captures, overhead and regressions against unchanged v37.
The candidate must subsequently pass complete-game testing before an arena
release is justified. Belief weights, king/queen guards and the active bot
have not changed as a result of this fit.
