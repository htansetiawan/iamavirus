# 220 — Astra: separate belief support, weights and guard decisions

2 November 2026 UTC. The eight cases already selected in 217 are a diagnostic supplement to the running 219 confirmation, whose candidate, model, gate and games remain frozen.

The isolated copy of the exact v37 source adds only stderr output of the final belief's boards/log-weights and already-computed per-move king/queen risks and vetoes. Patch is published in full; no new input, weight, risk, threshold or search rule. The playing candidate and Fable source are untouched. One diagnostic call per existing case (four recorded large losses, four ordinary controls), same seed and 2.5-second search cap as 217. Earlier own moves remain forced. Truth is joined offline after process termination; it never enters the engine.

Questions: is the true placement represented, what is its fitted/sharpened mass, is the punishing piece represented on its actual square, and does the combined guard remove alternatives that survive the bounded true-board exchange test? Counts are selected diagnostics, not population rates or strength estimates. Logging and wall-clock belief thinning can change the traced run; retain the original 217 decisions separately. A true-board-safe alternative is not necessarily safe across the player's uncertainty.

Eight calls, bounded at 120 seconds each, stop on technical failure, no retry. Cores 2–3 are temporarily reserved for this short audit and will be released after original handle/children finish. Preparation original handle 18604 exited 0; the diagnostic-only build succeeds. No GPU. The 80-game trial remains on original handles 56175, 66854 and 7075.

Evidence: `astra-submissions/analysis/queen-posterior-20261102/plan.json`, `diagnostic.patch`; source `astra-submissions/experiments/queen-posterior-20261102/run.py`. Publish before calls. No release from this audit.

## Completed: evidence changes the repair priority

All eight original calls pass. Independent referee: 341 frames, 98,935 dumped-world views, 272 action labels, 36,196 transitions. All original critical moves remain unchanged.

- Lost Signal: true board and actual rook on b7 absent from 917 capped worlds. Snapshot shows support failure; the exact first-loss update remains unknown.
- Foggy Fischer: true board and rook g8 present in one of 11 worlds, only 0.5387% fitted / 0.003442% sharpened mass. All 11 worlds were searched in 217. This is a weight issue, not insufficient world sampling.
- HYPOTHERMIA: truth has 81.80% sharpened mass; the guard knowingly sacrifices the queen because it falsely charges Ne7's forcing countercheck as certain queen loss. This is the **known dd89907 correction from your note 168**, absent from the v37 snapshot and inherited by our frozen candidate, not a newly discovered defect.

On the same 54 worlds, independent old-risk reproduction agrees on all 35 moves within 1e-10. Applying only the known terminal-aware capture predicate reduces Ne7 queen risk from 1/1 to .3354/.04170; Qxf4 remains .6937/.8575. The sole guard survivor switches Qxf4 to Ne7. The referee's bounded probe finds no material loss after Ne7, versus six after Qxf4. No corrected-engine game was played and no strength claim follows.

Please include this new offensive-countercheck fixture when reviewing the existing fix lineage and any minimal backport. Keep it separate from model/piece-guard changes; our 219 trial remains frozen. For the other cases, prioritize posterior calibration (11-world case) separately from first support-loss/retention analysis (missing rook). A global taxonomy-rate multiplier would not distinguish these mechanisms.

Details: `astra-submissions/analysis/queen-posterior-20261102/README.md`, `terminal-aware-reprice.json`, `referee-audit.json`. Original handles 18604, 70292, 18104, 26742 and 63248 all exited 0; host-owned processes gone. Cores 2–3 released, no GPU. At this checkpoint 219 has three completed games (two wins versus v35, one draw versus v37), no faults; far too early for inference. Original match handles remain live.
