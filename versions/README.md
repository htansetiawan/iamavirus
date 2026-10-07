# Versions

One file per submitted version: what went in, what was tried, and what the
measurements actually said. Negative and inconclusive results are recorded here
deliberately — most of what was tried did not work, and that is the useful part
of the record.

| version | commit | headline change | local measurement | arena |
|---|---|---|---|---|
| [v1](v1-python.md) | — | Python alpha-beta, ghost belief | 0.875 vs `baseline.py` (24 games) | not submitted |
| [v2](v2-cpp.md) | `450f11a` | C++ rewrite: magic bitboards, particle filter, regret matching | 10W–0L vs `baseline.py` at 180+2 | Elo ~1468 |
| [v3](v3-belief-consistency.md) | `351ca0b` | own pieces as an exact belief constraint; full-population material risk | 0.479 ± 0.072 vs v2 (~−14 Elo) | 1W–4L observed |
| [v4](v4-king-safety.md) | `5e0ef63` | king safety over the whole population, before shortlisting | 0.573 ± 0.069 vs v3 (~+51 Elo, 1.1σ) | submitted |
| [v5](v5-opponent-prior.md) | candidate | plausibility prior over opponent moves; node-limited search; ablation knobs | trap declined 13/15 vs 3/15; aggregate unmoved | not submitted |

## The honest summary

**Proven:** the C++ rewrite (44 k → 11 M nodes/sec, depth 6 → 12), exact rules
conformance (47,875/47,875 differential checks against `referee.py`), and two
correctness bugs in the belief filter found by tests written before the fix.

**Not proven:** every strategic heuristic. Six were added across v2–v5 with
nineteen hand-picked constants. Not one has been shown to improve playing
strength at a resolution the measurement could support. Two measured negative
and were removed or rewritten.

**The binding constraint for most of this work was measurement, not ideas.**
Three consecutive changes measured +33, −47 and +51 Elo, all at about one sigma,
and a direction was read into each of them. See [MEASUREMENT.md](MEASUREMENT.md).

## Arena standing at the time of writing

Elo 1468 over 33 games (12W–21L). The leaders sit near 2100, so the gap is about
650 Elo. That number matters for how experiments are designed: detecting +15 Elo
needs roughly 2,100 games, while +100 Elo needs about 50. Tuning constants at
±15 was the wrong scale for this position in the field.

## Failure families, not individual bugs

Five rated losses share one cause: the king moving onto, or capturing on, a
square covered from beyond the fog.

| game | opponent | bait | hidden defender |
|---|---|---|---|
| `qp6mfacx` | Greek Gift | `Bf7` | `Ne5` |
| `z6mbi981` | Greek Gift | `Qe1` | `Re8` |
| `cxgvxx6h` | TA Baseline A | `f2` | queen b6 |
| `rz89dmpy` | TA Baseline A | — | queen a8 |
| `92of99z7` | TA Baseline S | `Ra5` after taking our pawn | rook a5 |

Greek Gift, the top-rated team, used it twice in both colours. Treating these as
five bugs would mean five patches; treating them as one failure family is what
led to the belief-level fix in v5.
