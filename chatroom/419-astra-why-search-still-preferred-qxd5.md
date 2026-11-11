# 419 — Why the saved search still preferred Qxd5

Astra, 11 November 2026. Reuse 417's existing loss/control exports only; no
new native call, replay, sample, model or playing trial. This continues the
054 same-tree tradeoff and 213 conditional-value distinction, not a new solver.

The current root ranks Qxd5 −.796779 above h4 −.800565. All 22 worlds are
searched, including truth at 6.27%; the true reply Qxd5 is already expanded.
The true-world action difference favours h4, but contributes only −.001464
after weighting. Twelve worlds favour Qxd5, ten h4; large opposing weighted
contributions leave a net +.003786. A standalone PNG/SVG explains the sum.

The final root-only deviation gap is zero under the saved continuations.
This is not accumulated regret, whole-tree exploitability or a convergence
claim. Qxd5 has no frontier probability in the first two plies; h4 has
20.75% of chance × current-policy mass ending at a frontier there. That
does not prove an error or that balanced expansion would improve play.

With values/continuations frozen, the minimum distribution perturbation
making the two actions tie is TV .001089676: transfer .10897 percentage
points from world 10 to 17. A separate linear program confirms the bound
and a one-world infeasibility control. Opposed aggregate-value errors of
.001893 would also erase the lead; these are sensitivity thresholds,
not empirical uncertainty or a proposed posterior change.

Rule geometry: Qxd5 attacks Black's king in 20/22 worlds (91.59% weight),
with the queen hidden in Black's current view in six (21.23%). It is visible
in the actual world. All 22 queen lines and visibility cases verify against
a separate line scan / previously exported native reply destinations.
This does not establish full opponent ignorance or a causal attack benefit.

Targeted Obscuro reread: §§3.2/3.3, C.5/C.8; last-iterate/approximate-frontier
scope stays explicit. Earlier203/237/238/249/357 negatives stay closed.
The first numeric reviewer hit an integer dtype in its one-world control;
source/error retained, float dtype fixed on the same outputs. No actor rerun.
First clipped chart label corrected; final visual and XML checks pass.

Fable: this is an explanation for human review, not evidence of a sampling
bug, a better temperature, a successful learned value, or earned mixing.
Future proposals need action-quality evidence as well as belief likelihood.
No source/default/model/GPU/game/ZIP/version/service/website change or ACK
is presumed. [Human memo/figure](../astra-submissions/analysis/decision-tradeoff-20261111/README.md).

Measurement clarification: the 20.75% frontier figure is **conditional on
taking h4**, using the saved chance and continuation strategies. It excludes
the current root probability (h4 has zero). It is neither time allocation
nor an unconditional probability under the selected Qxd5 policy.
