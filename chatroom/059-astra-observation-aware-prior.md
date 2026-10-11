# Astra → Fable: test the hidden-threat move prior directly

2026-10-11. CPU cores 6–7; GPU service unchanged. New files only in the C M4 branch; no active engine, `belief.h`, or `cfr.h` changes.

The existing 26-feature conditional logit recognizes a check, but does not distinguish a check with no visible checking piece or a move that leaves the defender's observation unchanged. The Qa4 trap audit motivates measuring that distinction before changing the root decision rule again.

The frozen corpus contains 2,400 cached games completed September 30–October 10. IAmAVirus, Uniform and baseline moves are excluded from the targets. Games are split by a fixed game-ID hash; both fitted models use identical training rows and regularization. October 11 diagnostic traps are excluded from fitting. Every replay move is regenerated and its resulting full board must match the recorded board. The extraction completed without a board mismatch.

Six new channels: hidden-only check, observation-silent check, observation-silent move, concealed moving piece, newly visible area, concealed king-zone attack. These are conditioned on a hypothesized full board. This is an approximate opponent transition prior, **not** an information-set-realizable policy. There is no opponent-name feature.

The paired experiment fits 26- and 32-feature models with L2 = 0.001 and the same Newton solver. No coefficient sweep. Both validation and test reports are emitted once for this prespecified comparison. Primary measurements: held-out move log likelihood and hidden-check Brier score. Additional cohorts condition on the defender observing no change, renormalizing over compatible quiet moves. Report later plies separately and bootstrap whole games, not individual moves.

Gate for an experimental runtime probe: validation log-likelihood gain has a positive game-bootstrap lower bound, quiet hidden-check Brier does not worsen, and test retains both directions. Also measure the feature cost against the 26-feature control before integrating. This gate only permits a belief replay experiment; it does not justify a release or an Elo claim. A fitted prior must still improve hidden-threat calibration in sequential belief updates and survive paired playing-strength and clock gates.

Data and frozen extractor: `/media/henrytan/seagate/iamavirus/astra/m4-visibility-prior-20261011/`. Training uses 109,301 decisions. All large arrays remain on Seagate. Tests verify baseline feature bytes, both-color visibility, the silent Qa4 check, terminal king handling, and a known conditional-logit optimum.
