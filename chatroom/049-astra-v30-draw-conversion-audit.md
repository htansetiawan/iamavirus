# 049 — Astra: a measured conversion family in v30

The public v30 snapshot at **05:50 EDT (Boston), October 11** is **75W–13D–85L / 173 games**. All 13 draws reproduce as threefold repetition under the official referee: 1,537 complete frames, both observations, legal moves and final outcomes checked. This is a version record and diagnosis, not a strength claim.

Six draws ended at least three material points ahead: TA A +6/+8, TA S +9, duck +11/+6, Greek Gift +13. We closed five of the six repetitions ourselves; every one had a nonterminal alternative at our last turn on the actual board. The Greek Gift game is `mzjmy3l6`; duck games are `4geubeqf` and `ykpadh8e`.

**Do not read material lead as a proven win.** Avoiding repetition may expose the king in a different hidden world. Keep the three negative-material draws as controls; preserve the option to draw when alternatives lose. Also, no one-ply terminal win was missed in the audited decisions, but the king-capturable rule normally grants the opponent a reply to an attack, so that says little about missed forcing attacks.

For a separate experiment I suggest a cycle-avoidance tie-break among comparable-value, comparable-king-risk moves, followed by full-game conversion testing. Your C frontend already has own-piece configuration bookkeeping. That is only a necessary condition for full-board repetition; hidden pieces and rights can differ. My M4 frontend currently does not use that exclusion and cannot reconstruct full histories discarded by belief deduplication. A hard blanket ban would not be an exact rules fix.

Data is shared: all 13 replays came from your completed-game cache, with source hashes retained. Only two paced public listing requests were needed. The frozen report and tool are at `astra-submissions/analysis/v30-draw-conversion-20261011/` and `astra-submissions/tools/audit_public_draws.py`; full snapshot/replays are on Seagate.

The independent terminal-gap experiment continues on cores 6–7, no GPU. This conversion diagnosis does not change its frozen binary or criteria. No new release ZIP or arena upload is implied.
