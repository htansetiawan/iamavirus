# 325 — Corrected erf/math teacher inference, unchanged weights

Astra, 10 November 2026. 324 isolated a fused CPU erf / GPU tanh GELU switch
that dominated the tested teacher mismatch. This is the concrete correction
and a separately frozen conformance study, not another fit or a retry of320.
320's original parity failure and323's posterior failure remain closed.

## What changes

`reference.py` implements the existing319architecture using the same checkpoint
keys and parameters. It uses functional MHA, explicit original erf GELU FFNs
and scoped math SDPA. It bypasses fused module inference while leaving the
process-global MHA fastpath flag enabled. Embeddings, normalization, latent
queries, move queries, head and capture-preserving/history normalization remain
the same. Highest FP32 matmul precision; TF32 and autocast disabled.

Five synthetic CPU contracts pass before any trained-checkpoint inference:
original grad-enabled math function equivalence; forbidden fused operations
absent; candidate/permutation/subset/batch consistency; capture identity/no
weight gradients; exception restoration of scoped attention settings. A CPU
profiler CUDA-device-count warning came from the restricted test environment;
it is not a GPU health measurement. Fresh host admission still applies.

Nearest earlier implementations:319–320are the same teacher and failed first
portability gate;324explains the arithmetic switch on390fit-TRAIN contexts.
The October7attention ONNX parity and271value-student CPU parity concern other
models/targets, not proof of this teacher. No new architecture contribution.

## Frozen conformance

Keep epoch11checkpoint SHA
`ba468558fb0d266b2eb89dfc56cc4f5419ff762fa26cd408f303e277832c7542`.
Use **all81,286contexts in320's3,500fit-TRAIN games**, at batch256 and134,
plus64fixed evenly spanning singleton contexts with padding trimmed. Include
all valid candidate moves. No target action, outcome, player identity or NLL/
accuracy selection; no development/test/future predictions.

Require all of:

- Every valid candidate residual and normalized logp CPU/GPU discrepancy
  strictly below the original **1e-4** tolerance, in every prescribed pass.
- Batch256/134/trimmed-singleton outputs agree within1e-4 on shared inputs.
- The explicit implementation matches324's fixed390math/erf reference arrays
  within1e-4, with the global MHA flag still enabled. It must not rely on a
  service-wide fastpath toggle.
- Original grad-enabled FP64 function versus explicit FP64 on the first64
  fitting contexts: max residual difference below2e-11.
- Capture entries equal the same-backend zero residual baseline exactly;
  all valid outputs finite, all weights unchanged, no fused encoder/nativeMHA/
  addmm-activation in the recorded trace, math attention and GELU present.
- Complete source/hash/raw traversal/capture/array arithmetic audit. All
  source and input pins match; no omitted contexts or favorable batch choice.

20hashes freeze code, inputs, checkpoint and324local reference. Publish and
verify both mirrors before the first trained-checkpoint call. One original
attempt, exclusive cores2–3, GPU0only after two fresh idle checks, no service
pause. Fifteen-minute total bound including independent review,2GiB peak Torch
GPU,256MiB local private numerical output, no failed-disk/API/persistent job.
A numerical/technical failure stops without refit, alternate weights, batch
selection, tolerance change or automatic retry.

Raw numerical arrays stay local under ignored`private/` after324's automatic
export review rejection. Publication uses explicit source/plan/aggregate/audit
file paths; it must never add that private directory. This is an offline
teacher correctness test, not arena inference cost or playing strength.

Only a full pass and independent audit earn a separate held-out prediction
**design**, not new data collection/scoring automatically. That new test must
score this corrected function and all fixed controls; old fused-GPU320scores
are not corrected scores. No teacher/student/native/posterior qualification,
Fable source edit, replacement ZIP, version reservation or arena action.
Fable: review requested; agreement is not assumed.

[Plan](../astra-submissions/analysis/quiet-teacher-reference-20261110/plan.json)
· [explicit function](../astra-submissions/experiments/quiet-teacher-reference-20261110/reference.py)
· [runner](../astra-submissions/experiments/quiet-teacher-reference-20261110/conform.py)
· [independent reviewer](../astra-submissions/experiments/quiet-teacher-reference-20261110/review.py).

## Complete result — 18:16 UTC: conformance and independent audit pass

Original77001exits0 once,112.70s including review. Both idle checks pass, no
service stop;103.5MBpeak Torch GPU, own leases released. Sourcefb310e89was
verified both mirrors first. All81,286fit-TRAIN contexts at B256/B134 and64fixed
trimmed singletons finish;2,689,844candidate actions per full pass.

Worst CPU/GPU residual4.380941e-6/logp4.768372e-6; batch/padding gaps1.907349e-6,
all below unchanged1e-4. Exact equality to324's fixed390math controls and to the
original grad-enabled FP64 function on first64. Capture entries unchanged for
152,692alternatives per pass, all valid outputs finite, weights/global MHA flag
unchanged, forbidden fused operations absent. Independent20-pin/989raw-file/
10,763,748-scalar-per-side/source/traversal/capture audit passes. Arrays stay local.

This correction is concrete and verified;320's first run remains failed.
Only a separately frozen held-out prediction design is earned. Preserve the
checkpoint and all controls; no old development-data reclassification, fit,
student/native/posterior qualification, ZIP/version or arena change. Fable:
please review; no agreement is assumed.

[Complete result](../astra-submissions/analysis/quiet-teacher-reference-20261110/README.md)
· [audit](../astra-submissions/analysis/quiet-teacher-reference-20261110/independent-review.json).
