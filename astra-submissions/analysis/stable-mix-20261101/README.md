# Stable root-mixture pilot — 1 November 2026

Status: **closed, no promotion: 1W–0D–3L against v37 at 180+2.**
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

All four first attempts finished without protocol, illegal-move, clock or
infrastructure faults. The 369 replay frames validate. White scored 1–1 and
Black 0–2. The predeclared score-at-most-1/4 stop applies: the eight conditional
Misty jobs were never started, and no ZIP was produced. Both runner sessions
terminated with exit 0 and their CPU reservations were released.

There were 183 candidate decisions, 83 with eligible alternative probability,
and 30 non-argmax choices. The post-hoc `decision-audit.json` finds no immediate
king loss among those 30; all three terminal losses chose the argmax. Three
non-argmax moves have limited true-board exchange exposure, of which one was
exploited in the recorded three-ply horizon (net two points). This does not
establish causality or absolve earlier random choices. The logs record action
indices, not the unplayed argmax's UCI move; no saving counterfactual is claimed.

`disposition.json` distinguishes completed and conditionally unstarted cells.
`arena-refresh.json` records six newly fetched public replays, collected
separately and never added to this frozen test. Four games suffice to apply
the conservative stopping rule, not to estimate Elo or reject mixed play in
general. No threshold sweep or retry follows this result.

Initial match tool sessions: lane 0 = 6056, lane 1 = 54147; both completed.
Do not restart these first attempts. The frozen worker script verifies all
dependency hashes and independently validates every recorded frame against
the project's rules implementation when the course referee finishes.
