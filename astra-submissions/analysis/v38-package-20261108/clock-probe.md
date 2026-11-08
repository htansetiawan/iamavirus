# Clock probe: retain the failure and test the actual time control

The initial protocol stress script supplied 0.2 seconds at a new game's first
decision. The candidate forfeited; the original `zip-smokes.json` is retained.
The same probe against the unchanged v37 production binary also forfeits; see
`cold-subincrement-control.json`. Native `main.c` lines 324/332 override search
time with 0.3 seconds below a 20-second remaining clock. This is inherited,
not introduced by the scorer change.

That clock prompt is outside the 180+2 game's reachable turn-clock range:
the first clock is 180; after each successful move, nonnegative remaining time
plus the two-second increment is at least two. The corrected compatibility
probe checks 180 and two seconds, both colors, including a subsequent decision.
The first-turn two-second probe is deliberately harsher than an actual late
turn because it also includes cold first-search work.

This changes the validation fixture, not the ZIP or any running game. Preserve
the original failure; do not advertise support for sub-increment time controls.
Observation/guard work can still consume part of a real clock, so the ordinary
full-clock, turn-isolated games remain necessary. All 32 Misty games keep their
unchanged zero-technical-fault condition.
