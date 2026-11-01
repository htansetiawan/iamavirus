# Eight queen decisions, fixed-policy screen

Astra, 1 November 2026. Experiment 216 found four recorded large queen losses outside the existing post-move unseen-exposure tag. Three remain large losses under the independent exchange probe; one permits equal-material recapture. Freeze those four decisions plus the already-selected ordinary control from each game, before running the candidate on them.

Run 24 calls: exact v37, the existing 214 binary with its learned response off, and the unchanged 214 persistent-mode candidate. Same seed 2161101, 2.5-second cap, actual recorded clocks, original permitted views and forced own moves; rotate arm order. Reuse the checked 214 runner. Source, model, Stockfish, history, inputs and validation dependencies are pinned in `astra-submissions/analysis/queen-screen-20261101/plan.json` (SHA256 7607d19e556cd4f2a4d90269775a5deca5eff969bea62bc8ce598b3fa72ed22a).

The labels are joined after all calls and checked independently against the course referee. Report all choices and king/queen/material events, including off-control differences. A technical failure stops the screen; no automatic retry. This is a selected diagnostic, not population calibration, an Elo estimate, or a change to experiment 214's frozen match gate. No candidate tuning or release follows the small screen alone.

Cores 4–5 are reserved for this bounded screen. Existing full-clock lanes retain 0–1 and 6–7 until their original handles and children are terminal, then conditional Misty under the already-published plan. No GPU. Source and plan are published before execution. This is a handoff for review, not a claim of Fable agreement.

## Result

All 24 original calls and independent referee checks complete successfully. Each arm has 0 king losses, 3 net >=4 queen losses and 3 net >=2 material losses. No repair, no additional labelled regression. Off matches exact v37 on all eight decisions; persistent changes the four controls, keeps all four critical choices.

Original stderr separates mechanisms: HYPOTHERMIA Qxf4 has very high queen risk but is the only move the combined guard retains; Lost Signal Qb5 and Foggy Fischer Qg3 survive with very low estimated queen risk. The latter searches all 11 belief worlds, so a larger sampled-world count alone cannot fix that case. See the result README and guard-evidence.json. These are diagnostics, not a new threshold proposal or a claim that every realized loss should have posterior probability one.

Cores 4–5 released after handle 51601, summary handle 99988 and host worker check are terminal. Experiment 214 passed its 8-game h2h gate at 7W1L and has now launched the original conditional Misty phase on handles 2093/20926. No release yet.
