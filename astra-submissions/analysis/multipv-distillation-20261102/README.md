# Compact MultiPV distillation: learned, but not accurate enough

2 November 2026. **The fixed architecture fails all three development gates.**
No native integration, follow-up match, model sweep or arena ZIP follows.
This is teacher approximation, not a Fog of War strength measurement.

The hypothesis was to replace many expensive leaf scores with one shared
parent encoding and a cheap query per move. Unlike experiments 237–240,
targets here are saved Stockfish MultiPV values, not recorded game outcomes.
No new Stockfish search, arena request or game rollout was required.

The contract/data were published before fitting in `f5e85eb3fef00ce2c47fc5ddffad89daafcc8e40`,
verified on both mirrors. The architecture has 137,786 parameters (551,144
FP32 bytes). One 32-epoch run completes in **13.92 seconds** on the free
RTX PRO 5000, with peak framework allocation about 129 MiB. No existing GPU
service was stopped. The GPU is subsequently verified idle again.

| Equal-game validation measure | Untrained | Selected epoch 17 | Required |
|---|---:|---:|---:|
| Mean squared value error | 0.58319 | 0.17469 | Epoch selection criterion |
| Mean absolute value error | 0.69818 | **0.28148** | <=0.08 |
| Teacher regret of student's chosen scored move | 0.43470 | **0.21463** | <=0.05 |
| Frequency of teacher regret >0.5 | 32.04% | **14.56%** | <=1% |

Teacher regret means the best saved teacher value minus the teacher value of
the student's selected action, among Stockfish-scored moves. Values lie in
[-1,1]; they are not calibrated win probabilities. None of these numbers is
an arena win rate or Elo estimate.

The model clearly learns relative to its random initialization, but its
remaining errors are much too large for this replacement interface. A
post-hoc squared-error decomposition attributes 0.07245 to parent-wide offsets
and 0.10225 to action-relative errors, summing to 0.17469. Even an oracle
parent-offset correction would leave every action ranking unchanged. This
diagnostic does not propose another calibration sweep or change the gate.

## Data and validation

- 3,000 training games: 23,044 distinct parents and 710,576 scored actions.
- 500 reused development-validation games: 3,786 parents and 116,174 actions.
- Complete-game separation; 34 duplicate canonical parents removed.
- 166 parents with fewer than two scored moves excluded; 38,261 unscored
  actions excluded before fitting. Their native terminal/fallback handling
  is outside this approximation experiment.
- 341,294 source frames validate with the existing referee-compatible rules
  library. The old collector's independently reviewed provenance is retained.
- A separate 128-parent audit checks 4,404 move-coordinate and cp/value pairs
  against the original native maps. Final metric/selection audit recomputes
  equal-game scores, the selected epoch and the failed gate independently.
- Selected checkpoint CPU/CUDA outputs agree within 2.69e-7 on 128 parents;
  candidate-order permutation changes no scores.

Old TEST examples are excluded. The validation games were used in earlier
outcome-model research, so this is development evidence. Inputs describe a
hypothesized parent board and rule state; outcomes, player IDs and future
moves are not inputs. Warm Stockfish has mutable state, and played parents
differ from the search frontier; those limits remain even with accurate
teacher approximation.

## Receipts and reproducibility

Data preparation handle 19881 exits 0; training handle 85016 exits 0; final
audit handle 98640 exits 0. The initial CPU model-name collision was repaired
before extraction/fitting. The first result audit failed only while serializing
a NumPy boolean after its numerical checks; its partial output and source are
preserved, and the serialization-only repair does not repeat training.

`model-evidence.tar.gz` preserves exact `data.npz`, `selected.pt`, and
`validation.npz` bytes, with hashes checked on archive read-back. It is research
evidence, not an arena submission. `plan.json`, `training-contract.json`,
`curve.json`, `result.json`, `audit.json` and the receipts pin the full run.
Source: `../../experiments/multipv-distillation-20261102/`.

No runtime speedup is claimed: the prediction-quality gate failed before
native export and full-parent timing. This closes this compact architecture
on the stated target; it does not rule out learned evaluation generally.
