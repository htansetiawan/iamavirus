# The learned response predicts visibly losing moves

1 November 2026. The frozen student gives nontrivial probability to moves that
the acting player can prove lose its king from its permitted observation.
This is a concrete model-fidelity defect, not a demonstrated explanation for
the concurrent full-game losses or an Elo result.

The first 100 validation games from experiment 208 supply 6,116 target-side
decisions. These games were already used for model selection; this is a
development audit. Of those decisions, 640 have both provably losing moves
and alternatives. The student assigns **8.0415% average probability** to the
provably losing group, while the recorded players select **zero** such moves.
Across all 6,116 decisions, the predicted mass is 0.8415%. There are 48
recorded true king-loss moves, all outside this sufficient visible proof.
That distinction matters: hidden mistakes must remain possible in the model.

The discrepancy appears in every target team; this is not a player-name rule.
The maximum predicted mass is 94.12% in `5nwm3pzf:68`, where 40 of 42 actions
are visibly losing and the recorded player picks a surviving action. These
are correlated descriptive observations, not independent trials or a fresh
confidence-bound claim.

The proof applies each legal candidate to known own/visible enemy pieces.
Pawn, knight and king attacks require a visible attacker; slider attacks also
require every intermediate square to be known empty after the move. Unknown
squares prevent a slider proof. Castling, en passant, promotion, removal of
captured attackers, and terminal king-capture precedence are handled.

All **3,171 positive action proofs** agree with the independent C++ rules;
all 8,413 replay frames validate. Native ASan/UBSan edge tests pass. The API
accepts only actor-canonical tokens and legal candidates, never a hidden board.
See [plan](plan.json), [results](result.json), [per-decision evidence](decisions.jsonl),
[sanitizers](sanitizers.json), and
[source](../../experiments/observable-response-audit-20261101/).

No model parameter or active benchmark dependency was changed. Experiment
209 continues its original eight full-clock games. A separate follow-up can
condition the fixed learned policy on non-proven-loss actions, preserving
their relative probabilities. This is a modelling assumption that the learned
component avoids observable dominated choices; the adversarial free strategy
can retain all legal actions. It is not a change to Fog of War's move rules,
and it must pass its own decision and full-game tests.
