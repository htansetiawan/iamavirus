# Fog-feature value feasibility: negative screen

Three small logistic models were trained on cached replay positions: a
piecewise Stockfish-score calibration; that baseline plus material, mobility,
king attacks and undefended material; and the latter plus six fog features.
The fog features measure visible squares, concealed king attackers, concealed
attacks around the king, hidden queen attacks, hidden attacks on undefended
material and concealed own material. Inputs are differences between colors.
No team names, outcome labels or future moves enter the feature extractor.

The first 1,000 previously inspected games were excluded entirely. The remaining
9,000 games split into 5,367 training, 1,846 validation and 1,787 test positions.
All rows with equal first-five-field FEN keys share a fold; 8,750 distinct state
groups remain. Training-only standardization and validation-selected ridge
penalties precede test evaluation. Related games and versions can still be
correlated. A time/opponent holdout is not claimed.

| Model | Test Brier | Test log loss |
|---|---:|---:|
| Stockfish score + side to move | 0.13403 | 0.42920 |
| Plus ordinary board features | **0.13244** | **0.42356** |
| Plus fog features | 0.13265 | 0.42435 |

Fog minus ordinary Brier difference: **+0.000212** (worse); paired state-group
bootstrap 95% interval **[-0.000606, +0.001016]**. Fog minus score-only:
-0.001379, interval [-0.004458, +0.001506]. Neither interval excludes zero.
The fog model also loses to the ordinary model on validation log loss.

**Reject this feature model as a deployment candidate.** This tests these
linear combinations against recorded outcomes, not every possible fog-aware
evaluator or a learned temporal representation. The frozen reports and
predictions remain available for inspection. There is no strength claim and
no C runtime integration.

Feature extraction took 4.38 seconds for 9,000 positions on the CPU. This is
an offline batch timing, not a per-node runtime benchmark. Tests verify a
concealed queen check, color-swap symmetry, independence from labels/team names,
and recovery of known logistic probabilities. All three model fits converged.

Limitations: complete sampled-world features assume a correct belief world;
they do not fix missing truth or model an opponent's observation history.
Recorded winners confound policy skill and position value. Source FENs use
orthodox EP canonicalization; future exact fog features should preserve raw
FOW EP state as well. Raw data are on Seagate, with hashes in the manifest.
