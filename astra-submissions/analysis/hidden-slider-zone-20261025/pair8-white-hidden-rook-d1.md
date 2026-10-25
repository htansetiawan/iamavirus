# Guard screen pair 8, candidate White: concealed rook on d1

Source replay: `v35-guard0001-fullclock-extra-20pairs-seed20261042-pair8-candidate-white.json`.

The candidate (`v36-guard0001`) lost 0–1 by king capture after 55 plies. The
White king was on f1. Black moved its rook from d8 to d1 at ply 54, after which
the true board had a clear d1–e1–f1 rook attack. White's frame-54 observation
reported d1 as `?`, e1 as `-`, and f1 as `K`; in frame 53, d8 was also `?`.
White then played Nc7–a8 at ply 55 and lost.

This is a clean example of a slider arriving from a fully hidden origin to a
fully hidden destination, creating a line to a king whose own square and the
intervening empty square are visible. It is one observed loss, not a causal
assessment of the guard change. Add it to the regression suite as a hidden
arrival / already-exposed-king case, and inspect whether the guard assigned
meaningful mass to a rook on d1 before changing its threshold.
