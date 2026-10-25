# 126 — Corpus-level en-passant action coverage

I applied the v35/patch `view_moves` probes to cached public replays from the
top-opponent set. First filtered 123,251 matching games; a move-coordinate
prefilter yielded 91,972 games with a diagonal pawn move on an EP rank. I then
verified before/after boards and found **8,056 actual EP actions in 7,827
games**.

Across those actions, v35's current-view list omitted **4,727 (58.7%)**. The
conservative observation patch recovered **4,102 (86.8% of omissions)**, with
625 still absent. Strongly Invisible: 1,166 omitted / 1,020 recovered;
Instructors: 942 / 840; Knight Vision: 765 / 646; Decent Chess Bot: 348 / 320;
Greek Gift: 262 / 221; duck: 251 / 205. Omissions appear in eventual wins,
losses, and draws; this measures action coverage, not causal result impact.

The derived 8,056-event dataset and summary are in
[`ep-target-inference-20261025`](../astra-submissions/analysis/ep-target-inference-20261025/README.md).
The patch now has three separate positive observations: 2,500 seeded legal
playouts with no illegal extra action seen, exact recovery on all six curated
replay observations (v35 2/6, patch 6/6), and a five-seed decision path where
it consistently restores the move used in an Instructors win. The remaining
625 corpus actions and a paired whole-game strength gate are still outstanding.
Keep this separate from the king-guard variant; do not label it an Elo gain.
