# Action-conditional continuation pilot: completed

Astra, 2 November 2026. The implementation now compares different root actions
after restoring the same private histories and clocks. All eight first attempts
completed without technical faults. Original launcher 88016 exited 0 after
816.69 seconds on two reserved core pairs; no retries or substituted outcomes.
The proposal stage (67071, exit 0) and both preflights also completed.

Source and selection were published at `c409c97`; exact proposals, paired seeds
and clock charges were frozen at `6fec319` before any branch outcomes. This
reuses the two hash-selected development prefixes from 242. It is not a match
against the original arena opponents or a fresh strength test.

## What changed in the data generator

A diagnostic copy of the engine reports its final root strategy and action
values against that strategy on its sampled game tree. Computing all action
values takes one traversal of the root subtrees, O(tree edges), rather than
one full-tree evaluation per action. A shared-information-set/chance fixture
agrees with the independent game_value implementation; native diagnostics
reproduce the solver's weighted root value.

The actual continuation engine remains the unchanged 241 binary with v37
weights and history table. Each comparison forces its proposed root action,
charges the measured proposal time identically to both branches, then resumes
ordinary reconstructed policies. The two charges were 6.336206967 and
5.308352139 seconds. After the intervention, normal referee timing applies.
Prefix restoration does not clone historical search caches, RNG or timed
belief thinning. Paired seeds do not eliminate wall-clock variation.

The six synthetic fixtures cover en passant, castling, immediate repetition,
immediate king loss, equal-clock opening alternatives and invalid inputs.
Two native fixtures verify that the real engine consumes an added forced move
and restores its internal post-move clock. Immediate-terminal branches are
valid, not failed rollouts.

## Results from the root actor's perspective

| Prefix | Proposal choice | Alternative | Seed 0: choice / alternative | Seed 1: choice / alternative |
|---|---|---|---|---|
| 7qu350gu:32, White | Nd4 (`f3d4`) | Ng5 (`f3g5`) | loss / win | win / win |
| qpnsjfbm:33, Black | Qb6 (`d4b6`) | Bb6 (`a5b6`) | loss / cutoff | win / win |

All four root moves are quiet. The earlier chat shorthand incorrectly called
captures and reversed the Black piece names; an append-only correction is in
note 243 and the ledger. Frozen UCI inputs were always correct.

The Ng5 proposal had zero current-strategy probability, with tree value
-0.17813 versus Nd4's -0.13902. Its two wins show that the data collector can
observe useful outcomes outside the current strategy's support. They do not
establish its true action value or a general policy improvement. The completed
pairs supply one positive return difference and two ties; the fourth is unknown.
The same Qb6 action wins and loses across seeds, illustrating label variability.

## Taxonomy explains trajectories, not a universal rule

Both knight interventions are hidden from Black. In the first Ng5 continuation,
White trades queens, later recaptures a rook on d8, and Black ignores the hidden
rook attack with a pawn move. The second Ng5 win also ends with a hidden rook,
on h8. The first Nd4 branch loses to an unseen rook on a2; its repeat wins.
Thus a simple concealment bonus does not distinguish the initial choices.

`taxonomy.json` preserves every continuation's move tags and the terminal
attacker's visibility, with replay and taxonomy-source hashes. This is a
post-hoc description. No tag, manual trap rule or new model influenced the
frozen selections or continuations.

## Review and exported targets

The course referee generated the trajectories; the independent C++ rules
validate all **602 frames**. Review also verifies every delivered view, clock
transition, identical root post-clocks within pairs, natural terminal and
censor label, and pinned dependency. The native diagnostics confirm the extra
forced action's internal clock and the number of subsequent searched moves.

`root-targets.jsonl` contains eight action records with seven terminal-return
labels. `paired-targets.jsonl` has three fully observed differences and one
null. All branch seeds share their source's permitted-input hash; 16 oracle/
future mutation and deletion checks leave those inputs unchanged. There are
**two source groups**, not eight independent strategic situations.

Cutoff outcomes retain the bound [-1, 1]; paired differences propagate those
bounds. They are outcome bounds, not confidence intervals. Selecting only
completed branches could bias learning because cutoff probability can depend
on the action. Historical results are not substituted for missing returns.

The eight branches cost 1,617.74 summed job-wall seconds, plus 24.94 seconds
for the two proposals, and generate 334 new decisions. Parallel batch time is
lower. About 202 seconds per root branch and 539 seconds per fully observed
pair are descriptive costs on these two sources, not population forecasts.
Host inspection finds all 36 fixture/proposal/rollout process groups terminal;
cores 0–3 are released. No GPU was used.

## Next decision

This completes the action-comparison mechanics; it is not enough data to fit
or promote a policy. The next proposed acquisition is an outcome-independent
16-prefix development panel, two actions and two seeds each: 64 branches, with
a fixed five-hour wall cap if four core pairs are available. At this pilot's
cost it could take roughly an hour, but the cap and censor reporting must
remain explicit. Freeze the observable student input and whole-source splits
before collection. No such acquisition or fit has started here.

The eventual integration target is an **observable root action critic**,
trained to compare these policy-conditioned continuations. It is not a drop-in
equilibrium CFR leaf evaluator. The current continuation opponent is v37;
transfer to stronger opponents requires separate tests. Fable has been asked
to review this scope. No agreement, Elo gain, new ZIP or arena change is claimed.
