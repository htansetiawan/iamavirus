# Larger training models and smaller inference models

The user's proposal adds a useful axis: offline training capacity need not equal
the CPU model submitted to the arena. There are three distinct experiments:

1. A larger **trained teacher** can supply soft policy rankings, hidden-piece
   distributions and danger estimates to a smaller student. The teacher must
   earn those targets through held-out quality. More parameters alone are not
   evidence of better teaching.
2. **Self-supervised EMA teacher/student** learning bootstraps representations
   from actor observations without externally supplied labels. The current
   implementation uses teacher and student of equal capacity. It is not yet
   a large-teacher distillation experiment.
3. **Lower precision inference** reduces representation size and may reduce
   latency. It changes numerical behavior and needs its own tactical gate.

For an initial larger teacher, keep the same legal-candidate output interface
but allow a wider/deeper attention encoder and longer history context offline.
Then distill a compact encoder with policy-distribution, hidden-piece and danger
objectives. Compare against directly training the student using the same total
compute. The first CNN/attention comparison is complete and mixed: attention
improved danger ranking but worsened policy likelihood. A larger teacher has
not yet been implemented or trained, and was not folded into that comparison.

There are two deployment paths to compare: run the larger model directly at
lower precision, or distill it to a smaller model and then quantize the student.
Quantization lowers numerical precision; it does not remove layers or reduce
the number of mathematical operations. Distillation can reduce network size
and work as well. A larger model must first improve held-out predictions under
the same information boundary before it earns either deployment experiment.
The original [knowledge-distillation paper](https://arxiv.org/abs/1503.02531)
motivates transfer from a more expensive teacher; it does not establish an
improvement for our bot.

Our current FP32 graphs already occupy only 7.51 MB, so weight storage is not
the binding arena constraint. A useful result buys better decisions within the
CPU time budget, not merely a smaller ZIP. Report full hybrid move latency and
clocked results in addition to neural inference time. Distillation and direct
larger-model inference remain research paths, not completed releases.

## Precision choices

- FP32 is the current inference control.
- FP16/BF16 are 16-bit floating point, rather than generic "Q16". They save
  weight storage, but CPU speed depends on the actual kernels and hardware.
- INT8 is the first integer-quantization experiment. The ONNX implementation
  currently quantizes constant-weight MatMul/Gemm nodes; the CNN convolutions
  and other operators stay FP32. Report actual quantized elements and bytes.
- Mixed precision can retain the recurrent state transitions or sensitive
  output layers in FP32. Try this when broad quantization changes tactical
  rankings. Calibration-aware or quantization-aware training is a later option.

[ONNX Runtime's documentation](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)
distinguishes dynamic activation quantization, static calibration and
quantization-aware training, and recommends comparing affected tensors when
accuracy degrades. We first use dynamic quantization so no test or validation
examples are fitted as activation calibration data.

## The gate must include recurrence and decisions

Feed the FP32 and quantized models their **own** previous hidden state at every
observation. Supplying the quantized model with FP32 state would conceal error
accumulation. Compare all legal candidate rankings, top-k coverage, probability
calibration, and truth-labeled immediate king exposure of changed proposals.
Then measure the actual hybrid engine's decisions and complete clocked games.

The first v3-weight audit covers 16 validation games / 1,108 decisions. Partial
INT8 reduced the two graphs from 7,508,085 to 2,867,695 bytes. Top-1 policy
agreement was 1,089/1,108 (98.3%), but policy-only immediate fatalities rose
32→33, with one new and no saved fatal choice. Shared-host p95 observation plus
candidate scoring was 1.003→0.729 ms. Aggregate danger Brier improved slightly,
yet missed that added fatal choice. Maximum recurrent-state absolute difference
was 0.302. This is an explicit reason **not to promote** broad INT8 from average
metrics alone. It is not a claim about the hybrid search's resulting strength.

The next bounded precision ablation kept GRU nodes in FP32 on the same games.
Graph size was 4,038,061 bytes, maximum hidden-state difference fell to 0.099,
and top-1 agreement was 98.38%; the same extra fatal proposal remained. Neither
arm passes promotion. Any promising precision variant still needs a larger
held-out tactical set and a hybrid decision comparison. Current artifacts are
experiments, not arena releases.
