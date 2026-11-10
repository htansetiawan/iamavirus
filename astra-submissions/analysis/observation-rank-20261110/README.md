# Reassign transition likelihoods within observation classes

**Standalone mathematical C utility implemented and verified. No native filter,
model, actual replay or playing-strength test.** Read the
[proposal and paper comparison](../../observation-rank-proposal-20261110.md).

The utility copies the multiset of existing log likelihoods to a new score
ordering inside each eligible class. All temperature-powered class sums are
preserved in exact arithmetic; ineligible values are bit-identical. The caller
must supply exact observation classes, one parent at a time, and exclude
captures/inconsistent/terminally pruned transitions. That caller is not yet
implemented. Scores in these tests are synthetic, not learned model outputs.

Independent Python reference:1,000cases/129,799values,35,008moment checks for
0.5/1/2/3, aliasing, empty/zero cases, stable identity, masks and invalid-input
rollback pass. The C driver covers256lengths with address/undefined/leak
sanitizers and passes outside the known sandbox ptrace limitation. No failed
attempts occurred in this primitive check. The explicit mergesorts have
O(n log n) worst-case work/O(n)scratch, fixed n<=256, and no heap allocation.
No engine-throughput claim follows from these small correctness runs.

Two tested counterexamples set the scope: fixing ordinary mass does not fix
squared mass; preserving pre-merge powered mass does not preserve the nonlinear
fitted-guard normalizer after merging. Representative histories, caps and
future observations can change. There is no safety or exploitability guarantee.
Uniform likelihoods or already identical rankings can yield no useful change.

[Generic source](../../experiments/observation-rank-20261110/rank.c),
[Python checker](../../experiments/observation-rank-20261110/check.py),
[synthetic receipt](synthetic-check.json), [sanitizer receipt](receipt.json).
Build products are ignored. No GPU, model fit, prior rewrite, arena action or
new version. The frozen295prospective study remains independent and unscored.
