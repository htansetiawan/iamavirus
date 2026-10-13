# How we measure

*Every claim about an engine change is backed by one of three instruments: the regression suite, the local bench, or a schedule-adjusted arena checkpoint. This page says what each one is, what it can and cannot tell us, and the rules we hold ourselves to.*

[TOC]

## 1. The regression suite

A fixed set of **1,379 recorded decisions** from our own arena losses, each replayed with the engine's exact inputs (every view and clock up to that decision, our earlier moves forced) so the engine faces precisely the position it faced in the arena. Each decision is labelled with one or more kinds:

| kind | meaning |
| --- | --- |
| `check` | our king was attacked by a piece we could not see |
| `fatal` | the move we played left our king capturable on the true board |
| `material` | the next two plies cost us three or more points of material |

The decisions are built from our arena losses by `tools/suite_build.py` and replayed by `tools/suite_run.py`, both in the mist-c repository (the hybrid era's equivalents were `fatal_corpus.py` and `gym_replay.py` in `learning/`). The runner reports, per kind, how often the engine repeats the losing move, how often its new move is fatal, the centipawn loss of its move against Stockfish on the true board, and, with `--truth`, the true board's weight share and rank inside the belief. Two runs are compared decision by decision (`compare.py`), as *fixed* (was fatal, now safe) and *broke* (was safe, now fatal). The noise floor between identical runs is about five flips each way, so a change has to fix at least ten more than it breaks to count.

The suite is where belief and guard ideas are tried first: a run takes about an hour on three workers and gives a decision-level explanation of every change, not just a score.

## 2. The local bench

Paired games on the course referee between two engine builds, pinned to two cores with `taskset` at the arena time control (180 s + 2 s), both colours, seeded openings. The harness (`learning.arena_local`) logs every game with clocks and a replay, and a watcher alarms on time forfeits, crashes and illegal moves.

The bench answers two questions the suite cannot: does the change survive a full game against a different engine, and does it hold the clock. Our rule before any upload: **no forfeit, no crash, the lowest clock above 20 s, and the shortest loss not shorter than the previous version's**. Typical sizes are 40 games per pairing; 120 games were played before v34 against the v33 bytes, against v10 and against Misty.

The bench cannot rank versions finely. Forty games resolve a 15-point gap at best, and local opponents are not arena opponents.

## 3. Schedule-adjusted arena checkpoints

The arena pairs us against whoever is online, so a raw score over 20 games says more about the schedule than the engine. Every 20 games we compute what a reference version **would have scored against the same opponents** from its own per-opponent record, and report the difference with a binomial margin and a z value. The references are v25 (our last Python-era bot, with the longest record) and v30 (the Misty-based bot). A direct comparison with the previous version on the current version's schedule is added once there are enough games.

The report groups opponents: the **top six** of the leaderboard, Mist Opportunities (the Obscuro-based bot we treat separately), the TA baselines, and the rest. The top-six rate is the number that decides rank, and it moves slowest.

Two rules go with every upload and are written down **before the first arena game**:

- a **prediction**: what the version should score overall and against the top six, which failure modes should disappear, and what would count as the change not working;
- a **fail-fast rule**: the conditions under which the previous version is reactivated at the 20-game check, usually any forfeit or crash, or a score more than 0.15 a game below the previous version schedule-adjusted.

Predictions that break are recorded as broken, with the game that broke them.

## 4. The data pipeline

- `learning.ingest` pulls our games and the leaderboard snapshot from the arena every 20 minutes into `data/raw/` (replays with both players' views and the true board at every ply).
- `learning.arena_watch` and `learning.top6_report` regenerate the active version's watch report and the top-six report, committed to `data/reports/`.
- The suite builder turns new losses against the top opponents into suite decisions.
- Opponent replicas (`releases/replica-*`), behaviour-cloned from each bot's arena games, let the bench play against approximations of specific arena bots; the duck replica is known not to be faithful.
- Core reservations for benches are recorded in `chatroom/cores.json` so two agents never share a core pair during a timed run.

## 5. Rules we keep

- Test both colours. Several losses have been colour-specific.
- Compare throughput changes only as paired A/B runs at the same time; turbo and contention move absolute numbers by 30%.
- Never rewrite the games log while a bench runs; never gate a queued job on a process-name pattern that matches the job itself.
- The team token never enters source or a zip; the course starter kit is never vendored.
- Discuss a technique before testing it at random; record negative results with the same care as positive ones.
