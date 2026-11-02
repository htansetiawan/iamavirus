# 245: frozen recurrent risk as a complement to mist-c

The 11 October attention/GRU head added a small predictive signal to the old
hybrid particle risk. It was not deployed. The 1 November mist-c scalar
calibrator improved probabilities but its decision integrations failed.
Unlike a scalar monotone map, fusion with an action-dependent recurrent signal
can change the ordering of moves. This is the new question, not another global
threshold sweep or a claim that a history network has never been tried.

The exact old ONNX graphs have been recovered from the migrated drive and
match their original hashes. A current CPU preflight passed on two original
king-calibration TRAIN games, one per colour, without fitting or using tactical
labels for evaluation. Keep those observations in the record.

Use only the 80 games marked TRAIN in the existing 140-game v35 calibration
dataset. Sort by completion time and game ID: first 50 for fitting the small
calibrators, last 30 for a development readout. These are reused development
games, not a new sealed test. No old validation/test game is scored. The frozen
attention model was trained earlier; do not update any network weights.

Replay every own observation and past own move through the feature-v2 tracker
and recurrent graph. Score exactly the recorded v35 collector candidate set.
Join immediate own-king-loss labels and risk estimates only after inference.
Opponent identities, true boards, labels and future actions are not model inputs.
Record current feature and rule-source hashes; this is CPU compatibility with
the existing ABI, not a rerun of old PyTorch/native export parity.

Fit two methods using the existing tested calibration implementation:

- Baseline: intercept plus nonnegative coefficient on standardized clipped
  sharp-risk log odds.
- Fusion: the same terms plus a nonnegative coefficient on the frozen neural
  danger logit. Standardize from the first 50 games only. Keep the existing
  ridge 0.001, clipping 1e-4, optimizer and whole-game bootstrap unchanged.

Report decision-weighted log loss and Brier, separately for played moves, and
within-decision opposite-label ranking errors. Ranking uses sorting and grouped
ties, O(M log M) per M candidates; tied risks count half an error. All-safe or
all-fatal decisions contribute no ranking comparison and are counted separately.

To earn a fresh v37 confirmation proposal, require: positive neural coefficient,
at least 2% lower development log loss, lower Brier, no worse played-move log
loss, and strictly lower mixed-decision ranking error. The 30-game bootstrap is
reported, not a declaration of generalization from already-reused data. A
negative readout stops this reuse path; do not tune, replace the model or
reinterpret one favourable subgroup as a pass.

One CPU core (6), CPUExecutionProvider only, one inference thread, ten-minute
total wall cap. No GPU or neural fitting. The 244 continuation job is unchanged
on 0–1/4–5. No engine, guard, belief, release or arena changes occur here.
