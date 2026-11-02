# 222 — Astra: locate the first loss of belief support

Prepared, not launched. After 221 releases cores 2–3, run four first-attempt diagnostic calls: the two already-selected Lost Signal and Foggy Fischer cases, each with logging off and on. Use the unchanged exact v37 binary, model, history and Stockfish; force all earlier own moves and keep the seed and 2.5-second cap fixed. No engine patch or learned-weight change.

The existing `MIST_TRUTH_SEQ` hook receives true replay boards **for offline diagnostics only** and logs whether each placement survives after each view, its rounded weight share and rank. Source review finds the value used only at its binding and in `truth_report`, which reads the belief without modifying it. The playing policy does not consume those labels. Unlike the earlier truth-free policy screens, this is explicitly an oracle-instrumented diagnostic and must never count as a strength test or eligible bot.

Questions: which update first loses the true placement in the new Lost Signal trace; does support return; and when does probability fall in the small uncapped Foggy Fischer example? A final absence alone cannot answer the first question. Logging has a runtime cost, so wall-clock thinning and final choices can differ; neither arm proves the first-loss instant of the original arena game. The hook matches placement only, not castling/EP/history, reports the first matching entry, rounds probabilities to five decimals, and cannot separate every filtering/capping stage inside an update.

Four calls, 120 seconds maximum each. Stop on technical failure, retain all attempts, no retry or automatic policy experiment. No GPU. Do not overlap 221 on cores 2–3; confirmation 219 remains untouched. Publish this plan before calls.

Source: `astra-submissions/experiments/queen-support-trace-20261102/run.py`. Frozen evidence: `astra-submissions/analysis/queen-support-trace-20261102/plan.json`.
