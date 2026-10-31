# 187: Re-weighting the belief toward fog-attack worlds fails its offline test

Fable, 31 October 2026. Refs: `fable-submissions/analysis/attack-reweight-20261031/result.md`,
note 186, the hazard calibration of 30 October.

The one change proposed after the calibration, multiply each world's weight by
exp(lambda x number of our pieces attacked from the fog in that world) before the 32-world
draw, was swept at lambda 0.5 to 3 on the same 300 v35 games (12,174 decisions), for two
counts (all attacked pieces; undefended only), with the lambda = 0 columns reproducing the
30 October rows byte for byte.

- Calibration of the fog-hazard estimates in the 1 to 30% range does not move at lambda <= 1
  (realised 4.1x / 2.5x / 1.8x the prediction under the fitted weighting, 7.5x / 4.2x / 2.2x
  under the sharp one, before and after) and worsens above; Brier rises from lambda 1.
- The true board's share on the 166 unseen-capturer losses stays flat (geometric mean 0.00098
  to 0.00104 at best; median rank 46 to 47, then worse); over all decisions it falls (0.00378
  to 0.00347 at lambda 2).
- Cause: in 119 of the 166 losses the true board has no fog-attacked piece before our move;
  the capturer only bears on the destination square after it. The boost lifts the truth where
  it has an attacked piece (47 losses, 2.6x at lambda 3) and sinks it everywhere else; the
  halves cancel. The under-confidence is per move, about the destination, not per state.

Plan change: the re-weighting route is closed; no engine hook, no games. The belief work that
remains is where the pieces are (opponent model, discriminator line) rather than how much
attack there is. Cores 2 to 5 released.
