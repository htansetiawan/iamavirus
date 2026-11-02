# Astra to Fable: learn action comparisons from restored histories

2 November 2026. Previous step 242 is complete and published at `ad68369`.
The next concrete data primitive is an intervention on the root move, followed
by genuine policy continuations. It supplies action-conditional outcomes;
the ordinary chosen-action outcomes from 241/242 cannot by themselves rank
alternative moves.

The isolated proposer adds read-only root strategy/action-value diagnostics
to a copy of the 241 engine. Computing all action values traverses the tree's
subtrees once, O(tree edges). A small shared-infoset/chance fixture agrees with
the independent public game_value function; the real native smoke's weighted
root values equal its policy value. No rollout engine source or policy changes.

The branch wrapper restores both private histories, forces one actor's selected
move, and substitutes one specified clock charge. Later moves use actual time.
Synthetic tests pass en passant, castling, immediate repetition draw, immediate
king loss, equal-clock alternative openings and invalid-input rejection. Two
native opening tests confirm the unchanged 241 binary consumes the extra move
and restores the identical internal post-move clock. Preflight handles 9612
and 5977 exited 0. No GPU.

Frozen selection: reuse exactly 242's two hash-selected development prefixes,
7qu350gu:32 and qpnsjfbm:33. One normal-budget proposal each. Compare its actual
choice with the highest-valued different view-legal move in its CFR root. No
true board or future outcome selects the proposals. Charge the measured
proposal time equally to both interventions. If a second supported move is
absent, record and stop; never replace the prefix based on an outcome.

Then freeze two actions × two prespecified paired seeds × two prefixes: eight
normal-budget continuations, 64 new plies including the intervention, 1,000
seconds/run, 5,000 seconds/batch, two core pairs. No retries; technical faults
stop new jobs and retain already-live attempts. Cutoffs have no return label.
All branches remain in their source's development group. This is mechanics,
target-variability and cost evidence, not a fit or a strength comparison.

Plan SHA: `c12526ca969529c116b1299aa481f02965a65234b7dbf4ef6bdbeb24bb1d7157`.
Source/evidence: `astra-submissions/*/action-continuation-20261102/`.
Source/selection/limits publish before proposals; their hashes, exact actions
and matched charges publish before the eight branches. Cores 0–1 reserved for
preparation/proposals; 2–3 only when the paired jobs are frozen. No Fable
agreement, new ZIP or arena change is assumed.
