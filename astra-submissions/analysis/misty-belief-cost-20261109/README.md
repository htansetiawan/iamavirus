# Misty resource diagnostic: uncapped state growth is demonstrated

The stopped clock-aware comparison has five attempts: four normal games and
one Misty time forfeit at ply 85. Its fixed gate fails technically; 27 jobs
remain unstarted. There are only two clean matched White cells: candidate
one point, v38 control 1.5 points. No Black games or complete four-game seed
blocks exist. These counts support no strength or Elo conclusion. All 406
frames pass the independent course referee; our native bots had no technical
failure. Original session 89024 is terminal, and host cleanup finds no actors.

Installed engine_v2 defaults p_max_size to None, and the adapter inherited
that uncapped deployment setting. The strategy's five-second opening search
budget does not bound belief updates. To examine resource cost, the bounded
component replay used the same recorded observations and own moves, skipping
historical searches and optionally searching the last position. No opponent
hidden moves were supplied as observations. This is not a reproduction of
search values, carryover, random thinning or full-game timing.

| Diagnostic | Uncapped | Cap 200,000 |
|---|---:|---:|
| Maximum completed population | 2,992,741 | 200,000 |
| Completed all 86 observation frames and final search | no | yes |
| Exit | SIGABRT during opponent update at frame 83 | 0 |
| Runtime | 20.6 seconds | 6.8 seconds |
| Maximum RSS recorded at completed checkpoints | at least 906 MiB | 168 MiB |

The uncapped Rust update failed a 939,524,096-byte allocation under the
intentional 4 GiB address-space limit. That limit is stricter than a 4 GiB
resident-memory limit; this does not prove that an arena container would OOM.
The final timed-out live update was not instrumented, so the component trace
supports state-explosion risk without proving its exact live failure path.
The bounded trace finishes belief updates in 3.38 seconds total and its final
search in 2.90 seconds, returning a legal g5g4. Its population cap changes the
approximation and may drop true states; this is not an equivalent speedup or
evidence of playing strength. Both diagnostics used one core and left no
unverified process group.

At the live timeout, Misty had a king and four pawns, saw 11 squares, and
faced our rook, knight and three pawns plus king. We were seven material
points ahead. Loss of vision and hidden-piece mobility plausibly enlarge
consistent-state sets; the measured growth makes this a useful hypothesis
for future strategy analysis. The material advantage does not turn the
technical result into a clean game.

Next is score-independent qualification of a finite-cap local Misty against
unchanged v38 in both colors. Cap 200,000 is the exposed caller setting and
matches our deployed engine's ceiling; no installed code or candidate changes.
This will be a bounded local opponent, not verified current arena Misty.
