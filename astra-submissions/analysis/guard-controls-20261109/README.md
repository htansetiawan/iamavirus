# Guard-disagreement control screen

Frozen64decisions from32 unused historical v37games, four each against eight
relevant opponents. Dates November3–7; game-ID hash selects games, ply hash
selects a later own king move. Each game also contributes its third opening
decision. Two late cases use a general-move fallback. Selection uses no
results; it yields32White/32Black decisions and32opening/32later cases.
These are historical development controls, not a confirmatory arena sample.

One actor reconstructs one belief and searches both masks at2.5seconds each,
with the same seed, fresh identical v38 scorers and alternating arm order.
A raw-memory fingerprint and exported sampled worlds/weights verify that the
belief stays unchanged. Only the mask changes. Actor inputs are observations,
own forced moves and recorded clocks; true boards label choices after exit.
Forced replay does not reproduce historical Stockfish state or exact thinning.

Both-color same-mask and candidate-mask preflight passes. Budget overrides
apply only to this offline paired search; actual180+2 behavior requires full
games. Readout cost is outside the search allocation and included in total
recorded runtime. The existing bounded capture/response probe measures3+
material exposure; it is an omniscient diagnostic with a limited horizon.

Advance to the separately frozen16-game pilot only if all cases complete
without technical/illegal errors, at least4masks differ, at least1newly
admitted action is selected, at most1fatal case breaks, zero opening fatal
cases break, and at most2new3+material exposures occur. These are screening
limits, not a significance test. Fixes cannot cancel broken-case counts.

The initial provisional plan is preserved in prelaunch-plan-initial.json.
Before any actor run, the gate clarified broken versus net counts, added
zero opening breakages and verified owned process-group cleanup. The final
plan and all source hashes are published before the control cohort starts.
No failed first attempt is replaced. Case150s/global40min bound, one0–1pair.

Sources: [prepare](../../experiments/guard-controls-20261109/prepare.py),
[paired actor](../../experiments/guard-controls-20261109/pair.c),
[runner](../../experiments/guard-controls-20261109/run.py),
[review](../../experiments/guard-controls-20261109/review.py).
