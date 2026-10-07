# Astra: v12 review and the guide's hidden-bait experiment

October 7, 2026. User has returned the active arena version to **v10**, API
confirmed at 21:15:49 UTC. Arena v11 is our archive labelled v12; arena v12 is
Fable's upload. Keep results attached to played versions, including matches
that finish after an activation switch.

The [frozen latest-ten review](../astra-submissions/analysis/arena-v12-latest10/20261007T210637_952140_0000/README.md)
found 4W–6L. All six losses had hidden final attackers and immediate surviving
alternatives on the true board; three ignored an existing hidden check, while
`xidde3fz` escaped a visible pawn check onto the remembered bishop's diagonal.
Five followed an unchanged observation. Four losses were already materially poor.

Two distinct priorities follow from the evidence:

- `xidde3fz`: Bc3 was visible at ply 52, remained there through ply 86, and killed
  Kg7. Check posterior mass and escape-square choice; geometry alone cannot tell
  us whether the belief, recovery, shortlist, or evaluation caused the error.
- `8zro5fh7`: before ply 43, pawn c3 and queen d2 were both visible. Bxf5 allowed
  c3xd2. Investigate earlier material choices, not only the last king move.

All ten replays reproduce exactly under the referee (2,283 board/observation
checks), with no public protocol failures or warnings. The six losses left
60–130 seconds unused. Four wins also came from hidden attackers; offense exists,
but consistency remains poor. A ten-point Elo fluctuation cannot rank versions.

User explicitly asked to try the YouTube strategies. Fable's raw-vision arm was
reported null and shelved. Astra's [first bait experiment](../astra-submissions/analysis/guide-bait/README.md)
is an isolated, default-off search admission, not a payoff constant: admit one
otherwise omitted move offering a profitable hidden recapture or concealed king
bait, only if its full-population king risk is no worse than the safest retained
row. Keep all existing rows and the same node budget. Do not assume the opponent
will take bait or that a hidden defender is forgotten.

Native fixtures cover both colors, visibility before commitment, own-king-unsafe
recaptures, EP, and promotion accounting. Staged code is not a passed test: follow
`analysis/guide-bait/run-v1/state.json` for actual phase/results. The queued build
waits for Fable's real-clock lane on 2–3, then runs default-off parity and paired
gates. Shared node-limited runs cannot provide throughput or time-budget evidence.

If the arm produces a newly fatal move on the first fixture, withhold it and
record the negative result. If it only raises the feature's own count without
better decisions or play, that does not earn an arena upload.
