# 383 — Add an actual multi-world decision to the presentation

Astra, November 11 UTC. The 375 end-to-end case has one surviving world;
376 explains the earlier 14-world probabilities. Neither shows the default
32-draw search sampler on a larger retained population. This follow-up stays
within Henry's presentation-first phase; it is not a strength experiment.

The plan reuses the **unchanged 375 control and output-only trace binaries**,
the shipped v38 history and modified Stockfish, and the same already selected
`c8ozqj0m` win. No engine source change, build, candidate or model update.

Selection is fixed before action outputs: an all-forced, no-search probe of
White decisions through ply 14; choose the first at ply 6 or later with
33–4,096 retained worlds. Capping/thinning before that point is disallowed.
If none exists, report that outcome; no replacement game is selected here.
The selected prefix then gets one original-control and one annotated search,
two seconds each, fixed seed 3831111, 90-second call caps, exclusive cores 2–3.

Independent review must reconcile complete retained worlds with course-rule
enumeration, normalized log weights, sampled world/count shares, initial
frontier action values, the first shared-root CFR updates and final argmax.
Recorded truth joins only in review. The bot inputs contain White's views,
clocks and earlier own actions; no opponent move or full-board input.

Plan SHA-256:
`5f36a8c1c77dc22f6fa52b972ef9c671aefd607e94fd05dd349875fb8176a4fa`.

- [Plan](../astra-submissions/analysis/presentation-multistate-20261111/plan.json)
- [Runner](../astra-submissions/tools/trace_multistate_presentation.py)

Forced history, shortened time and logging prevent a claim of reproducing the
arena's tree, probabilities or move. Control/trace differences are not a speed
or strength estimate. No new gate, fit, GPU, game, service, package, version,
commit, push or deployment; existing negative experiments remain closed.
