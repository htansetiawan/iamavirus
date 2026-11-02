# 255: profile whole-search cost after the exact solver gate

254 is closed before full games: 1.252x faster fixed-tree solver work yielded
only 1.021x median nodes at equal search time, below its declared threshold.
Fable's note 051 already establishes that Stockfish scoring, rather than pipe
transport, was expensive in v9. This experiment measures the current v37 and
exact optimized solver, separating growth/cache/strategy costs from solver
traversal and Stockfish calls. It does not retest asynchronous search or MultiPV.

Profiling-only wrappers preserve original function bodies. A nested stack
records exclusive wall and parent-thread CPU time for solver iterations,
strategy computation, array growth, tree selection, child expansion and
Stockfish calls. Remaining search work has a separate bucket. Nested calls
within one bucket are charged once. CPU is the main search thread only;
Stockfish worker CPU is excluded. Wall minus CPU includes waiting and scheduler
delay and cannot be called pipe overhead. Mode is reported explicitly: original
v37 uses synchronous rounds by default, with asynchronous search opt-in.

Require deterministic nested-timer accounting and complete-engine fixed-work
parity for both colors before profiling. Use the eight previously selected
cost cases (227/253), chosen by belief population without outcomes. Run four
arms per case: original v37, profiled original, exact optimized solver, and
profiled optimized solver. Rotate order across cases. The unprofiled controls
measure whether instrumentation substantially changes achieved work, but
independent processes and adaptive belief thinning prevent a precise overhead
or causal speed estimate. No outcome-based case selection or retries.

32 first attempts, 2.5-second maximum search budget, cores 0–1, 120-second
per-process cap and 20-minute total bound. Public replay truth is used only
after exit to validate moves; input is own observations, clocks and forced own
moves. Stop on technical failure. Verify bucket sums and all final choices
against the course referee. No GPU, model update, strength gate or ZIP.

Use the measured cost shares to bound possible improvements and select the next
mechanism. Do not claim that eliminating CPU work saves the same amount of wall
time when workers overlap it; nor that more nodes alone improve playing strength.
