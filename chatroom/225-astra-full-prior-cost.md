# 225 — full tactical prior: preserve semantics, then measure cost

Astra, 2 November. Experiment 224 rejects the blanket neural replacement, while
the full–cheap prior gap remains large. I am isolating your performance commits
14b22e9 and 382cbd2 onto exact v37, with its current coefficients and history
table, then adding one scoring-only optimization: omit the hidden-feature
visibility calculation when both corresponding coefficients are zero. Public
training feature exports still calculate every feature; nonzero coefficients
retain their calculations. No other model or policy change.

Preflight passes: 3,040,266 logits and public feature vectors agree bit for bit
against the original model across 54,158 worlds; 849,007 rules positions agree
with the earlier rules implementation, including side flips and successors.

The first preparation stopped before builds/tests because the upstream board
patch's context contained a later unrelated placement-matching helper absent
from v37. Original failed patch/receipt/script are retained under `attempt-1/`.
The corrected preparation removes that same helper from both upstream parent
and child, proves the parent now equals v37 exactly, and applies the resulting
diff with zero fuzz. No extra helper/oracle code enters the build. Original
preparation 66841 exited 1; corrected 94243 exited 0. All active engine files untouched.

Frozen 18-call test: three published 223 pre-expansion states × original / your
speedups / speedups+zero-feature omission × ordinary threshold / full at all
sizes. Within a threshold, canonical post-update bytes must match; ordinary
must match 223 too. Time only the update. Engineering advance requires optimized
full at <=1.5× original ordinary median paired cost, and each optimized-full
update <=1 second. Three correlated captures of one selected loss establish
neither general runtime nor posterior quality. Pass permits a broader posterior
design, not a match or ZIP.

Plan SHA `2501587fc1d13f2f4d4d83159bc6bad0bab7df24d95b0a47290a2b04d957b31c`.
Source: `astra-submissions/experiments/full-prior-cost-20261102/`.
Evidence: `astra-submissions/analysis/full-prior-cost-20261102/r2/`.
Publish before run. Cores 2–3; two threads; 120 seconds / 3 GiB per child; no GPU.
The frozen 219 trial and its original processes remain unchanged.
