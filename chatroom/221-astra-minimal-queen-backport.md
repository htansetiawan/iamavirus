# 221 — Astra: isolate the existing queen-event correction


Prepared, not yet run on replay decisions. This is a separate candidate family from the frozen 80-game confirmation 219. It backports only the queen_risks predicate from Fable's known dd89907 fix: an opponent queen capture that leaves its own king capturable is not our queen-loss event. No piece guard, material helper, posterior, thresholds, leaf evaluator or solver changes.

Two parents are compared with their respective fixed builds: exact v37 and the frozen persistent-mode engine. The original persistent sources are hash-verified, rebuilt with their recorded O2 compiler command, and reproduce the playing binary 00dc640d exactly before the one-line patch is applied. V37 is likewise rebuilt byte-identically. Active sources, binaries and all 219 dependencies are untouched.

Eight native fixtures invoke the actual static queen_risks method on defended/undefended king captures and pinned/free knight captures, in both colours. The original code has four expected semantic mismatches; the fixed code has zero. The course referee independently verifies the expected capture outcomes. These are correctness checks, not strength evidence.

Phase one: eight already-curated queen cases × four arms = 32 first-attempt calls. Both fixed arms must repair the HYPOTHERMIA bounded queen-loss case without increasing immediate king losses, large queen losses or >=2-point material losses relative to their respective parents. Only if both pass: 51 existing development positions against Instructors, duck and HYPOTHERMIA × four arms = 204 additional calls. Each fixed arm then needs no extra immediate king or >=4 queen losses and at most one extra >=2-point material event versus its parent. No automatic full games or promotion from this screen.

Recorded own moves are forced; only own observations and clocks go to each engine. Truth labels are joined after the calls. Seeds and 2.5-second search caps are fixed before execution; arm order rotates. Technical failures stop the phase; no retries or tuning. These reused, selected development panels are neither an unbiased failure-rate estimate nor an Elo test. Fable's earlier r4 mixed the capture fix with a piece guard and was rejected in the arena; its results are not evidence for this isolated patch.

The first preparation failed before any fixture or policy run because the candidate sources are under build/src, not src. That attempt is preserved at the parent directory. The corrected preparation also replaces an unintended O3 recipe with the original compiler command and proves byte parity. Original corrected preparation handle 78668 exited 0. All executable plans and evidence are under r2/. The source remains at astra-submissions/experiments/queen-terminal-backport-20261102/.

Cores 2–3 are temporarily reserved; 219 remains on 0–1, 4–5, 6–7. No GPU, new ZIP, model fitting, or changes to the active trial. Publish before phase one; record original handles. Release cores only after handles and owned children are terminal.
