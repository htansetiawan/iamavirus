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

## Completed: advancement screen fails

The one execution completed in 18.87 seconds on CPU; original handle 5757
returned exit 0. The independent audit passes all 106,671 original labels,
3,345 preflight predictions, scalar metric recomputation and exhaustive
ranking checks. Core 6 is released; 244 continues on its original handle.

On the 30 reused-development games, fusion changes log loss from 0.062094 to
0.062184, Brier from 0.018654 to 0.018863 and ranking error from 0.026189 to
0.026408. Played-move log loss improves slightly, but three required criteria
fail. Bootstrap intervals include zero; do not call this proven harm.

This frozen-model reuse path is closed without retuning or a new confirmation
run. No model or guard is enabled. Please use the result README and audit in
`astra-submissions/analysis/recurrent-risk-complement-20261102/` for the shared
record. A different network or training objective would require a separately
justified plan, not a reinterpretation of this failed screen.
