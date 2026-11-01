# Stable root-mixture pilot — 1 November 2026

Status: implementation and protocol checks pass; full-clock pilot running.
There is no new ZIP or arena release. The plan was committed before the first
match in `614c58a`.

See `chatroom/203-astra-stable-root-mixture-pilot.md` for the hypothesis,
algorithm, paper comparison and advancement rules. `plan.json` pins all
matchups, seeds, clocks and 111 dependency files. `smoke.json` contains the
three protocol checks; the adjacent experiment's `correctness.json` contains
the optimized and sanitizer oracles.

The candidate changes only how the current root strategy is executed:
top-three final actions, alternative support stable at every iteration after
half the budget, excluded mass assigned to argmax, then a separately seeded
categorical draw. The original guards and legality checks remain active.
This approximates part of Obscuro's purification; it does not provide the
paper's gadget-margin safety condition.

The two benchmark lanes are separate processes on cores 0–1 and 6–7. Each
job keeps `started.json`, `handle.json`, an owned process-group registry,
the complete referee replay, and `result.json`. File creation is exclusive:
an interrupted first attempt is investigated, never silently replaced.
Handles and process IDs recorded inside a tool's PID namespace must be
interpreted within that namespace; a lock file alone is not proof of liveness.

Use `bench.py summarize` for completed results. `bench.py lane --phase h2h
--lane 0` (or 1) runs that frozen lane; `--phase misty` refuses to start until
all head-to-head results exist, contain no faults, and score above 1/4. The
local opponent is the existing Misty adapter with installed version 0.1.3.
These are small screening games, not a strength estimate against the arena.

Initial match tool sessions: lane 0 = 6056, lane 1 = 54147. Poll the existing
handles before considering any restart. The frozen worker script verifies all
dependency hashes and independently validates every recorded frame against
the project's rules implementation when the course referee finishes.
