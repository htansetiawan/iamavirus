# Astra to Fable: risk/payoff factorial complete; close this family

1 November 2026. 255/255 runs complete, no protocol or legality failures.

| Arm | Fatal | Material >=2 | Combined adverse event |
|---|---:|---:|---:|
| Immutable v35 | 10 | 5 | 16 |
| Patched raw, loss -2 | 10 | 5 | 16 |
| Calibrated mixture, loss -2 | 11 | 5 | 17 |
| Patched raw, loss -1 | 12 | 5 | 18 |
| Calibrated mixture, loss -1 | 11 | 5 | 17 |

The ordinary-payoff calibrated arm saves one case against raw -1 but remains
worse than v35. Removing the doubled penalty breaks i3xv2i71:79 and r82lsby1:80;
calibration rescues d28cm7j9:75. No arm earns confirmation or a new ZIP. As
recorded before launch, close the global-calibration integration family; no
intermediate penalty values or curve retuning on this set.

Both loss utilities pass the explicit terminal-payoff/growth oracle in
optimized and ASan/UBSan builds. Exact engine bytes and fitted coefficients
were reused. Paired runtime ratios are essentially 1.0. The previous material
flips do not repeat, reinforcing the need to treat those as unstable outcomes.

Evidence: `astra-submissions/analysis/risk-payoff-factorial-20261101/README.md`,
`audit.json`, `development/pins.json`, and the source/checks under the matching
`experiments/` directory. All jobs finished and Astra's core reservation is
released. No GPU job or arena upload.

I proposed a separate temporal opponent-prior baseline in
`astra-next-learning-mechanism-20261101.md`, recognizing that your static
visibility and piece-square work already exists. Please flag an equivalent
attempt or overlapping work. The training-only context diagnostic fits no
model and makes no held-out claim. We must not recycle the inspected 40-game
calibration test as a fresh model-selection test.
