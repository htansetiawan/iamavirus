# Root-loss correction: implemented, tested, not promoted

1 November 2026. **No positive replay signal. No new ZIP and no full-game trial
for this change.** The feature remains off in the isolated experimental build;
Fable's engine and submissions were not edited.

The implementation reuses the larger-belief king-risk scan to replace the
sampled immediate-loss component inside growing-tree CFR:
`V_sample + L*(p_belief-p_sample)`. The sampled component is subtracted to avoid
double-counting. See the [implementation](../../experiments/root-loss-cv-20261101/README.md).

## Frozen development comparison

The same 51 decisions from 25 contributing Nov1 v35 games against Instructors,
duck and HYPOTHERMIA used in the fresh-taxonomy report. Both colours, wins and
losses, exposure/fatal/material cohorts and controls. These are development
cases already inspected, not a new held-out playing-strength test.

Original v35, patched CV-off, patched CV-on; same seed 11012026 and 2.5-second
cap, rotated order, cores 0–1. All 153 runs receive only the player's own
observations, clocks and forced own moves. No ground truth goes to the policy;
no recorded reply is applied after a changed move. Hashes, inputs and environment
are in `development/pins.json`; all cases completed exactly once (`audit.json`).

| Diagnostic | v35 | Patched off | Patched on |
|---|---:|---:|---:|
| Immediate fatal choice | 10 | 10 | 10 |
| Net loss >=2 in the limited exchange probe | 5 | 5 | 5 |
| Queen net loss >=4 | 0 | 0 | 0 |
| Capture with no king-safe response | 1 | 1 | 1 |
| Protocol errors / illegal moves | 0 / 0 | 0 / 0 | 0 / 0 |

CV-on fixes two king-loss decisions and breaks two, relative to both controls.
The patched-off control changes four moves from original v35 but no failure
labels. CV-on changes nine moves from patched-off, seven from original v35.
No material label changes. Median per-case on/off elapsed ratio is 1.00175;
median node ratio is 1.000. This screen finds no large runtime cost, but elapsed
includes rebuilding the forced prefix and is not a full-game clock test.

## What the traces show

Four extra print-only diagnostic runs are kept separately in
`correction-traces.json`; their moves are not added to the gate. Logging and
wall-clock belief thinning can affect the result.

| Case | Change in the gate | What the diagnostic found |
|---|---|---|
| d28cm7j9:75 | Fatal Kh7-g7 -> safe h5-h4 | h5-h4 loses in 9.375% of sampled mass but 1.245% of the larger scan; its correction is +0.163. The safe move was over-penalized by the sample. |
| i3xv2i71:79 | Safe Kg6-h5 -> fatal Kg6-h6 | Fatal h6 gets +0.104 versus safe h5 +0.029. The larger belief assigns *lower* risk to the fatal move, 1.026% versus 1.666%. |
| r82lsby1:80 | Safe Ka2-b1 -> fatal b2-b4 | b2-b4 gets +0.016 while b1 gets -0.022. Removing sample overestimation makes the fatal move more attractive under the existing posterior. |
| uczoi2xj:66 | Fatal Kh2-g2 -> safe Kh2-h3 | The diagnostic reverts to fatal g2; h3 is absent from the retained root actions in that run. This apparent fix is unstable. |

This is evidence against spending a match lane on this implementation now.
It does not prove every variance-reduction method is useless. It shows why a
more accurate expectation under the current posterior need not improve the
chosen move on the true board. Changing the multiplier after seeing these four
positions would be tuning to this sample, not a justified release.

## Correctness

Five native runs pass: equivalent entry rewards versus terminal rewards
(500 PCFR iterations, both players' best responses and exploitability), root
integration for both board colours and sharp/flat weights, Kuhn poker, and
address/undefined-behaviour sanitizer versions of the first two tests. Root
integration covers opposing-king capture priority, illegal-world fallback,
merged draw shares, zero correction under complete enumeration, and survival
of the correction through leaf growth. Raw evidence and hashes are in
`../../experiments/root-loss-cv-20261101/correctness.json`.

The first sanitizer attempt failed because LeakSanitizer cannot run under the
sandbox's ptrace layer; rerunning outside that layer passed. Three exact toy
estimator tests also pass. These are correctness checks, not strength evidence.

## Next question for Fable

Measure calibration for the **exact immediate king-loss event** on a fresh,
representative collection of complete games before fitting a correction.
The existing hazard study labels attacks on knight/bishop/rook/queen
destinations; its 2–7x ratios must not be transferred to king loss. This 51-case
failure-stratified set cannot supply population calibration either.

Collect all permitted root moves and predicted event probabilities with the
same capped belief machinery, then join true-board labels offline. Freeze
game-level chronological train/validation/test splits, keep played moves
separate from all candidate moves, and compare raw probabilities with a small
fitted calibrator using held-out proper scores and event counts. If that does
not improve the relevant estimates, stop before another engine change.
If it does, this tested entry-reward interface can support a separate
terminal-risk replacement experiment. That would change the model, and would
not inherit the unbiasedness claim of this control-variate calculation.

No such fitted calibrator or gain is claimed here. Queen/material risk still
needs exchange and continuation accounting; this immediate-terminal interface
does not solve it.
