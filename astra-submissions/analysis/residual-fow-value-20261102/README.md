# Bounded SF residual passes development; fresh confirmation required

2 November 2026. The selected flat residual improves prediction on the reused
development-validation set. It earns a fresh confirmation experiment. **It is
not a held-out generalization result, a stronger playing bot, or an arena ZIP.**

The formula keeps calibrated Stockfish as a skip connection and adds at most
two log odds. Two board-conditioned heads modulate the correction by SF's
certainty. This tests learning a correction without reconstructing ordinary
chess value. Output heads start at zero; outcome targets only. No teacher
distillation or player identity is used.

Contract/source published on both mirrors at
`8ec6c5fd9665fc7ad53fe5423cc9d47ccff24fdd` before fitting. Plan SHA-256:
`97a83efd26f07cb836c35347a587fd6f8a50e0dd626f1503003a4c24228a2bce`.

## Development comparison

Both architectures train from scratch for 32 epochs on the same 193,517
positions, with identical optimizer/schedule and seed. They consume different
compute. Validation has 8,746 positions from 1,145 games; games receive equal
weight. It has informed previous architecture experiments and is explicitly
development data. Neither 237 nor 238's opened test is scored here.

| Model | Validation log loss | Brier | Hidden-threat log loss |
|---|---:|---:|---:|
| Raw SF | 0.491656 | 0.148187 | 0.358090 |
| Frozen calibrated SF | 0.467669 | 0.142238 | 0.326383 |
| Flat residual, selected | **0.446316** | **0.135454** | **0.294034** |
| Query residual | 0.446986 | 0.135862 | 0.296647 |

Both best checkpoints occur at epoch 3. The flat model wins the predeclared
validation selection. Its relative log-loss improvement is about 4.57%; Brier
also improves. The hidden-threat slice has 181 positions in 171 games. All
development requirements pass. Later epochs worsen validation; they are kept
in the curves, not used to replace the selected checkpoint.

One GPU run, original handle 89370, exits 0 in 99.54 seconds. The existing
service was not stopped; the launcher required a fresh empty compute-device
probe. No fit retry occurred.

## Native implementation and independent review

Flat payload: 640,392 bytes, median 9.37us per position on one CPU core.
Query payload: 561,288 bytes, median 45.00us. Encoding and whole-search cost
are not included. Both pass the fixed 50us/1MiB native budget. All validation
predictions match native C to maximum probability errors 1.06e-7 / 1.17e-7.
The observed maximum residuals are 1.793 / 1.974 log odds, below the bound 2.

Reviewer 64127 exits 0: independently reconstructs calibration, equal-game
metrics, all subgroup metrics, checkpoint/arm selection, every CPU/native
prediction and trained native timing. Neutrality, nonzero/extreme-head parity,
analytic gradients and address/undefined-behaviour sanitizer checks also pass.

An initial preflight failed under deliberately extreme output biases because
the C output dot product accumulated small terms onto a large bias, losing
precision before two heads cancelled. Adding bias after the dot product
fixes it under the unchanged 2e-5 logit tolerance. Initial handle 87526, exit1,
and its source are retained; corrected 82077 exits0 before any fitting. This
changes only Astra's new inference export, not the live engine or older models.

The zero correction preserves the **calibrated** baseline, not v37's raw leaf
map. Any later policy comparison must include calibration alone, and keep
terminal outcomes unchanged. The model does not repair missing belief worlds
or prove counterfactual value accuracy under another continuation policy.

## Next gate

Experiment240 freezes this flat checkpoint before selecting disjoint games.
Query is only a secondary comparator; it cannot be substituted after opening
the test. New data exclude every237/238 game, trajectory and canonical input.
An older-unused cohort and a new-date cohort are reported separately, with
ordinary-position and hidden-threat safeguards. Prediction confirmation would
earn a separate search-integration check, then full games if justified.

`model-evidence.tar.gz` retains both checkpoints, native exports, all curves
and validation predictions with per-member hashes. These are research
artifacts, not arena submissions. Source is under
`../../experiments/residual-fow-value-20261102/`.
