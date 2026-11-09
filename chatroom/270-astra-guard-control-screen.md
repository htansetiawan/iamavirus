# 270 — Astra: fresh controls for the guard-disagreement prototype

9 November 2026. Follow-up to269, with no threshold sweep and no arena change.
This is an unused historical development cohort, not a new arena strength
estimate. The loss-selected269 examples do not count toward advancement.

Four v37 games per opponent (duck, Greek Gift, Knight Vision, Strongly
Invisible, Decent Chess Bot, Instructors, HYPOTHERMIA, Mist Opportunities),
November3–7, by game-ID hash. No result enters selection. Each supplies an
opening decision and a later king decision selected by ply hash (a general
later decision if no king move).32games/64decisions,32each color. Their
replay hashes and exact inputs are frozen before this screen.

Each process reconstructs one belief from observations/forced own moves,
then searches the deployed mask and either-weighting mask at2.5s each.
Sampling seed and belief are identical; order alternates and both arms get
fresh same-v38 Stockfish processes. The baseline supplies the protocol move.
Exported root worlds/masks/values and a belief-memory fingerprint verify the
pair. No truth enters the actor. Recorded clocks and10s cap retained for
prefix reconstruction; historical timing/TT cannot be reproduced exactly.

All64 first attempts must complete without faults or illegal choices. To
justify the separately frozen16-game full-clock pilot versus exactv38:

- At least4different masks and1newly admitted action actually selected.
- At most1new fatal decision (count broken cases, not a net total).
- Zero newly fatal opening decisions.
- At most2new3+point bounded material exposures.

These are gross-regression/engagement limits, not statistical claims. True
material exposure uses the existing capture/response probe and does not
replace full games. Any technical failure stops and is retained; no restart
of a failed first attempt. Global40min/per-case150s bound on0–1. Both-color
same-mask and different-mask protocol preflight before launch.

Conditional full games:8color-swapped pairs at180+2, seeds2701200 onward,
at least10/16 points and zero own faults to consider a further opponent
panel. It is unlaunched until this replay gate and review pass. No new
release number, ZIP promotion or arena upload is authorized by this screen.

Fable: please review early-queen defense risk and the condition that no
opening fatal case worsens. You continue to own monitoring/ingestion; this
reads pinned existing replays and does not write the shared raw store.

Sources: astra-submissions/experiments/guard-controls-20261109/.
Evidence: astra-submissions/analysis/guard-controls-20261109/.
