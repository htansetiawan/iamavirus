# Action-conditional continuation pilot

Experiment 243 builds on verified 241/242 mechanics. It compares the actual
normal-budget proposal with the highest-valued other view-legal move retained
by that proposal's CFR search. Values are against the final strategy on its
sampled tree, not truth-board or equilibrium certificates. A diagnostic-only
source copy reports the root strategy and action values in O(tree edges).
Actual continuations retain the unchanged 241 binary and v37 model/table.

Reuse precisely the two hash-selected development prefixes of 242; no new
holdout or strength claim. One proposal call per prefix. Its measured root
decision cost is charged identically to both action interventions. The engine
receives its own historical moves plus its intervention and exact post-move
clocks; no hidden opponent moves or true board. After that action both players
resume their ordinary reconstructed policies, with a 10-second maximum.

Two actions × two prespecified seeds × two prefixes = eight runs. Seeds are
paired across actions and differ between replicates. Wall-clock nondeterminism
still exists. Sixty-four new plies including the intervention, 1,000 seconds
per run, 5,000 seconds per batch, two exclusive core pairs. Technical failures
stop new jobs; all first attempts and already-running jobs remain recorded.
Cutoffs have no terminal-return label. Immediate terminals are valid outcomes.

First publish source/selection/limits, then make the two proposals. Freeze their
hashes, selected actions, matched charges and all eight jobs before any action
continuations. A missing second supported action is recorded and stops this
pilot; no outcome-based substitution. Both proposals and all branches from a
source belong to one development group. This small pilot validates a useful
training interface and its cost; it cannot select a stronger policy or justify
a model fit, bulk data run, new ZIP or arena upload.

Commands: `build_proposer.py`, `preflight_branch.py`, then `experiment.py prepare`,
`experiment.py propose`, `experiment.py freeze`, `experiment.py launch` and
`experiment.py review`. Preparation and result artifacts are written once.
