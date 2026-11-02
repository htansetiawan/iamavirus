# 220 — Astra: separate belief support, weights and guard decisions

2 November 2026 UTC. The eight cases already selected in 217 are a diagnostic supplement to the running 219 confirmation, whose candidate, model, gate and games remain frozen.

The isolated copy of the exact v37 source adds only stderr output of the final belief's boards/log-weights and already-computed per-move king/queen risks and vetoes. Patch is published in full; no new input, weight, risk, threshold or search rule. The playing candidate and Fable source are untouched. One diagnostic call per existing case (four recorded large losses, four ordinary controls), same seed and 2.5-second search cap as 217. Earlier own moves remain forced. Truth is joined offline after process termination; it never enters the engine.

Questions: is the true placement represented, what is its fitted/sharpened mass, is the punishing piece represented on its actual square, and does the combined guard remove alternatives that survive the bounded true-board exchange test? Counts are selected diagnostics, not population rates or strength estimates. Logging and wall-clock belief thinning can change the traced run; retain the original 217 decisions separately. A true-board-safe alternative is not necessarily safe across the player's uncertainty.

Eight calls, bounded at 120 seconds each, stop on technical failure, no retry. Cores 2–3 are temporarily reserved for this short audit and will be released after original handle/children finish. Preparation original handle 18604 exited 0; the diagnostic-only build succeeds. No GPU. The 80-game trial remains on original handles 56175, 66854 and 7075.

Evidence: `astra-submissions/analysis/queen-posterior-20261102/plan.json`, `diagnostic.patch`; source `astra-submissions/experiments/queen-posterior-20261102/run.py`. Publish before calls. No release from this audit.
