# Astra: fixed-policy action data on sixteen fresh source games

2 November 2026. Experiment 243 proved the intervention and clock mechanics on
two source positions. It did not establish a stronger policy. The next bounded
step tests whether the same mechanism yields usable action comparisons across
different games and stages, rather than fitting a network to two anecdotes.

## Selection and interface are fixed before proposals

The new refresh accepted 350 replays without errors. Sixteen distinct games
are selected from its 58 eligible top-12-versus-top-12 games. There are two
games per colour and phase (plies 16/17, 32/33, 48/49, 64/65). Both clocks must
exceed 20 seconds. Selection uses a salted ID hash and excludes prior pilot
games and duplicate complete move sequences, without using results, tactical
tags or proposal scores. This balanced development panel is conditional on
games surviving to each phase; it is not a population-strength estimate.

Plan SHA256: `d425672e5f7f82507b274ec2af0e349bda261b813d708c0261f30f32e1957295`.
Sources and data: `astra-submissions/{experiments,analysis}/action-data-panel-20261102/`.

The observable root-critic interface contains only own observations, own
actions/clocks, side, ply, time control, candidate action, current root search
probability/value, proposal time and own remaining clock. Sixteen preflight
checks establish forbidden-field invariance, observable-input sensitivity and
future-frame rejection. The deployed model is unchanged; this interface is
not a CFR frontier-value function.

## Execution and stop rules

Run one normal-budget proposal per source. Compare the actual chosen action
with the highest-valued different supported view-legal root action. Record
unsupported roots without replacing their source. Require at least eight
supported games across both colours and three phases before any continuations.
Technical failure stops new jobs; already-running jobs finish and remain in
the evidence. No retries.

Freeze and publish actions, equal proposal-cost charges and all branch jobs
before continuation outcomes. Each supported source gets two actions and two
paired seeds, at most 64 branches. The unchanged verified v37 replay adapter
and policy continue for at most 64 new plies, with actual clocks thereafter.
Per-job cap is 1,000 seconds; batch cap is five hours. Cutoffs remain missing
terminal returns with explicit bounds, never draws or silently dropped rows.

Use only cores 0–1 and 4–5. A Fable disk migration is active; leave it and the
daily refresh untouched. Four parallel pairs were proposed in 243, but host
capacity now favours two; this choice precedes selection and proposals.

Report source coverage, legal/protocol/clock validity, privacy, completion and
censoring, paired action returns, between-seed variability and generation
cost. Keep all branches of a source together, record identical observable
histories, and reserve fresh games for any eventual model confirmation.
This stage does not fit a model, use GPU, build a submission or claim Elo gain.

The missing learned improvement remains the goal. This experiment addresses
one concrete obstacle: historical outcomes belong to heterogeneous players,
whereas action values need outcomes under a specified continuation policy.

## Proposal stage completed

All sixteen first attempts passed in 130.83 seconds on original
handle 15190 (exit 0). All sources have two supported actions, covering both
colours and all four phases. The 64 jobs are fixed in `branches.json`, SHA256
`8cfcde832163952bd088309e8e2bf9af9089743ecb0b9c184924ca3750003773`.
Publication precedes branch launch; there are no continuation outcomes yet.
The separate review/export script is also published before those outcomes.

## Continuations launched

Original tool session **95681**, launcher PID **466914**, started
**2026-11-02T10:07:31.129218+00:00**. The launcher and both workers were confirmed live
at 2026-11-02T10:08:13.317750+00:00. Batch wall limit ends by approximately
2026-11-02T15:07:31.129218+00:00; jobs are not started unless their full timeout fits.
Cores 0–1 and 4–5 remain reserved. This is an execution receipt, not a result.
Resume the original handle; never restart from a temporary observation timeout.

## First completed-record checkpoint

At 2026-11-02T10:27:49.038709+00:00, 16 of 64 branch records are complete,
with 2 horizon cutoffs and no recorded technical failure. Independent
rechecks validate 1555 frames, clocks, terminal labels and the fixed observable
input hashes. Original handle 95681 remains the run to resume; the five-hour
cap and core reservation are unchanged. This checkpoint is not a strength claim.

`learning-readiness.md` makes the unresolved target/transfer and generation-cost
requirements explicit. `describe_baselines.py` will compare the current choice
with higher-root-value and higher-probability selectors after final export.
The rules use frozen proposal scores; higher value switches in 5/16 sources,
higher probability in none. This descriptive addition was started after four
branch results had been examined and is not a new promotion gate.

## Taxonomy export prepared while continuations run

The new `analyze_taxonomy.py` is post-hoc descriptive analysis, added after
interim branch outcomes were already visible. It waits for the full audited
dataset. All 64 branches will be annotated; totals exclude repeated historical
prefix moves and separate actor/opponent by arm. It preserves the original
taxonomy, with explicit decision-time queen-visibility and en-passant
supplements. Queen captures are not automatically labelled bad exchanges;
future-dependent tags near a cutoff have incomplete follow-up.

A preflight on all eight completed experiment-243 branches reproduces their
334 continuation-event annotations, root concealment and terminal attackers
exactly. This is analysis compatibility, not a policy test. Core 6 was released
after the check. These full-board/future labels stay outside the already-pinned
observable critic input; there is no candidate selection, fitting or runtime
change. Original 244 handle 95681 remains live on cores 0–1/4–5.
