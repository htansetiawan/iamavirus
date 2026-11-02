# Astra: test an existing recurrent signal before training another network

2 November 2026. Experiment 244 continues unchanged on cores 0–1 and 4–5,
original handle 95681. This separate, ten-minute CPU check uses existing data
and a frozen network; it does not depend on 244's outcomes.

The 11 October attention/GRU risk head was a measured complement to old hybrid
particle risk, with an inconclusive choice improvement. It has not been shown
to complement the stronger mist-c belief. I recovered its exact graphs from
the migrated `astra-legacy` directory. Hashes match the original receipt.
Current feature-v2 CPU compatibility passed for both colours on two TRAIN
histories, 218 observations and 3,345 candidates. No tactical quality was
evaluated in that preflight and no model weights were fitted.

The scalar calibration family closed on 1 November cannot change a wrong
move-risk ordering. A recurrent, action-dependent signal can. The bounded
question is whether the frozen old signal actually helps that ordering now.

Plan SHA256: `947fdbb906d17ec9f904063b2a93365e82a55f60e3e9b1a280fed4e61d8b0f52`.
Source: `astra-submissions/experiments/recurrent-risk-complement-20261102/`.
Evidence: `astra-submissions/analysis/recurrent-risk-complement-20261102/`.

Use the original calibration dataset's 80 TRAIN games, sorted chronologically:
50 fit the small calibrators, 30 produce a reused-development readout. Neither
the older validation nor test partition is scored. Both network weights and
the v35 risk estimates are fixed. Compare particle-logit calibration with
particle-plus-neural calibration, using the existing tested optimizer, clipping,
ridge and whole-game bootstrap. No parameter sweep. A new sorting-based
within-decision ranking check matches exhaustive pair comparison on 200 cases,
including ties and decisions with no mixed labels.

Before execution, the advancement screen is: a positive neural coefficient,
at least 2% lower development log loss, lower Brier, no worse played-move log
loss and strictly lower opposite-label ranking error. Passing earns only a
fresh v37 confirmation proposal. These old development games cannot establish
generalization, guard quality or playing strength. Failure closes this reuse
path without retuning to a favourable subgroup.

CPUExecutionProvider only, one thread on core 6, 600 seconds total. No GPU or
neural training. No changes to Fable's engine source, beliefs, guards, archive
version or arena activation. The ongoing disk migration remains untouched.
