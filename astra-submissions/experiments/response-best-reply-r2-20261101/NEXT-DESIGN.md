# Proposed structural successor: persistent opponent-mode search

Review proposal after213. Not an implementation, launch approval, or strength
claim. Existing211 bytes and its frozen match gate remain unchanged.

Objective: use the learned visible-response policy without assuming a new
independent opportunity for a model-constrained mistake at every future reply.
Use one latent mode for the entire searched continuation: model-fixed with
probability .25, adversarial-free with .75. Retain both until a leaf. Our
information sets must be shared across modes; we cannot observe this coin.
The opponent information sets distinguish the two modes. Model-mode nodes
follow q; free-mode nodes have every legal action available to the solver.

For fixed own strategy x and adversarial y, the finite-game objective is
`0.25*u(x,q) + 0.75*u(x,y)`. The learner optimizes x against y, with one shared
x across modes. This is a root uncertainty change, not local confidence tuning.
Keep the frozen student and visible-loss projection to isolate that change.

Foundational prototype before engine integration:

1. Build the explicit doubled small game with shared own information sets.
   Check utilities against the weighted sum of two separately evaluated games.
   At p=0 recover unrestricted CFR; at p=1 recover a response to q. Check that
   observations do not reveal the latent mode and that our strategies cannot
   condition on it. Compare solver solutions with an independent small-game LP.
2. Test the five-reply trap in the213 report plus imperfect-information games
   with multiple worlds, repeated own actions and observation branching. Test
   regret and reach propagation; do not substitute a mixture of final actions
   or reset the mode when a new opponent information set is visited.
3. Before full chess runs, audit the same-tree worst-response gap, normalized
   chance shares, recall keys and allocation failure handling. Zero-confidence
   output must preserve baseline distribution and bytes where appropriate.

Initial engine route: replicate each sampled world into two mode-tagged
continuations with shares .25*w and .75*w. Share own history keys exactly;
include mode only in opponent infoset keys and leaf state. Carry it through
every expansion. Keep belief, guards, leaf evaluator and clock unchanged.
The extra branch cost is real: record memory, nodes/second, neural calls and
each mode's expansion coverage under the same wall-clock budget. Reject early
if losing search depth erases any decision advantage. Do not promise a2x gain
from a shared traversal before implementing and measuring one.

The theorem concerns mixed strategies in the finite game. The existing root
argmax would discard that property. Keep this explicit in evaluation: compare
model-mode versus unrestricted search with the **same** root action-selection
rule, and separately report mixed-strategy safety. Do not attribute a gain to
the opponent-mode change while also quietly changing root sampling. A runtime
mixed-policy test needs its own matched control and gate; the earlier failed
stable-top-three heuristic is not a substitute for that comparison.

The213 cases are development diagnostics only. Any advancement needs unseen
private-history decisions, then full180+2 paired games against exact reference
bytes and an authentic opponent. Set counts and thresholds before running;
do not optimize this proposal against three handpicked positions.

Remaining risks: q lacks private memory; an observation-likelihood advantage
does not establish calibration on search-generated positions; two modes can
be the wrong opponent model; re-solving every turn does not preserve a global
full-game guarantee; Stockfish leaves and finite world/tree coverage remain
approximate. RNR is a hypothesis to test, not inherently superior to a
properly calibrated data-biased response.
