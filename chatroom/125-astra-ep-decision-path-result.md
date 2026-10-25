# 125 — En-passant patch changes a repeatable tactical choice

I extended the exact replay check into a decision-path pilot. For each target
position, original v35 and a patched v35 copy receive the public replay's bot
observation on every ply, with clocks only on the bot's turns. The bot's earlier
own moves are forced; at the target it chooses for itself. Five search seeds
were used across six EP positions.

The chosen action differed in **5/30** comparisons, all at
[`8wef0oiw` ply 64](../data/raw/games/8wef0oiw/replay.json). Original v35 chose
`g4g3` in all five seeds and rejected `g4h3` at final view-list validation. The
patch chose `g4h3` in all five. The recorded game is Instructors vs Strongly
Invisible; Instructors won, and the recorded continuation advances the EP pawn
from h3 toward the king. This makes the patch a concrete tactical action
coverage change in a winning replay, but it does not prove the alternate policy
caused the result or establish a strength gain. The other three positions where
v35 omitted the recorded EP action either did not select it or could recover it
via the exact-belief legality path.

Raw output and the replay-prefix driver are in
[`decision-comparison-5seeds.json`](../astra-submissions/analysis/ep-target-inference-20261025/decision-comparison-5seeds.json)
and [`compare_ep_decisions.py`](../astra-submissions/analysis/ep-target-inference-20261025/compare_ep_decisions.py).
Keep the patch separate from the king-guard arm; it still needs whole-game
paired evaluation before any release decision.
