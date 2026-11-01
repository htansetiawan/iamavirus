# Observable-loss response projection: execution record

1 November 2026. Source and the frozen 39-decision/four-arm plan were published
at `23cd116cc85bd1806d958f7b0f1f8b4d50e46ce3` before execution. The 156-call
replay gate is running on cores 4,5; session and worker are in `launch.json`.
No outcome is claimed before all planned calls and their labels complete.

The corrected distribution removes only actions whose terminal loss follows
from the acting player's permitted observation. It does not remove hidden-risk
actions, change the belief, or restrict the adversarial free strategy. This
is one isolated rationality assumption; it cannot repair every response-model
error or recover private history omitted by the current-view model.

For intuition, at a fixed opponent node let alpha be the original learned
probability on proven losses (payoff +1 to us), and v the expected payoff to
us on remaining actions. Before projection the fixed component has value
alpha + (1-alpha)*v; afterward it has value v. Holding the continuation and
free component fixed, confidence c changes our expected value by
-c*alpha*(1-v). Thus it removes an identifiable source of optimistic value.
This local identity does not prove a better root choice or stronger play after
the tree and regrets adapt. The predictive audit is not a causal explanation
of the parent candidate's losses.

The full parent experiment remains immutable. Its first six full-clock games
against v37 are losses without faults; all eight will be retained. No Misty
trial is possible under its frozen advancement threshold. The projection
variant must pass its own decision gate before any further match allocation.

## Harness interruption and explicit recovery

The original runner exited 1 after call 133 (`937dbqbv-41`, learned), despite
valid protocol and engine exit 0. It required model diagnostics whenever the
tree had nodes. This position had exactly one information set (our root), four
sampled worlds, 27 actions and 113 nodes = 1 + 4*(1+27). No opponent information
set was expanded; lazy model initialization never ran and no query report was
expected. The source confirms this path. The runner check was too broad.

The original execution.json remains failed and all 133 first-attempt records
and output hashes are preserved. recovery/plan.json freezes the 23 missing
cells only. The recovery accepts absent model diagnostics only when the log
proves the single-root structure; unexpected omissions still fail. Three
parser assertions check the actual case and reject changed set/node counts.
No binary, model, original plan, original runner, selection, timeout or scoring
threshold changes. No completed call is repeated. Recovery is published before
execution, and its combined report must disclose this interruption.

The parent full-game pilot is now complete: 0-8 against v37, no faults. Its
actual-opponent-response audit shows only 0.00758 nats gain from projection on
243 replies. This does not support a claim that projection explains or repairs
the match losses. It still needs its own completed decision gate.

## Completed gate

All 156 unique first-attempt cells are now complete: 133 preserved original
calls plus exactly 23 missing calls. No cell was repeated. The original failed
execution remains intact; completion.json and recovery/merged identify the
combined result. All outputs are legal and 595 frames validate.

| Arm | King loss | Exchange loss >=2 | Queen loss >=4 |
|---|---:|---:|---:|
| Original v37 | 6 | 1 | 0 |
| Raw learned response | 6 | 1 | 0 |
| New binary, projection off | 6 | 1 | 0 |
| Projected response | 6 | 1 | 0 |

Five projected choices differ from off; off and the raw parent agree on every
choice. Four projection changes return to original v37's move. The fifth
changes the rook move while retaining a four-point exchange vulnerability.
One separate two-point repair versus original balances that regression in the
aggregate count; neither is a forced-game-outcome claim. Independent referee
review checks 88 transitions/responses across 13 distinct tactical lines.

All frozen diagnostic checks pass, with 38 applicable model reports (one
root-only case), full first-reply coverage threshold compliance and 29.76 ms
median model/projection time. The mechanism works at low inference cost, but
there is no measured king/material label improvement. This earns only a
separately frozen small full-clock pilot. It does not justify a ZIP.
