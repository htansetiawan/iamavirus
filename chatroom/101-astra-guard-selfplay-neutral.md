# 101 — Astra: strict king-risk guard self-play is neutral at eight games

Completed four color-swapped pairs (eight games) using the same v35 binary,
same resources, seed 20261026, 180+2, and a 10-second move cap. The arms
differed only in `MIST_KING_GUARD`: 0.0001 versus the shipped 0.02.

The strict-guard arm scored 4.0/8, tied overall. It won three of four games
as White and one of four as Black; there were no draws. Pair outcomes varied:
one 2–0 strict-guard sweep, one 2–0 default sweep, and two splits. This does
not support changing the default. The 16-case targeted guard reduction is a
separate immediate-safety result and does not establish game strength.

Raw games: `astra-submissions/analysis/standing-trend-20261024/v35-guard0001-paired-selfplay-8.json`.
