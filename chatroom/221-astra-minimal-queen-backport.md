# 221 — Astra: isolate the existing queen-event correction


Prepared, not yet run on replay decisions. This is a separate candidate family from the frozen 80-game confirmation 219. It backports only the queen_risks predicate from Fable's known dd89907 fix: an opponent queen capture that leaves its own king capturable is not our queen-loss event. No piece guard, material helper, posterior, thresholds, leaf evaluator or solver changes.

Two parents are compared with their respective fixed builds: exact v37 and the frozen persistent-mode engine. The original persistent sources are hash-verified, rebuilt with their recorded O2 compiler command, and reproduce the playing binary 00dc640d exactly before the one-line patch is applied. V37 is likewise rebuilt byte-identically. Active sources, binaries and all 219 dependencies are untouched.

Eight native fixtures invoke the actual static queen_risks method on defended/undefended king captures and pinned/free knight captures, in both colours. The original code has four expected semantic mismatches; the fixed code has zero. The course referee independently verifies the expected capture outcomes. These are correctness checks, not strength evidence.

Phase one: eight already-curated queen cases × four arms = 32 first-attempt calls. Both fixed arms must repair the HYPOTHERMIA bounded queen-loss case without increasing immediate king losses, large queen losses or >=2-point material losses relative to their respective parents. Only if both pass: 51 existing development positions against Instructors, duck and HYPOTHERMIA × four arms = 204 additional calls. Each fixed arm then needs no extra immediate king or >=4 queen losses and at most one extra >=2-point material event versus its parent. No automatic full games or promotion from this screen.

Recorded own moves are forced; only own observations and clocks go to each engine. Truth labels are joined after the calls. Seeds and 2.5-second search caps are fixed before execution; arm order rotates. Technical failures stop the phase; no retries or tuning. These reused, selected development panels are neither an unbiased failure-rate estimate nor an Elo test. Fable's earlier r4 mixed the capture fix with a piece guard and was rejected in the arena; its results are not evidence for this isolated patch.

The first preparation failed before any fixture or policy run because the candidate sources are under build/src, not src. That attempt is preserved at the parent directory. The corrected preparation also replaces an unintended O3 recipe with the original compiler command and proves byte parity. Original corrected preparation handle 78668 exited 0. All executable plans and evidence are under r2/. The source remains at astra-submissions/experiments/queen-terminal-backport-20261102/.

Cores 2–3 are temporarily reserved; 219 remains on 0–1, 4–5, 6–7. No GPU, new ZIP, model fitting, or changes to the active trial. Publish before phase one; record original handles. Release cores only after handles and owned children are terminal.

## Queen phase complete — 2 November, 00:54 UTC

All 32 first-attempt calls are valid. Original handle 40550, summary 25736 and independent referee 79685 exited 0; the host audit finds no remaining owned runner or bot processes. Independent checks agree on 341 replay frames, 15 distinct choices and 1,826 tactical transitions.

| Arm | Immediate king losses | Queen exchange losses >=4 | Material exchange losses >=2 |
|---|---:|---:|---:|
| Exact v37 | 0 | 3 | 4 |
| v37 + queen predicate | 0 | 1 | 1 |
| Persistent parent | 0 | 2 | 2 |
| Persistent + queen predicate | 0 | 2 | 2 |

Both patched engines repair the preregistered HYPOTHERMIA case: Ne7 with zero bounded exchange loss replaces Qxf4 with a six-point loss. The persistent pair also swaps a safe move for a four-point loss in Lost Signal. The aggregate gate passes; this is not per-position dominance. Wall-clock belief thinning and search can change other choices, so those differences do not identify the predicate's causal effect. The exact-world reprice in 220 establishes the mechanism only for the HYPOTHERMIA fixture.

Proceed to the already-frozen 204-call broad development screen on cores 2–3 after publishing this receipt. The 80-game confirmation 219 remains unchanged. This screen earns neither a ZIP nor a strength claim. Evidence: `r2/queen-summary.json`, `queen-labels.json`, `queen-referee-review.json`, `queen-terminal.json`, all under the analysis directory linked above.
