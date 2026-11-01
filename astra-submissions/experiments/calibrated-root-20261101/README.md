# Calibrated root terminal risk

1 November 2026. An isolated v35 experiment. No release ZIP, promotion or
change to Fable's source. The trained curve is frozen from the separate
king-event calibration experiment; its test data will not be used to refit it.

## Hypothesis and treatment

The exact immediate king-loss probabilities underestimate observed events on
held-out reconstructed v35 decisions. Does using the fitted correction in
search improve decisions, with the existing guards unchanged?

`MIST_ROOT_CALIB=0` is the default, feature-off control. `=1` selects the
probability mixture, `=2` the additive residual. Other values disable it.
The belief model, history table, Stockfish, guard thresholds, time budget,
root purification and random seeds remain the v35 settings.

Let L be the existing root-loss payoff (-2), p the immediate-loss mass in the
sampled worlds, q the calibrated larger-belief probability, and V_safe the
conditional expected continuation in non-losing sampled worlds.

- Mixture: `L*q + (1-q)*V_safe`. Losing terminal values receive multiplier
  `q/p`; safe branches receive `(1-q)/safe_mass`. If p=0, all safe branches
  also receive a single entry reward L*q. If no safe continuation exists,
  retain the original value rather than invent a continuation.
- Residual: `V_sample + L*(q-p)`. This replaces the terminal-loss component
  but retains the original probability mass on surviving continuations.

The exact event includes move legality and opposing-king capture precedence.
Both variants reuse the sharp king-risk scan at the existing guard; a missing
cache key receives no correction. In particular, disabling the king guard or
forcing a historical prefix disables collection of this cache. Single-choice
positions also bypass it. Forced prefixes therefore stay identical.

An entry reward survives conversion of a frontier leaf into a decision node.
Each safe frontier stores its positive utility multiplier, which is applied
to every new child's utility and inherited by its future frontier. Both
players' regret updates therefore see the same zero-sum payoff transformation.
The correction is not merely applied to the displayed root value.

This is an action-dependent surrogate game. It does not define a coherent new
posterior over all boards, fix relative move-risk rankings, or establish a
Nash guarantee. The calibration clips input probabilities; even a raw 0/1 is
mapped inside (0,1). That limitation is shared by both experimental variants;
there are no special thresholds fitted to the inspected test data.

## Correctness and development screen

`build_experiment.py` verifies the v35 ZIP hash and overlays only the files in
`src/`. `run_checks.py` checks both colours and all three modes against an
independent oracle that transforms explicit terminal utilities. Coverage
includes merged sample shares, no losses, no survivors, nearly-zero survival,
calibration endpoints, two generations of tree growth, both best responses
and 300 PCFR iterations. Existing entry-reward and Kuhn tests remain included.
Sanitized runs check memory and undefined behaviour.

The four-arm replay screen uses the already-inspected 51 fresh-taxonomy cases
from 25 games. It is a development screen, not held-out strength evidence.
Arms: immutable v35, patched-off, mixture, residual. Rotate order per case,
seed 11012026, 2.5 seconds, exclusive cores 0-1. Each arm sees only its own
observation history and forced own moves. Truth is used after exit to judge
the choice; no recorded opponent reply is followed after a changed move.

Decision rule fixed before running: any protocol or legality error stops the
screen. A variant earns independent confirmation only if combined fatal or
material events improve by at least three net cases, immediate fatalities
decrease, and neither material-loss nor queen-loss counts increase versus v35.
Inspect the feature-off control and paired cases before attributing a gain.
No local full-game lane or release follows a null result. An accepted screen
still needs independent confirmation and actual games, including v35 and an
authentic opponent; calibration scores alone do not demonstrate strength.
