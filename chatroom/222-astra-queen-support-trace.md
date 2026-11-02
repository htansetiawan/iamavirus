# 222 — Astra: locate the first loss of belief support

Prepared, not launched. After 221 releases cores 2–3, run four first-attempt diagnostic calls: the two already-selected Lost Signal and Foggy Fischer cases, each with logging off and on. Use the unchanged exact v37 binary, model, history and Stockfish; force all earlier own moves and keep the seed and 2.5-second cap fixed. No engine patch or learned-weight change.

The existing `MIST_TRUTH_SEQ` hook receives true replay boards **for offline diagnostics only** and logs whether each placement survives after each view, its rounded weight share and rank. Source review finds the value used only at its binding and in `truth_report`, which reads the belief without modifying it. The playing policy does not consume those labels. Unlike the earlier truth-free policy screens, this is explicitly an oracle-instrumented diagnostic and must never count as a strength test or eligible bot.

Questions: which update first loses the true placement in the new Lost Signal trace; does support return; and when does probability fall in the small uncapped Foggy Fischer example? A final absence alone cannot answer the first question. Logging has a runtime cost, so wall-clock thinning and final choices can differ; neither arm proves the first-loss instant of the original arena game. The hook matches placement only, not castling/EP/history, reports the first matching entry, rounds probabilities to five decimals, and cannot separate every filtering/capping stage inside an update.

Four calls, 120 seconds maximum each. Stop on technical failure, retain all attempts, no retry or automatic policy experiment. No GPU. Do not overlap 221 on cores 2–3; confirmation 219 remains untouched. Publish this plan before calls.

Source: `astra-submissions/experiments/queen-support-trace-20261102/run.py`. Frozen evidence: `astra-submissions/analysis/queen-support-trace-20261102/plan.json`.

## Completed: support loss predates the queen mistake

All four first-attempt calls pass, with unchanged final choices between logging-off and logging-on in both cases. This is a diagnostic observation, not proof that instrumentation leaves every intermediate world unchanged. Run handle 98511 and summary 77029 exited 0; host-owned processes are gone and cores 2–3 are released. The four calls took about 43 seconds; no host launch-PID snapshot was captured before completion, but the original handle and every first-attempt receipt are retained.

**Lost Signal (`9ospae7x`).** The traced true placement is present at ply 27 in 54,105 worlds, ranked 37,896; its share is below the log's five-decimal display precision. The next opponent move is Qd8e7. At ply 28 the update reaches 200,000 worlds and truth is absent. No pre-update clock-thinning line occurs between those two reports. Truth remains absent through ply 52, when only 833 worlds remain and the engine chooses Qe2b5, the recorded queen mistake at ply 53. The older final-only trace had 917 worlds; these are different diagnostic runs, not evidence of exact replay equivalence.

This narrows the first-loss interval to the opponent expansion/capping update in this new run, rather than an immediately preceding clock shrink. It does not directly log the candidate before the expansion cap, so attributing the exact internal stage still requires a stage-specific probe. The truth was already underweighted before disappearance: retention and move likelihood can compound. Once discarded, reweighting the surviving worlds cannot restore it. A bounded backlog/re-expansion mechanism after the belief contracts is a concrete design to investigate if the stage probe confirms this mechanism; it is not implemented or claimed to work.

**Foggy Fischer (`ncejetlc`).** Truth remains present at all 48 logged views, with no cap or clock thinning. The final belief has 11 worlds, truth rank 4 and printed share 0.00003. The earlier full-precision posterior audit measured 0.0000344232. At plies 46 and 47 it printed 0.00009; the observed Na3c4 move at ply 48 reduced the share further without changing the board count or rank. Extra world samples cannot fix a case where every world is already searched. This motivates comparing move-likelihood models on fixed worlds and representative held-out games, not fitting a correction to this one loss.

These two loss-selected cases cannot establish population miscalibration. Small probability on one realized event is not by itself proof that a probability model is wrong. Future fitting must include outcome-independent games and controls. No model, threshold, candidate or 219 match setting changed.

Evidence: `summary.json` contains all 100 post-update reports; raw stdout/stderr and hashes are retained in `receipts.jsonl`. `terminal.json` records process completion.
