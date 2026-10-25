# Astra 142 — Completed teacher gate: more search does not overcome hard exclusions

2026-10-25. To Henry and Fable. This completes a bounded data/teacher validation
step for the DeepRL plan; no GPU training or new bot tournament was started.

**The 80-position paired teacher gate provides no immediate-safety improvement.**
At 0.4 seconds the base makes 10 fatal choices; at 1.6 seconds the teacher makes
11. There is one rescue, two regressions and 77 unchanged binary outcomes.
Exact two-sided discordant-pair p=1; this does not establish that more search
is globally weaker. The panel does not measure nonfatal strategic improvements.

Both budgets used the same frozen belief, sample, root actions and exclusions
inside one process. Execution order alternated. All 80 pairs completed within
the ten-minute cap and passed numerical export checks. The teacher is the raw
root selector; only the base was also checked through the final front end.

**Five of the base's ten fatal choices are imposed by the supplied action set:**
the king guard explicitly excluded every actual escape before CFR ran. These
are `5osaf68l:77`, `xg494buf:99`, `2w26eevv:71`, `ob3vxglp:89` and `jeoowbe2:168`.
Four attack cases also have no currently attacking hypothesis in the sampled
worlds; one overlaps the exclusion cases. Treat these as separate failure labels.

A learned prior behind an unchanged hard mask cannot choose the excluded move.
For `π(a|I) ∝ M(I,a) exp(fθ(I,a))`, `M=0` makes its probability and own-logit
derivative zero. Distilling the masked teacher cannot repair that action support.
This is why I recommend reviewing **posterior/danger calibration and uncertain
root exclusions together** before spending the proposed bulk-training budget.
It is not evidence to disable the guard globally or start another scalar sweep.
The existing neural model already has a danger head and candidate-wise BCE
training; we should assess that implementation and its calibration, not invent
another duplicate head. Keep omitted actions distinct from negative targets.

Data quality is now independently checked: **512 games, 40,348 frames, 80,696
attacker-set comparisons and 1,336 events** agree with the Python referee and
saved census. Where an escape exists, immediate failure follows 166/528 hidden
attacks (31.44%) versus 62/682 visible attacks (9.09%). The game-clustered
difference interval is 17.95–26.74 percentage points. This remains an association,
not causal concealment value. The derived diagnostic panel has five composable
patterns with 16 cases each and one case per game; it is not guaranteed unseen
by older fitted models.

The 80 paired cases cost 494.3 seconds, of which 138.5 was search plus export;
355.8 was startup/prefix/guard/teardown work. Production collection should reuse
live engine processes and reconstructed prefixes. A GPU does not accelerate
that CPU work automatically.

Review artifacts:

- [Teacher gate and exact excluded moves](../astra-submissions/analysis/deeprl-table-audit-20261025/teacher-readiness-report.md)
- [Machine-readable gate summary](../astra-submissions/analysis/deeprl-table-audit-20261025/teacher-readiness-80-summary.json)
- [Independent replay audit and fixed panel](../astra-submissions/analysis/hidden-slider-zone-20261025/independent-audit-512/README.md)

Cores 0–1 have been released. The two previously registered full-clock screens
continue at their fixed caps. The new model/training plan remains with the
committee for review; this result should inform that review.
