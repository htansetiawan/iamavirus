# Real-game corpus

`corpus-all.txt`: 164 seats from public arena replays, one line per seat:

```
<game_id> <side w|b> <result> <reason> <opponent> <uci moves...>
```

Only move lists are stored. Observations are rendered by the engine, whose
renderer agrees with `referee.py` on 47,875 checks, and replaying the moves also
recovers castling rights and en-passant state that a board diagram cannot carry.

Committed so the next machine does not have to re-download, and so the public API
is not hit again unnecessarily. Regenerate with `harness/corpus_download.py`.

Seats by opponent: Strongly Invisible 40, Greek Gift 40, Decent Chess Bot 31,
Knight Vision 30, TA Baseline A 14, duck 4, TA Baseline S 3, TA Baseline P 1.
These are mostly **losing** seats, so the benchmark asks "what would our engine
have done here" in positions where a strong opponent won.
