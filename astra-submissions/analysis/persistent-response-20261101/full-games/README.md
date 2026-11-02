# Persistent-mode pilot: complete, eligible for confirmation

**7 wins, 0 draws, 1 loss against exact v37**, across all eight planned 180+2 games. Candidate White: 4–0; candidate Black: 3–1. All 761 frames passed rules validation. No illegal move, protocol failure, timeout or other recorded technical fault. This is a small pilot, not proof of a true 87.5% win rate or arena Elo gain.

| Pair | Candidate White | Candidate Black |
|---|---|---|
| 0 | win, 86 plies | loss, 74 plies |
| 1 | win, 98 plies | win, 179 plies |
| 2 | win, 92 plies | win, 83 plies |
| 3 | win, 70 plies | win, 71 plies |

Both original handles (11227, 10536) exited 0. The host audit verifies both lane parents, all eight workers and all 16 bot groups are gone; see `h2h-terminal.json`. No game was repeated. Binary/model/clock/seed rules match the published plan.

The unchanged gate advances to eight Misty games: four candidate and four exact-v37 controls, matched by colour and seed, on cores 0–1 and 6–7. A larger-trial review requires candidate score at least the v37 control with no technical faults. Misty is the authentic local engine, not verified current arena bytes. This pilot alone earns no ZIP.

Source and immutable plan were published at 13e7201 before the first game. `taxonomy-h2h.md` and JSON describe every completed valid game; per-colour behaviour rates do not establish causation. The separate eight-decision queen screen is diagnostic and does not alter this match gate.

## Conditional Misty result

All eight original games completed without technical faults: **candidate 3W–1L, exact-v37 control 3W–1L**. Both policies won their two White games except the pair-1 v37 control; the candidate lost its pair-0 Black game and the controls won both Black games. Thus their equal totals conceal different paired outcomes, not identical play.

| Pair | Candidate White | v37 White | Candidate Black | v37 Black |
|---|---|---|---|---|
| 0 | win, 66 plies | win, 50 plies | loss, 50 plies | win, 49 plies |
| 1 | win, 66 plies | loss, 57 plies | win, 101 plies | win, 97 plies |

All 544 Misty-phase frames passed validation. Original handles 2093 and 20926 exited 0; the host confirms both parents, all eight workers and 16 bot groups are gone (`misty-terminal.json`). No games were repeated. The frozen pilot gate passes. The next experiment is an independently frozen 80-game confirmation, not a ZIP or arena Elo claim: `../../persistent-confirmation-20261102/plan.json`.
