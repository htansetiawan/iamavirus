# Attention teacher arithmetic diagnosis — 10 November 2026

**The installed fused CPU and GPU Transformer paths apply different GELU
approximations. This explains the dominant tested mismatch with unchanged
weights.** It is an inference-semantic difference, not evidence that another
model fit is needed. 320's original failed gate remains failed.

Original session33909 exits0 once, after two free-GPU checks (750MiB,0%, no compute
apps). Measurement takes3.78s, peak Torch GPU allocation192.9MB. No service is
stopped; the GPU/core lease is released. Source publication123edacf is verified
on both mirrors before the first forward. The independent stored-array/scalar
review verifies all84 metrics and16 dependency pins. No new fit or labels.

## Isolated operator and model evidence

On a fixed [-4,4] grid with identity GEMM, CPU `_addmm_activation(use_gelu=True)`
matches its erf GELU exactly and differs from tanh by0.000473499. CUDA differs
from erf by0.000474215 but matches tanh within0.000005312. These references use
the installed Torch GELU operators. The GPU fused implementation has a small
additional approximation error, so this is not exact equality to explicit tanh.

The unchanged epoch11 checkpoint is then evaluated on390old fit-TRAIN contexts,
including every valid candidate, at three prescribed shapes. No target action,
outcome, opponent name, development/test/future score or NLL is used.

| Batch shape | Default CPU/GPU max logp gap | Explicit math/erf FP32 gap | Math/erf FP64 gap |
| --- | ---: | ---: | ---: |
| 256 |0.000810623|0.000002861|5.33e-15|
| 134 |0.000724792|0.000002861|4.44e-15|
| 1 |0.000341415|0.000003815|3.55e-15|

The tanh causal control agrees with itself across CPU/GPU to3.82e-6 or better,
but differs from the FP64 erf reference by up to0.000813393 in batch256.
Default CPU is close to explicit erf (max2.87e-6); default GPU is close to
explicit tanh (max9.54e-6), while it differs from explicit erf by0.000809193.
Operator traces confirm `_transformer_encoder_layer_fwd`/`_addmm_activation`
in both default paths; the explicit controls use math SDPA and separate GELU.
These paired controls make the GELU explanation stronger than merely observing
a backend gap. Minor remaining differences can still come from attention/GEMM.

All configured paths preserve capture likelihoods within their own backend.
The teacher checkpoint SHA remains
`ba468558fb0d266b2eb89dfc56cc4f5419ff762fa26cd408f303e277832c7542`.
Installed Torch2.11.0+cu128, CUDA12.8; highest matmul precision and TF32 disabled.
These flags are measured for this run, not reconstructed facts about the old
terminated320process. Complete aggregate comparisons and operator names are published; numerical arrays remain local.

## Consequence and concrete correction proposal

The original training code uses grad-enabled Transformer operations; the fused
encoder inference path is disabled during training. Its configured GELU is erf.
A separate corrected inference specification should therefore keep the trained
weights, explicitly use the unfused encoder/MHA path with math attention and
original erf GELU, and retain highest FP32 precision. This removes the tested
semantic switch rather than loosening320's tolerance.

Next conformance should verify that exact specification across all original
fit-TRAIN contexts, variable batch sizes and capture/normalization controls,
with the same unchanged weights. It needs a new frozen implementation contract.
Only then design separate held-out prediction confirmation; do not re-run320's
old review or relabel its failure. That future study must report the corrected
function's actual scores, not silently reuse the old GPU fused scores.

The corrected reference is an offline teacher candidate, not a fast arena prior:
587,649parameters per hypothetical parent still needs measured distillation and
native cost/posterior gates. No model qualification, student, C integration,
replacement ZIP, version reservation or arena action has occurred.

[Plan](plan.json) · [all comparisons](result.json) ·
raw arrays (retained locally; SHA in result.json) · [independent audit](independent-review.json).

Primary implementation references: [Transformer FFN](https://github.com/pytorch/pytorch/blob/v2.11.0/aten/src/ATen/native/transformers/transformer.cpp),
[CUDA fused GEMM](https://github.com/pytorch/pytorch/blob/v2.11.0/aten/src/ATen/native/cuda/Blas.cpp),
[Python encoder path conditions](https://github.com/pytorch/pytorch/blob/v2.11.0/torch/nn/modules/transformer.py).

Publication boundary: automatic approval review rejected exporting the raw
`arithmetic-arrays.npz` because it classified derived training-context arrays
as sensitive. That file remains local and is excluded from the publication
scope. Source, aggregate results, artifact hash and the independent audit are
reviewable in the repository; no approval to export those arrays is assumed.
