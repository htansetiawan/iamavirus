# 227: where exact speed improvements go during a move

The 226 test establishes identical ordinary posterior outputs at about half
updater cost. It does not establish more search or better decisions under the
adaptive clock. This profile compares the complete original and optimized v37
engines with the same ordinary feature cutoff, model, guards and search.

Select eight decisions from the already evaluated 24-game panel using belief
size only: the four games with the largest maximum pre-update parent population,
then four remaining games whose largest decision population is nearest 1,000.
Within each game choose that maximum's earliest decision after own move eight.
Outcomes, played move and tactical labels never select cases. This is a selected
cost diagnostic, not held-out strength evidence.

Build production binaries first and require original to reproduce the immutable
v37 extraction. Profiling copies add clocks and one stderr line per searched
move, identically in both arms; no changed branch, payoff or model coefficient.
Replay permitted observations and forced own moves interactively. Only the final
decision searches. Measure that entire input/output turn, existing update/queen
logs, total guards, search time, requested budget, tree nodes and final belief
size. Turn clocks remain the recorded clocks; maximum search budget is 10 seconds.
This includes adaptive thinning and recovery, unlike 226. The optimized arm may
therefore keep a different belief: this is not another fixed-state parity test.

Sixteen first attempts, rotated order, cores 2–3, at most 120 seconds / 4 GiB
per process and 20 minutes total. No retries or GPU. One technical failure stops
the run. Recheck all dependencies before execution; publish before launch.

True-board immediate king loss and bounded exchange labels are joined after
engine exit. They are diagnostic only. No release/strength gate is attached to
these eight selected cases. Use the measured stage costs to choose one next
resource-allocation experiment, rather than claim updater speed is Elo or silently
enable the full prior rejected by 226. Independent ordinary parity remains the
separate 225/226 result. All original/frozen experiment files remain unchanged.
