# 373 — Earlier loss patterns, with winning and drawing controls

Astra, November 11 UTC. Extends the existing 337 diagnostic across all
345 v38 games in 369's reviewed window. No bot run, new model or deployment.

Definition stays fixed: first at-least-three-point deficit lasting five
recorded frames, P/N/B/R/Q/K = 1/3/3/5/9/0. The frozen plan is
`116a7197e6f16aeab5fea7ab800b3d2f14544088c961b74092b035a93f2faed8`.
Original 18163 exits 0 in 1.26 seconds; 30,945 frames / 343 unique trajectories.
Independent raw-frame/sequence/reduction review passes. Twelve old 337 IDs
overlap and their onset/material/visibility fields match exactly.

| Outcome | Games | Ever three points down | Five-frame deficit | Later even or better | Five-frame recovery above −3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Win | 184 | 134 | 18 | 15 | 12 |
| Draw | 17 | 16 | 3 | 0 | 0 |
| Loss | 144 | 137 | 121 | 26 | 10 |

Loss onset median is ply 51, a median 29 plies before the end. Of 121 loss
onsets, 116 are captures and five quiet promotions. Hidden capture sources
account for 111: rooks 50, knights 15, bishops 14, queens 13, pawns 13, kings 6.
Victims are rooks 39, knights 29, queens 20, bishops 12, pawns 11. In 83/111,
the victim is at our previous UCI destination. These are role-defined
descriptions, not proof of deliberate traps, posterior failure or bad moves.

Controls change the interpretation: many wins have a temporary threshold
crossing, 18 wins have five-frame deficits, and three of those never return
to nonnegative material. Seven losses end with a short deficit tail that
cannot meet the five-frame horizon. Do not turn these labels into an
automatic material veto or call them causal/counterfactual safety labels.

The private normalized event view has 142 onset events and 203 game-level
controls. Recorded observation, candidate action and hindsight are separated;
the candidate is not known pre-choice policy state. The original scan's
capturer-specific hidden facet also described three quiet promoters; v2 uses
a generic hidden-source name without changing the scan/metrics. Game-level
controls are not matched negative decisions or a ready training dataset.
No actor-only retriever, training loader, model, history table or guard changes.

The human brief includes a standalone vector/PNG figure: an actual rook-loss
onset vs HYPOTHERMIA and a recovered win vs Lost Signal. Selection is explicit
and illustrative, not experimental. Please review the interpretation. This
does not reopen failed material/king-penalty candidates or qualify a release.

[Human findings and figure](../astra-submissions/analysis/field-material-onsets-20261111/README.md)
· [Aggregate result](../astra-submissions/analysis/field-material-onsets-20261111/result.json)
· [Independent review](../astra-submissions/analysis/field-material-onsets-20261111/review.json).
