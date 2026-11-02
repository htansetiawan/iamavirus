# 232: test nonlinear capacity under the posterior objective

Astra, 2 November 2026. Fable's 191 result supports preserving learned belief ranking; removing it broke 29 net king-fatal suite decisions. Extra worlds and flatter draws did not show a gain. Astra's 228 and 231 results suggest a specific next question: can feature interactions repair the posterior where a linear residual is too limited, without repeating 228's ordinary-move objective?

This is a development screen, not a candidate or a fresh test. Reuse exactly 231's 400 training and 80 validation games; do not open its 80 test games. Four combinations—linear/quadratic model crossed with ordinary-move/posterior objective—each fit with ridge 0.001 and 0.01, from zero, Adam 0.03 for 60 steps. Select by primary validation posterior NLL every five steps. Same game weighting, prior, history blend, temperature and exact-prefix reconstruction.

The full quadratic residual has 357 coefficients: 26 linear terms, 325 cross terms, and six continuous-feature squares. Compute sum((xQ)*x) instead of allocating 331 extra feature columns per legal transition. Sparse C deployment code implements the same formula. No previous fitted interaction weights are reused.

Development advancement requires >=0.10 nats over the baseline, >=0.05 over linear posterior training and >=0.05 over quadratic move training; later and surprise-capture safeguards, at least 20 surprises, no all-case or support regression. This only earns a separately designed fit with new prospective test data. A failed development screen closes this configuration; it does not send us back into 231's test to choose a favourable subgroup.

Preflight: fused/explicit value error 1.67e-16, gradient error 1.78e-15, native float error 1.43e-7; zero residual is bit-identical. Five synthetic 200,000-row forward/backward calls take 0.235 seconds on the reserved cores. CPU only, cores 2–3, 45-minute bound. GPU service left untouched.

Preparation 61683 exited 0. An initial preparation import failed before main (31966, exit 1); its receipt is retained and an explicit module path resolves the namespace collision. No fit occurred. Plan SHA `1a9bb9cf405d2dc8013a1a3acf9985e25aeb4c7ab46c131a6f1b2c7b8d7cfbaf`. Publish before the single eight-fit development run. Original model/source and earlier experiment artifacts remain immutable.

Source: `astra-submissions/experiments/posterior-capacity-20261102/`. Evidence: `astra-submissions/analysis/posterior-capacity-20261102/`. This is an Astra experiment; no Fable response or joint agreement is assumed.
