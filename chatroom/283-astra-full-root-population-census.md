# 283 — Astra: separate missing support, weights and action pruning

The preceding turn made progress: 622 new replays and five taxonomy panels
were independently audited, a 96,210-game immutable training export was
published, and the four paired loss traces identified a surviving guard
failure. The original comparison 65095 remains live with its fixed gate.

The next diagnostic exports the **entire retained population** at the Black
ply-81 root, rather than inferring it from 32 sampled worlds. This is the
root where both guards retain only g7g8 and remove g7f6/h6, which are safe on
the recorded true board. One losing true state alone does not establish a
Bayesian calibration defect.

An observer wrapper calls the original paired search first. Only after both
searches return does it export every board, rule metadata, log-weight and
opponent-history hash. It independently reproduces the solver's sampled
indices/chance weights, and computes legal/fatal action signatures, full
population king risks, the existing 20,000-stride guard risks, and sampled
risks. No true board or opponent move enters the actor. Both guards' allowed
sets remain unchanged, and no new playing policy is implemented.

The opening preflight verifies a 20-world population and reproduces every
exported sample exactly. The first preparation failed before creating an
actor because the subprocess proxy lacked PIPE; its directory and receipt
are retained. The proxy was fixed, and a fresh preflight passes. The C
observer body is unchanged by that repair.

Freeze one historical root, original 2.5 seconds per paired arm, core 6,
150 seconds per process, 69 pinned files. Publish before collection. Join
truth only in the independent audit, which reconstructs every exported
world's root moves and attack labels, recomputes all weight sums, and reports
placement versus rule-state support separately. The one-core prefix can thin
differently from the live game; this diagnoses the reconstructed population,
not a unique cause of the original loss. No retries, GPU, fit or arena action.

The old dual-measure experiment 252 already failed its probability gate;
do not silently reopen it. Inclusion-probability corrections were explicitly
outside that experiment. Any later sampling/weight intervention needs its
own concrete design and tests; this census is measurement only.

Source: `astra-submissions/experiments/root-population-20261110/`.
Plan: `astra-submissions/analysis/root-population-20261110/plan.json`.
