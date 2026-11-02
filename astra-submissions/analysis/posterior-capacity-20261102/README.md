# 232: nonlinear posterior capacity screen — closed

**The tested interactions do not provide a large enough development gain.** All three minimum-effect requirements fail. No fresh test, filter integration, match or ZIP follows this configuration. These are reused validation games, not an independent strength result.

| Model and objective | Primary validation board NLL | Gain versus baseline |
|---|---:|---:|
| Unchanged v37 prior | 2.65930 | — |
| Linear, move likelihood | 2.66271 | -0.00341 |
| Linear, posterior likelihood | 2.64952 | +0.00978 |
| Quadratic, move likelihood | 2.66266 | -0.00337 |
| Quadratic, posterior likelihood | 2.64234 | **+0.01696** |

Primary: 536 nontrivial decisions across 80 validation games, with equal game weight. The nonlinear posterior model gains only **0.00718** over the linear posterior control and **0.02033** over the nonlinear move-trained control. Required gains were 0.10 over the baseline and 0.05 over each control.

Later-update gain is 0.08686 (266 cases / 36 games); surprise-capture gain is 0.03194 (44 / 26); all-update gain is 0.01324 (810 / 80). All these safeguards pass, and every case has natural truth support. Those subgroups do not override the failed aggregate requirements.

## What was actually compared

Exactly 231's 400 training and 80 validation games, producing the same 3,058 training and 810 validation cases byte for byte. Its 80 test games were not exported or scored. Four forms/objectives crossed with two fixed ridge values produce eight fits. Same data, game weighting, optimizer, incoming beliefs, history blend, temperature and exact-prefix restrictions. Every model starts at zero; no 228 or 231 fitted interaction weights initialize it.

The quadratic formula allows 357 coefficients: 26 linear, 325 pair interactions and six continuous squares. Some real feature combinations are necessarily absent; this is not a claim of 357 independently identifiable parameters. The fused formula avoids allocating 331 extra columns for every transition. CPU only on two reserved cores; no GPU usage.

Selected models: linear-move ridge 0.01 / step 30; linear-posterior 0.001 / step 40; quadratic-move 0.01 / step 30; quadratic-posterior 0.001 / step 20. All curves and parameters are retained. Selection and metrics use development validation; no confidence interval is offered as if this were a fresh test.

## Verification and execution

The four CPU linear curves reproduce the earlier GPU controls: maximum coefficient difference 7.31e-14, NLL difference 8.89e-16. This rules out a backend discrepancy as the explanation for the capacity comparison.

Independent review reconstructs all 810 validation cases, confirms exact feature hashes and selection, and checks every model probability in separate NumPy calculations. Maximum log-probability error is 1.27e-14; the sparse C float scorer differs in logits by at most 6.54e-7. Source and replay hashes verify. The engine rules and belief updater are unchanged dependencies.

Plan published on both remotes at `9d10430fe9f4605247cda7977a58d35a9c302318`; plan SHA `1a9bb9cf405d2dc8013a1a3acf9985e25aeb4c7ab46c131a6f1b2c7b8d7cfbaf`. The single run (original handle **85980**, exit 0) completed in 586.74 seconds; wrapper 588.43 seconds. Independent reviewer **58697** exited 0. PIDs 2/3 in the launcher receipt are sandbox-namespace PIDs, not host identities. Original handles and terminal receipts identify completion.

One preparation import failed before main or any fit (31966, exit 1). Its receipt remains in the source folder; using an explicit module path fixed the ambiguous import. Successful preparation was 61683. No training restart, test-selected rescue, or changed gate.

## What to investigate next

This screen does not show that all nonlinear models are ineffective. It does show that this fixed quadratic expansion of the same 26 inputs is insufficient on these development data. Before another larger fit, measure whether different consistent hidden transitions have identical scoring inputs and therefore fixed relative probabilities under every scorer on those inputs. That would identify information the representation cannot express. The proposed audit must distinguish a proven feature-equivalence bound from ordinary prediction error; it must not claim such a bottleneck before measuring it.

The retained C scorer and verified posterior-loss pipeline can support a genuinely different representation later. Neither is a deployed upgrade.
