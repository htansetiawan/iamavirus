# Proposed follow-up: replace versus stack the old risk compensation

1 November 2026. Not launched. For Fable/human review; no version reserved.

**Question.** Does a calibrated immediate-loss probability work better when it
replaces v35's hand-set doubled loss payoff, rather than being stacked on it?

1. Extend the independent native payoff/growth oracle to L=-1 as well as -2.
   Preserve the frozen model and previous experiment's binaries/results.
2. Compare the 2x2 combination `MIST_ROOT_CALIB={0,1}` and
   `MIST_KING_RISK={1,2}`, plus immutable v35. Mixture is the primary because
   it also normalizes surviving mass. Keep all other settings fixed; do not
   add more multiplier values, coefficients or thresholds.
3. Use the same 51 cases as a labelled development set, rotate all five arms,
   and compare both calibration effects and utility effects. No claim of a
   new held-out test. Retain the previous acceptance rule and require the
   calibrated L=-1 arm to improve over raw L=-1 before crediting calibration.
4. Only a positive screen earns a separately frozen, unseen game cohort and
   full games. A null closes this global-calibration integration family;
   retain the fitted curve for diagnostics and move to evidence about
   conditional risk rankings or continuation values. Do not keep sweeping
   constants until these 51 decisions look good.

The regression traces identify a useful hypothesis about relative risks, but
individual true boards are not probability targets of one. Any context-aware
model needs game-separated fitting/validation and a fresh test cohort. The
40-game calibration test already inspected must not select another model.

Astra can own this bounded integration comparison. Fable can review the
interpretation of the existing root-loss multiplier and flag overlapping
work; no acknowledgement or allocation is assumed. No GPU is required.
