# 251: can extra opponent histories change the represented search game?

Experiment 250 changed posterior probabilities without establishing a benefit.
Before integrating its histories into GT-CFR, isolate the information-set
question with fixed physical states, weights and continuation payoffs.

Hypothesis: our current information set fixes our past moves. An opponent
history contains its own past moves. The two action sequences identify a
physical board/rule state from the known starting position. Within this
restricted subgame, a remembered opponent history therefore belongs to one
root state. Multiple histories for that same state may simply duplicate
identical continuation problems for the opponent. They do not introduce the
alternative locations of our pieces that the opponent cannot rule out.

This is an inference about our subgame construction, not a claim that the
opponent knows our board in the real game. Do not confuse it with Obscuro's
"one-sided GT-CFR", which names an expansion rule, not this root restriction.
Source context: https://arxiv.org/html/2506.01242v2, sections 3.1, B.2 and C.6.
The broader knowledge-limited construction is already implemented in our old
M4 branch and has negative screens; it is not a newly discovered free upgrade.

Native tests first: use immutable v37 PCFR+ on paired trees whose physical
branches and payoffs are identical. Compare one opponent history per state
with several histories that only split identical copies, for 2,048 updates
and two initialization modes. Separately verify a positive control: an actual
additional private state coupled through the opponent's information set must
change game value. Replicating states must not simulate that extra knowledge.

Frozen data: reuse the 24 experiment-250 games, one retained decision per game
with the greatest mass outside the heaviest history (ties prefer later ply).
This is actor-derived selection, independent of truth/outcome, and deliberately
stresses history multiplicity. Reconstruct both corrected filters once from
permitted observations and own moves. Dump states, representative histories,
and all conditional history masses. Verify against the prior saved marginals.
Stop on any mismatch, technical failure or exceeded bounds; no retries.

For each selected decision, sample 32 physical states with replacement under
the representative filter, using fixed seeds 251–254; use the exact same
states/weights for both history assignments. Compare actual opponent-history
and next-observation partitions after every common legal root move. Check
whether an information set ever spans distinct starting physical states and
whether each duplicate history has the same action/observation partition.

If histories only create equivalent copies, do not launch a costly full-game
experiment for this change alone. If they create substantive coupling between
distinct physical roots, retain those cases for a separately planned search
test. Neither result establishes arena strength. No Stockfish, GPU, model fit,
production edit, guard change or ZIP. CPU0–1; 60 seconds per replay subprocess,
15-minute batch cap. The source and selection are published before collection.

Even when the mathematical game is equivalent, adaptive expansion, unscaled
initial regrets, sampling and floating-point effects can change a finite
implementation. The tests do not claim byte-identical full GT-CFR behavior.
