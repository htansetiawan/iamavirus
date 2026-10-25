# Astra 136 — hidden-slider sensitivity and live gate checkpoint

## Posterior sensitivity probe

On the exact pair-8 hidden-rook loss, the held-out hidden-slider prior candidate
barely moved the true board (rank 158 to 154 of 392; printed mass remained
0.00001) and repeated the fatal move. A temporary 10× coefficient intervention
raised true-board mass to 0.00014 / rank 14, but still chose the fatal move.
At 100× it switched to Ke1, which remains on the rook's attack line; it also
rated the two genuinely safe king moves as about 0.999 risk. Reject global
weight scaling. This one-position probe points to a missing calibrated signal
for newly hidden direct king attacks, not a release-ready coefficient change.

Details and hashes:
`astra-submissions/analysis/hidden-slider-zone-20261025/pair8-hidden-slider-prior-sensitivity.md`.

## Gate status at 16:57 UTC

- v35 vs EP-history: 2/40 games, candidate 1/2. Neither game exercised an EP
  action. In game 2, Black had a pseudo-legal `b4a3` after White's `a2a4`, but
  White had already lost by king capture on that move, so Black never got a
  turn. Do not treat this as a candidate EP opportunity or a feature test.
- v35 vs v36 king guard: 18/40 games, candidate 9/18. Pair 8 split 0–2 for the
  candidate. Its White loss to hidden `Rd8-d1` is analyzed in the linked
  regression note; this is still a small self-play sample, not an Elo result.

Both processes remain live on their recorded core pairs. No ZIP is ready for
submission.
