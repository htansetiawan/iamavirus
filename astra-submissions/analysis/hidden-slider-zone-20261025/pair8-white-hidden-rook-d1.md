# Guard screen pair 8, candidate White: concealed rook on d1

Source replay: `v35-guard0001-fullclock-extra-20pairs-seed20261042-pair8-candidate-white.json`.

The candidate (`v36-guard0001`) lost 0–1 by king capture after 55 plies. The
White king was on f1. Black moved its rook from d8 to d1 at ply 54, after which
the true board had a clear d1–e1–f1 rook attack. White's frame-54 observation
reported d1 as `?`, e1 as `-`, and f1 as `K`; in frame 53, d8 was also `?`.
White then played Nc7–a8 at ply 55 and lost.

This is a clean example of a slider arriving from a fully hidden origin to a
fully hidden destination, creating a line to a king whose own square and the
intervening empty square are visible. On the exact recorded history, both v35
and v36 chose `c7a8`; v35 excluded 2 of 19 moves with the king guard, while
v36 excluded 4 of 19. Both assigned the true board only `0.00001` posterior
mass, rank 158 of 392, and logged zero king risk for the chosen move. The true
board has exactly two moves that evade the attack, `f1e2` and `f1g2`; the
candidate chose neither. Exact diagnostics are in
`pair8-white-risk-replay.json`, reproducible with `replay_guard_case.py`.

This is one observed loss, not an aggregate assessment of the guard change.
It localizes this failure to belief weighting/support and its propagation into
the guard: tightening the veto did nothing when the true board's weight had
already collapsed. The held-out hidden-slider prior candidate
(`43125879…edd7f9`) also replayed `c7a8`; truth rank moved only from 158 to
154, its logged share remained `0.00001`, and the guard vetoed only 2 of 19
moves. This selected counterexample shows the fitted feature did not materially
repair this posterior either. Retain it as a regression case before changing
thresholds.

A one-position coefficient sensitivity probe increased the full-prior hidden
slider-zone weight 10× and 100×. The 10× version increased true-board mass to
`0.00014` (rank 14/392) but still chose `c7a8`; at 100× it chose `f1e1`, still
on the rook's attack line. The stronger weight inflated risk on the two truly
safe king moves instead. This rejects global feature scaling as the fix. See
[`pair8-hidden-slider-prior-sensitivity.md`](pair8-hidden-slider-prior-sensitivity.md).

Reproduce the guard comparison (and substitute the hidden-slider-prior binary
for the candidate to reproduce that check) with:

```sh
taskset -c 0,1 .venv/bin/python \
  astra-submissions/analysis/hidden-slider-zone-20261025/replay_guard_case.py \
  --replay astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-fullclock-extra-20pairs-seed20261042-pair8-candidate-white.json \
  --baseline data/arena_local/builds/iamavirus-v35-mist-c-v14 \
  --candidate /tmp/iamavirus-v36-kingguard0001 \
  --target-frame 54 --side white --seed 20261058 \
  --out astra-submissions/analysis/hidden-slider-zone-20261025/pair8-white-risk-replay.json
```
