# Astra v11 hybrid

Historical experimental candidate authored in the isolated Astra workspace. At packaging, label 11 was one greater than Fable's then-latest package, v10. The code was validated under the provisional v10 name before Fable published its own v10; the evidence paths retain that provisional name. Repository publication is separate from an arena upload; this candidate has no confirmed arena upload. See the workspace README for the newer campaign. The immutable ZIP retains its original embedded release note.

## Change

Starting from the exact arena-v5 hybrid archive, enforce a safety invariant on the **final** hybrid candidate union: it contains at least one move with the minimum particle-estimated king-loss probability among eligible moves.

Search and policy candidates retain their original ordering when a minimum-risk move is already present. Otherwise, replace one highest-risk row with the best omitted minimum-risk candidate. Ties among removable rows prefer the last row. The existing risk ordering chooses among minimum-risk candidates. Matrix size remains capped at 12 by default; no new weights or thresholds are introduced.

This differs from appending multiple safety rows before constructing the hybrid union: the invariant is checked after all capacity limits have been applied. Diagnostics add `safety_replace` and `shortlist_risk` to the decision trace.

The pretrained Stage A v1 ONNX graphs are unchanged. This release contains no PPO checkpoint. Existing v5 particle propagation, evaluation, fatal-cell scoring, and deadline behavior remain the baseline; this is one isolated candidate-selection experiment.

## Validation

- Regression from public game `1sv22xki`, tested with neural advice favoring non-king moves, four particle seeds, and row caps 6 and 12. Before the fix, two cases kept only 100%-risk rows while a 29.1%-risk move was available. After the fix, all eight cases preserve a minimum-risk candidate and stay within the cap.
- Nine C++ suites: 169,474 checks, zero failures.
- Differential rules test against the course referee: 30,100/30,100 checks agree.
- The repository's `astra-submissions/analysis/` contains the matched offline hybrid-corpus comparison and complete referee smoke games. The release record outside the ZIP records their final results and the archive checksum.

## Limits

Minimum estimated risk is not guaranteed true-board safety. This does not repair a particle population that entirely misses an attacker, and including a candidate does not force the matrix solver to choose it. Offline forced-history diagnostics and a small smoke match do not establish an Elo improvement. Treat this as a trial candidate, not a demonstrated promotion over v5 or Fable v9.

## Run

`bash build.sh` compiles the submission. `bash run.sh` starts hybrid mode. The arena provides ONNX Runtime at `/opt/onnxruntime`; `ORT_HOME` overrides the SDK path for local builds. The package contains source and pretrained graphs, and excludes a host-compiled executable.
