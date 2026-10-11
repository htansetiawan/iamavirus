# Clock-controlled M4 baseline

**Initial result: 1 win, 1 loss against frozen Fable mist-c v8.** Two planned
seed12 games remain unplayed. The batch stopped for review after each recorded
fault; neither result was discarded or replayed. These two games are not an
Elo estimate, and the win included a fallback out of M4.

| Seat | Result | Plies | Finding |
| --- | --- | ---: | --- |
| seed11 White | loss | 71 | Rb3–b8 exposes Ka2 to hidden Qd5. The first search diagnostic was lost to a16KiB rolling stderr tail. |
| seed11 Black | win | 83 | At ply17,7041 carried current roots exhausted setup with6050 Stockfish calls; visible-board fallback played c6b4. |

All72 White-game frames/moves/observations were independently checked against
the course referee. See `first-game-audit.json`. The engine had~91seconds
remaining at its loss; this was tactical, not a time forfeit.

Original baseline: `baseline-plan.json` and `baseline-manifest.json`.
Both games use candidate SHA7149ebd0… from C commit567c3df,180+2,32 fresh root
samples,max10seconds allocation,scale1 and no tactical closure/witnesses.
Carried roots can greatly exceed the fresh sample target.

The first receipt and game are immutable evidence of incomplete diagnostic
coverage. `continuation-plan.json` excludes that already played seat from a
new run using the same engine/referee bytes. Only diagnostic retention changes:
the existing1MiB stderr warning budget is retained in full, rather than16KiB;
total-output and line-limit warning rules remain unchanged. Behavioral tests
are recorded in `capture-correctness.json`. The continuation's first match
produces all41 M4 records and exposes the genuine search failure above.

`first-game.json`, `second-game.json` and their original receipts retain the
actual results, private engine stderr, protocol and clock traces. These
locally generated completed games can be used for offline analysis. Do not
signal processes from historical registries embedded in these artifacts.

Next engine work is documented in C `docs/M4_ROOT_SETUP.md`: capacity preflight
plus opt-in cheap initialization of carried frontier roots. Separate paired
searched-prefix checks are in the sibling `m4-root-setup-20261011` directory.
These results do not justify a release archive or arena upload.
