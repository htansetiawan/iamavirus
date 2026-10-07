# Astra v12 — population-wide material exposure

This is a conservative collaborative arena-trial candidate. It adds Fable's
population-wide one-ply material-exposure evaluation to the engine currently
mapped to arena v10. A move is charged for the opponent's best immediate net
capture anywhere on the resulting board, including a piece the move leaves
behind or a slider line it opens. The earlier destination-only term could miss
those losses. King-loss probabilities and their fatal-cell charges remain
separate.

The runtime and model files are byte-identical to Fable's earlier, unsubmitted
`iamavirus-v11-hybrid.zip`, SHA-256
`d549f8b5379ddfe70be01f973e6c4228d05079771bffed4e7767e75e8b3b489e`,
recoverable from Git revision `9614f6f`. Fable authored the exposure feature;
Astra froze, independently built, validated, and packaged this release.
The source is not the separate experimental `astra-submissions/implementation/`
tree. No PPO weights or new trained model are included.

Defaults: hybrid mode, Stage A v1 ONNX model, 2,048 particles, hand opponent
prior, exposure stride 4, real-time search with the existing 4-second cap.
The arena-v10 safety-row, fatal-cell-payoff, and deadline fixes are retained.
Newer deduction, capture-recovery, grouped-prediction, adaptive-clock,
promotion-pruning, and two-ply-threat experiments are excluded.

Before packaging, a clean ONNX-enabled build passed all nine C++ unit suites
and 18,625 differential checks against the course referee. These establish
correctness, not higher Elo. The source/model/configuration freeze precedes
opening the prospective replay gate. Completed gate reports, paired match
results, and their limitations are published separately in
`astra-submissions/analysis/release-v12/` so this ZIP stays immutable.

The archive label is 12 because the highest Fable archive major version at
packaging is 11, including candidate filenames. It is not an arena version.
The public API assigns the actual version only after the human uploads it.
Repository publication does not upload or activate a bot in the arena.

Build with `bash build.sh`; run with `bash run.sh`. The course runtime supplies
ONNX Runtime; local builds may set `ORT_HOME`. Missing ONNX support falls back
to the C++ engine, so the gate also checks that the intended hybrid model loads.
