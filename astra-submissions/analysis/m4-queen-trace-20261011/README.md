# Queen-loss continuation follow-up: earlier decision did not reproduce

A searched-prefix trace using the same seed12 and frozen default-off settling
candidate chose **Qd4-f4**, rather than the previously repeated Na4-c3. Earlier
wall-clock searches produced 91 current roots rather than 76. This trace is
retained as a divergent diagnostic, not substituted for the earlier results.

The complete trace contains 91 roots and 2,781 board-node records. The independent
referee validates every exported path and finds one exact true-state root.
After Qf4 in that true state it finds no opponent reply forcing an immediate
loss by our next turn. The chosen move nevertheless has 30.47% immediate-loss
share under the search's effective gadget reach across other worlds. This
share is not the belief posterior or a calibrated probability of losing.

The intended question—whether the actual Nc6xd4 queen capture is sufficiently
searched after Na4-c3—remains unanswered by this selected-move trace. Do not
rerun until the desired answer appears. Extend post-selection diagnostics to
inspect a nominated alternative in the same saved tree, or freeze a repeatable
search state/budget before making a causal search comparison.

The trace adds about 9 ms after selection and is not a tournament clock test.
The raw JSONL is losslessly retained as `trace.jsonl.gz`; its uncompressed hash
matches `probe.json`. The frozen input manifest and independent audit are kept
alongside it. No candidate policy or arena submission changed.
