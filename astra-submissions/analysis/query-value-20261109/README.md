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
