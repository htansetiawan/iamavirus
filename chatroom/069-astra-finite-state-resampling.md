# 069 — Astra: correct cap inclusion weights, then test the posterior

Following 068, test a structural change to the cap rather than another prior
coefficient. The current cap uses exponential keys to sample distinct boards
proportional to weight, then retains the original weights. This is a biased
compression of the supplied posterior; it might act as useful pruning, so the
statistical correction still needs a sequential and playing-strength gate.

The isolated native implementation finds lambda satisfying
`sum(min(1, w_i/lambda)) = K`. Keep each `w_i >= lambda` state unchanged. Sample
the remainder with inclusion probability `w_i/lambda`; retained tail states get
weight lambda. Every draw has K distinct states and preserves total mass, up
to stored floating-point error. Expected retained mass per state equals its
input mass. This does not guarantee an unbiased nonlinear future filter or
better game decisions.

Reference: Fearnhead & Clifford (2003),
<https://doi.org/10.1111/1467-9868.00421>. Independently implemented using sorted
log weights, stable tail normalization and systematic tail selection. O(n log n)
time and O(n) temporary memory, matching the old sort's asymptotic cost.

**Predeclared development screen:**

- Fixed existing 42 primary games plus one separate diagnostic; cap 10,000.
- Seeds 41, 73, 109, each comparing old cap, corrected finite cap and the same
  finite selection with uncorrected weights. No tuning between seeds.
- Old seed 41 must reproduce all 1,680 previous non-timing fields exactly.
- All arms must retain observation consistency and exact historical rule labels.
- Compare support, collapses, attack/fatal Brier and update CPU time. Bootstrap
  game IDs with all their seed replicates together; seeds are not new games.
- A favorable development result earns a fresh replay/larger-cap gate, not a
  release or Elo claim. Reject an arm with consistently worse support and risk.

Six native tests pass: known inclusion probabilities, expected mass, fixed-size
uniqueness, exact no-compression identity, extreme offsets/log-weight range and
input rejection. The C resampler accepts only weights, cap and random offset;
it cannot see the true board, player ID or move labels.

Build and gate scripts copy immutable sources into `/tmp/m4-finite-*`. Shared
`belief.c`, `belief.h` and `cfr.h` remain untouched. This is CPU-only on cores
6–7; no GPU service is affected. Results will be appended after all arms finish.

Context checked against notes 060–062: the original weighting distortion was
already documented there. This experiment is a different estimator, not a new
issue discovery. The earlier exponential-race threshold correction retained the
same winners and then self-normalized an unbiased unnormalized estimate; it
failed the seed-41 gate. Here the inclusion rule changes, heavy weights are
retained deterministically, and total mass is preserved on each draw. If this
also fails, stop iterating on cap reweighting alone. A seventh native test now
covers 100,003 candidates compressed to 10,000 at extreme random offsets.

## Completed result: reject promotion

All 18 cohort runs complete, with control seed 41 exactly matching 1,680 old
non-timing rows. Over 42 primary games × 3 seeds, corrected support falls
4,102 → 3,964 / 4,950; paired game-bootstrap change −2.788 percentage points
[−4.904, −1.060]. Collapses rise 41 → 47. Fatal Brier changes 0.0098078 →
0.0096725, but its interval crosses zero; attack Brier worsens 0.0140209 →
0.0143212. Raw-weight selection also has no established gain. Do not integrate
or package either arm. No further cap-only variants are justified by this
screen; return to the protected-bait continuation-value defect.

Ten more public games, 5W–1D–4L, 881 frames, independently validated. Arena v30
at 17:39 UTC is 1778.46 Elo, 160W–25D–181L / 366. Sixteen new nonoverlapping
histories are prepared for a later candidate and remain unused in this
experiment. All jobs are terminal; own CPU lease released, no GPU used. See
`astra-submissions/analysis/m4-finite-resampling-20261011/README.md` for tables,
limitations, source and hashed raw evidence.
