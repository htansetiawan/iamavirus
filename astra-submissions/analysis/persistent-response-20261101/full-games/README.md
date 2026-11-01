# Persistent-mode full-clock pilot: running

1 November 2026. First two completed games: **2 wins, 0 draws, 0 losses**,
both as White versus exact v37. The two original lane handles 11227 and10536
continue the remaining six head-to-head games on cores0–1 and6–7. Do not
restart any started game. No faults in the completed games; all186 frames
validated against the independent rules implementation.

| Pair | Candidate White | Candidate Black |
|---|---|---|
| 0 | win,86 plies | running |
| 1 | win,98 plies | running |
| 2 | pending | pending |
| 3 | pending | pending |

This is an incomplete pilot, not an Elo estimate or release recommendation.
The unchanged plan requires all eight head-to-head games before deciding on
the conditional eight Misty/control games. H2H <=2/8 closes the configuration;
otherwise Misty follows. A larger-trial review requires H2H >=4/8 and no worse
candidate than control against Misty, with no faults. No ZIP is earned here.

The immutable plan and dependencies were published at13e7201 before launch.
`launch.json` records the original handles and host process identities. Only
completed game folders are published during the run; the source, model and
rules are unchanged. No GPU use.
