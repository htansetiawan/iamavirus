# Grouped opponent prediction — experimental, not in Astra v12

The experimental `implementation/` tree can aggregate identical predecessor
particles before enumerating opponent moves. This avoids repeating the same
expansion and replaces the old first-20,000-successors cutoff with weighted
groups of compact transitions. Complete state equality resolves hash
collisions; it includes piece boards, colour occupancy, side, castling rights,
en-passant square, and halfmove clock.

Each group's mass includes predecessor multiplicity and the likelihood of the
new observation. Opponent-action priors are normalized over **all** legal
actions before inconsistent transitions are excluded. Two-stage systematic
resampling first chooses predecessor groups and then their consistent
successors. Only selected full boards are constructed. The population remains
resampled: this is not exhaustive history retention or a cure for strategy
fusion. A future move-memory prior must include that memory in the group key.

Enable with `FOW_GROUPED_PREDICTION=1`; it is off by default. Capture evidence
and visibility deductions retain separate switches.

The focused belief suite passed **850 checks**. Over the existing 1,444-ply
random audit, combined capture+deduction truth-in-population rose from
805 to 835 with grouped prediction; collapses remained 13. A 2,048-duplicate
opening population expands one predecessor, enumerates all twenty legal
moves, and preserves systematic-resampling count bounds. See
[belief-tests.log](belief-tests.log).

No paired action benchmark or playing-strength gate has been run for this
variant. It is checkpointed as research and excluded from the urgent release.
