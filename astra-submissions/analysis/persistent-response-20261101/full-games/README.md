# Persistent-mode full-clock pilot: running

Completed head-to-head games: **5 wins, 0 draws, 1 losses** against exact v37. All 605 recorded frames passed rules validation, with no technical faults. This is an incomplete pilot, not an Elo estimate or release recommendation.

| Pair | Candidate White | Candidate Black |
|---|---|---|
| 0 | win, 86 plies | loss, 74 plies |
| 1 | win, 98 plies | win, 179 plies |
| 2 | win, 92 plies | running |
| 3 | win, 70 plies | running |

Original lane handles 11227 and 10536 continue on cores 0–1 and 6–7. Do not restart any started game. Source, model, clock and acceptance rules are unchanged.

All eight head-to-head games finish before the conditional eight Misty/control games. H2H score <=2/8 closes the configuration; otherwise Misty follows. A larger-trial review requires H2H >=4/8 and candidate Misty score at least the v37 control, with no technical faults. No ZIP is earned by this small pilot.

Plan and dependencies were published at 13e7201 before launch. `launch.json` records the original handles and process identities. `taxonomy-h2h.md` describes every completed valid planned game by policy and colour. Behaviour rates do not change the gate or establish causation. Only completed game folders are published.
