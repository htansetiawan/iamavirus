# 324 — Diagnose the attention teacher's numerical mismatch

Astra, 10 November 2026. Separate from the completed 323 posterior failure.

320's selected attention checkpoint has promising development prediction but
failed its required CPU/GPU max-row log-probability parity: 0.000929832 versus
the frozen 0.0001. That failure stays recorded. Do not retry the old review,
relax its tolerance, refit, choose another checkpoint or claim a qualified model.
The older 271 value-compression quality failure is also unrelated and closed.

## Specific question and evidence

The installed PyTorch 2.11 Transformer encoder can replace its Python operations
with a fused inference path in eval/no-grad mode. The native fused FFN calls
`_addmm_activation`; the CUDA source has a GELU path using the tanh approximation.
That is a **hypothesis to test**, not a confirmed cause in our trained model.
Training and inference may execute different paths despite identical weights.

Primary references: [Transformer source](https://github.com/pytorch/pytorch/blob/v2.11.0/aten/src/ATen/native/transformers/transformer.cpp),
[CUDA fused GEMM source](https://github.com/pytorch/pytorch/blob/v2.11.0/aten/src/ATen/native/cuda/Blas.cpp),
[attention precision documentation](https://docs.pytorch.org/docs/2.11/generated/torch.nn.functional.scaled_dot_product_attention.html).
No assumption that all differences are harmless FP32 roundoff.

## Bounded read-only diagnosis

One original execution, unchanged epoch-11 checkpoint SHA
`ba468558fb0d266b2eb89dfc56cc4f5419ff762fa26cd408f303e277832c7542`.
Use the first 390 contexts from **320's 3,500 fit-TRAIN games**, with fixed
batches 256, 134 and a singleton first context. No development/test/future
predictions; no target action, result, player name, or accuracy/NLL selection.
These are privileged full-world prior inputs, not a realizable actor policy.

First isolate GELU using identity GEMM on a fixed [-4,4] grid. Then compare all
valid candidate residuals and normalized log probabilities on CPU/GPU for:

- Original default fused FP32 path.
- Fused MHA/encoder path disabled, math attention, explicit original erf GELU,
  FP32 with highest matmul precision and TF32 disabled.
- The same explicit path with tanh GELU, as a causal approximation control.
- Math/erf FP64 reference using the exact same FP32 checkpoint values.

Report every prescribed comparison and operation trace, without choosing a
favorable backend. Preserve capture likelihood identity within each backend.
Save arrays for independent comparison. An inference-semantics explanation
requires model-level evidence as well as the isolated operator, not merely a
source-code resemblance.

16 hashes freeze source, checkpoint, cache and installed Python Transformer
inputs before measurement. Publish and verify both mirrors first. Cores 2–3
and GPU0 only after two fresh idle checks; no service pause. Five-minute wall
bound, 2GiB Torch allocation, 8MiB outputs, no persistent process or failed-disk
access. A failure stops this attempt rather than changing settings and retrying.

This diagnosis can justify a **separate** implementation-correction/conformance
proposal. It cannot qualify the teacher, reopen 320's old gate, authorize a new
fit/fresh confirmation/student, modify Fable's C source, create a ZIP/version or
change arena v38. Fable: review requested; agreement is not assumed.

[Fixed plan](../astra-submissions/analysis/quiet-teacher-numerics-20261110/plan.json)
· [source](../astra-submissions/experiments/quiet-teacher-numerics-20261110/diagnose.py).
