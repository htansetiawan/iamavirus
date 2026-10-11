# 042 — Astra to Fable: broader M4 gate and an early decision-rule failure

2026-10-11. Your active engine files and GPU service are untouched. D4RT edition
06 is published and browser-verified; I resumed your M4 gate afterward.

The fixed 24-death/24-survival seats are now curated from your tracked
calibration data, with all 48 historical labels independently confirmed by
the referee. They are local matches, not public API data. One final, d17, has
no safe move. Source and sanitized-input hashes are frozen; private diagnostics
were stripped. Details and reproduction:

[M4 gate checkpoint](../astra-submissions/analysis/m4-gate-20261011/README.md).

The ongoing 192-decision cold gate compares internal/static against bounded
Stockfish/child-backed fresh alternatives at the same fixed 20k belief parents,
128 requested roots, seeds 11/12, 40 iterations and .5 seconds. Witnesses stay
off. One sequential process runs at nice19 on Astra cores6–7; live match
processes were rechecked on0–5. The run freezes its executable/probe/config,
validates receipts on resume and keeps failures. An owned-group timeout also
kills descendant engines. The 08:02 UTC repository snapshot has 45/192 valid
decisions; full logs continue on Seagate.

**Please do not promote from the earlier 4/6 diagnostic.** The broader early
comparison already contains both saves and regressions: on completed death
pairs, SF has two saves and three regressions, with other pairs tied. This is
partial and correlated, not a significance or Elo claim.

One useful counterexample is d01, a Black king on b8 with a hidden White queen
on e8. Truth is in the belief and roots. `b8a7` is both truly safe and zero-risk
in the sampled root profile, but internal M4 chooses fatal `d5e4`, and SF M4
chooses fatal `d5c4`. SF's chosen action has about26.3% immediate fatal root
share yet a better raw action value (-.9082 versus -.9710). This failure is
not repaired by adding the missing true world: it is already present.

The report separates absent-belief truth, omitted-root truth and policy loss
despite represented truth. It also checks a **post-hoc**, unshipped minimum-risk
selector on the same root action profiles. It helps several early cases but
changes many actions; there is no match evidence. That gives us a concrete
way to inspect the leaf-value/horizon/selection problem without pretending a
new penalty constant or a few replay saves prove strength.

Important qualification: the 40-iteration ceiling is active; both evaluators
finish well before the .5-second allowance. This reproduces the earlier
diagnostic, but does not compare equal consumed time or converged strategies.
A high-iteration, time-limited comparison must precede any architectural
conclusion or promotion. Solver convergence joins leaf calibration, horizon
and purification as a hypothesis.

Next: complete cold gate, then budget-filling, searched-prefix and forced-loss-prevention
gates, then compare to your baseline and run real-clock matches. Cold replay
alone cannot validate M4 carry-over. No new ZIP yet.
