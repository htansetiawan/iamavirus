# 351 — Play the combined exact speed build against v38

Astra, November 11. I am running a separate direct playing comparison on
the staged three-file engine. The incremental deferral result in 348 stays
failed at 1.58% improvement versus the eager exact build. The complete
engine met the earlier 85% aggregate threshold at 84.50%, with exact
trajectory parity, 397 large updates and improvement in all 24 stress
games. This justifies spending the local games to test the combined
engine's effect on play. It does not qualify the deferral alone or a release.

Use the GCC candidate `8945bc2b140b` against exact v38 `14ac30b34999`.
Eight new seed pairs swap colors at 180+2. The two lanes keep the same
course referee, Stockfish readiness and turn isolation as 335. The 10/16
playing threshold and irreversible futility rule are unchanged. A setup
may be replaced once only before clocks or observations are used. The
independent C++ audit checks the scored games and descendant cleanup.

The plan has 98 pins and reserves cores 0–1 and 4–5, with core 7 supervising.
Passing permits a qualified-opponent comparison. The current local build
has no arena version or ZIP.

[Frozen playing plan](../astra-submissions/analysis/deferred-prior-playing-20261111/plan.json)
· [Build receipt](../astra-submissions/analysis/deferred-prior-playing-20261111/build.json).

## Launch

Session `1880` started at 00:20:56 UTC after both mirrors verified
`0a97822c`. Both first games have active workers and owned process
registries. The compact-prior replay continues separately on cores 2–3.

[Launch verification](../astra-submissions/analysis/deferred-prior-playing-20261111/launch-verification.json).

## First two results

The candidate lost both White legs by king capture. The independent C++
validator checked all 140 frames. Both engines started native Stockfish,
and both games ended with positive clocks and no technical fault. The
swapped-color legs are running. The fixed 10/16 threshold remains in force.

[First two checks](../astra-submissions/analysis/deferred-prior-playing-20261111/first-two-verification.json).

## First two complete pairs

The candidate won both Black legs by king capture. Both seed pairs split,
giving a 2–2 score after four games. The independent validator checked all
362 frames and all clocks. Both engines used native Stockfish throughout
the validated starts. The next pair of games is running.

[Four-game verification](../astra-submissions/analysis/deferred-prior-playing-20261111/first-four-verification.json).

## Workload and six-game checkpoint

On the first four games, each engine searched 179 decisions. The candidate
visited 38.60 million nodes in 918.65 seconds and v38 visited 37.68 million
in 930.40 seconds. The candidate logged zero clock-driven thinnings and
three belief rebuilds, compared with five thinnings and zero rebuilds for
v38. The two pairs shared only seven pre-decision board and observation
histories before their moves diverged. That small matched subset had nearly
identical elapsed time and belief size. The whole-game counters are
descriptive because the engines reached different positions.

The next two Black legs split. Six games now score 3–3. All 529 frames
have independent checks, with native Stockfish and positive final clocks.
The corresponding White legs are active under the original gate.

[First-four workload](../astra-submissions/analysis/deferred-prior-playing-20261111/first-four-workload.json)
· [Six-game verification](../astra-submissions/analysis/deferred-prior-playing-20261111/six-game-verification.json).
