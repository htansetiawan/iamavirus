# Observable-loss projection of the learned response

1 November 2026. One separate correction to experiment 209, with its ongoing
full-game trial and all dependencies left unchanged. Fable's core source is
untouched. This is not a released bot.

Experiment 210 found that the frozen student assigned 8.0415% average mass to
provably losing actions on 640 validation decisions with both such actions
and alternatives. The recorded players selected none. All 3,171 positive
action proofs agreed with the independent rules engine. These are development
data and do not establish why experiment 209 loses full games.

For the fixed learned response q, let D contain legal actions whose immediate
king loss is provable from the actor's own observation. Set q'(a)=0 on D and
q'(a)=q(a)/sum(q(b), b outside D) otherwise. This is the minimum KL(q'||q)
projection onto those zero-probability constraints. Retain q when every action
is proven losing or surviving probability is zero. The diagnostic all_proven
counter includes both fallback cases. Relative probabilities among surviving
actions are preserved; no model retraining or new hyperparameter is involved.

This is an opponent-rationality assumption, not a rule forbidding legal moves.
Hidden attackers remain uncertain, and the free adversarial strategy retains
all legal actions. Search still uses 0.25*q' + 0.75*free_strategy. Belief,
guards, Stockfish, root purification, time allocation and model bytes match
209. The information-set adapter sees only actor-canonical observations and
legal actions. Repeated information sets must have identical inputs.

## Frozen decision gate

Before execution, select eight fresh November 1 v37 games by ID hash, four
per colour, excluding earlier fixed-tree, history-response and 209 panels.
No result is used for selection. Use own turns 9,17,25 and the final two own
decisions, deduplicated. This gives at most 40 positions and 160 executions;
endpoint selection makes this a diagnostic, not a population sample.

Four arms, rotated order, identical seed 2111101 and 2.5-second search cap:

- original: exact v37;
- learned: frozen 209 binary, confidence 0.25;
- off: new binary with projection disabled, confidence still 0.25;
- projected: new binary with ASTRA_VISIBLE_PROJECT=1, confidence 0.25.

Sequential execution uses cores 4,5, with a 120-second per-call timeout that
includes rebuilding observation history. Previous own moves are forced;
truth, opponent observations and future actions never enter the policy.
Independent rules labels are joined only after all policy calls finish.

To earn manual review before a separately frozen full-game trial, require:

- No protocol/rules/model/input errors; projection applied at least once.
- No additional immediate king losses or four-point queen exchange losses
  compared with any of the three controls.
- At most one additional bounded two-point exchange loss compared with the
  worst control, with changed tactical failures reviewed before advancement.
- At least three choices different from off, exceeding off-versus-learned
  differences by at least two. Those controls expose timing/patch noise.
- At least 75% of searched positions have first-reply learned coverage of
  at least 0.5; median model plus projection time at most 0.25 seconds.

Native proof edge fixtures and integration ASan/UBSan tests precede the gate.
The unchanged adapter/CFR source inherits 209's parity and solver checks.
The frozen plan pins binaries, model, source, runner, Stockfish, history and
private replay inputs. Report all arms, timings and failures. Do not retune on
this panel if it fails. Passing is not evidence for an arena ZIP. No GPU.
