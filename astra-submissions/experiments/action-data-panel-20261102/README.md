# 244: distinct-source root action data

This expands the verified 243 action-intervention mechanism to sixteen new
development games. It is data acquisition, not a model fit or strength trial.
The unchanged proposer/rollout binaries and v37 model/table remain pinned.

Source: new IDs from the bounded latest-400 refresh started 2 November09:47UTC,
completed after the previous refresh ended. Both teams must be in that new
snapshot's top12. Select two distinct source games for each of four fixed
ply bands (16,32,48,64) × two actor colours. Black uses the following odd ply.
Both recorded clocks must exceed20seconds at the branch. Select by a salted
ID hash, late buckets first, without inspecting outcomes, tactical tags or
proposal scores. Deduplicate complete move sequences and exclude241/242games.
No replacements after proposals. This is a deliberately balanced development
panel conditional on reaching those phases, not an arena population estimate.

One normal-budget proposal per prefix. Supported means the actual choice and
at least one different view-legal CFR root move. No second supported move is
an eligibility outcome, not a reason to retry or replace the source. Require
at least eight supported games spanning both colours and three phases before
spending time on branches. Other technical failures stop the stage, retaining
already-live jobs. Freeze supported actions, equal proposal-time charges and
all jobs before continuation outcomes.

Each supported case gets two actions × two paired seeds, at most64branches.
Normal10-second maximum budgets,64newplies including the intervention,
1,000seconds/job,18,000seconds/batch, two reserved core pairs (0–1 and4–5).
The host has a running disk migration; remaining cores are left available for
it and the daily refresh. This resource choice is fixed before proposals. Proposed
actions come only from the observable proposal, never a recorded future move
or a true-board evaluation. The environment checks legality after selection.
No failed attempts are retried. Cutoffs stay censored with return bounds.

The future learner input is fixed in input_contract.py: own observation/move/
clock history, side/ply/time control, candidate UCI, its current root strategy
probability and tree value, proposal time and resulting own clock. No team
identity, source/seed ID, opponent private information, true board, future move
or outcome enters that input. A root critic is not a CFR leaf-value network.

All branches and replicas of one source stay in one split. Record shared
observable-history hashes too. The output is for development; a later model
must use fresh confirmation games. Report support coverage, censored pairs,
between-seed label variability and cost. Do not market a favourable pair count
as a stronger playing policy. There is no fitting, GPU use, ZIP or arena upload.
