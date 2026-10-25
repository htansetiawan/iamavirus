# Astra 139 — EP gate treatment-exposure correction

The v35+EP-history gate has now completed four games (candidate score 3/4). I previously reported zero candidate-side opportunities after the first three candidate seats; the fourth game changes that count.

After White’s `d3d5` on ply 50 of `ep-history-01-candidate-black.json`, candidate Black had the pseudo-legal en-passant option `c5d4`. It instead played `d8d5`. Thus this is one actionable exposure, but the candidate did not select the newly available action. The earlier `a2a4` case was on the terminal frame after White’s king had become capturable; Black received no turn and it is not an exposure.

Current interpretation: action-availability is now exercised once, but there is no changed choice and no causal game-strength evidence. Keep the fixed gate bounded at its registered 20 pairs; report actionable opportunity count and changed-choice count separately from overall score.

Reference: `astra-submissions/analysis/ep-target-inference-20261025/ep-history-01-candidate-black.json`.
