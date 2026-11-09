# Relational query compression: one development fit

The retained nonlinear FOW teacher predicted outcomes better than calibrated
Stockfish; the flat distilled student failed its quality gate. This tests
whether a small relational bottleneck retains more of that signal than the
flat model. It follows the already proposed Astra query-attention branch.

Architecture:64square tokens, width64, eight learned queries with one cross
attention and one latent self-attention layer, then a value head. Inputs are
the same piece/visibility/castling/EP tokens and halfmove count as the teacher.
It is a continuous latent representation, with no VQ codebook or quantization.
Pair counts and parameter size alone do not prove CPU speed or strength.

One fixed8-epoch fit with equal outcome/teacher loss, same training/validation
corpus and per-game weights. The already opened old test fold is not scored.
Validation selects the epoch; this is development evidence. To justify fresh
temporal confirmation, require at least2% validation log-loss improvement
over the better raw/calibrated Stockfish control, no worse Brier, no worse
log loss than the retained flat student, and fewer parameters than that
160,065-parameter student. No sweep or test-based refit follows a failure.

A development pass does not permit deployment. Fresh game-level evaluation,
native parity/inference cost (the existing25microsecond contract), sampled
world tests and full-clock games remain necessary. Real replay outcomes are
off-policy labels, not equilibrium/CFR values; these features omit histories
and beliefs. A frontier value cannot select an action excluded by the root
guards, which is why the guard-control branch is being tested separately.

GPU launch requires a new host probe: utilization below10%, memory below2GiB,
and an explicit reservation. No existing service is stopped. One GPU job on
device0, CPU4–5,30minute hard training bound with a31minute outer timeout.
Large original dataset/teacher are reused by verified hashes; new checkpoint
is small and stays under the ignored local work directory. All first-attempt
failures are retained. Native CPU preflight verifies shape and finite gradients.

Sources: [model](../../experiments/query-value-20261109/model.py),
[training](../../experiments/query-value-20261109/train.py),
[admission/launcher](../../experiments/query-value-20261109/launch.py).

## Completed: close this configuration

Original87395 exited0 in24.34seconds; eightepochs ran and validation selected
epoch8. The73,345parameter model uses293,380bytes of FP32 parameters, about
46% of the flat student's parameter count. It improves on that student a
little, but fails the stronger control:

| Validation model | Log loss | Brier |
|---|---:|---:|
| Raw archived SF | 0.49166 | 0.14819 |
| Train-calibrated SF | **0.46767** | **0.14224** |
| Retained attention teacher | 0.46363 | 0.14435 |
| Retained flat distilled student | 0.47254 | 0.14706 |
| New query student | 0.47051 | 0.14701 |

The query student fails both log-loss and Brier requirements against calibrated
SF. It would still lose to that control without the2%margin. The teacher's
own validation gain is only0.86%, so the2%development target is demanding;
that qualification does not change this candidate's negative comparison.
These validation data select the model and are not a fresh confirmatory set.

Independent CPU review62668 exited0. It reproduces every metric by averaging
per-game losses, verifies epoch selection and saved hashes, and predicts all
8,746validation inputs from the checkpoint. Maximum CPU/GPU probability
difference7.73e-5; CPU log loss differs by9.54e-7 and the failed gate stays
failed. The old test fold is not evaluated in either script.

No test evaluation, native optimization, search integration, additional fit or
threshold change follows this configuration. Continuous query compression
remains a broader idea; this single eight-epoch design did not meet the bar.
The GPU reservation is released. Checkpoint, predictions and source are
preserved in model-evidence.tar.gz with an adjacent hash/member manifest.
