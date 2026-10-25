# King-guard candidate: fixed 20-pair result

**Decision: do not promote `iamavirus-v36-kingguard0001.zip`.** The fixed run
finished 16 wins, no draws and 24 losses against unchanged v35. This supersedes
the earlier optional-arena-trial recommendation. Preserve the archive and
results for reproducibility; no further guard-threshold sweep is proposed.

## Completed comparison

The only candidate source change lowers the default `MIST_KING_GUARD` tolerance
from 0.02 to 0.0001. This tightens the allowed excess estimated king risk when
screening root actions. It does not improve the belief posterior or train a
model. Both engines used the 180+2 clock with the existing 10-second move cap.

The 20 color-swapped pairs used fixed bot-specific seeds beginning at 20261042.
The run completed on October 25, 2026, at 15:33 America/New_York. Its process
exited successfully at the original 40-game cap. No games were added or removed
after observing the result; the earlier 16 exploratory games are not pooled.

| Candidate seat | Wins | Draws | Losses | Score |
|---|---:|---:|---:|---:|
| White | 7 | 0 | 13 | 35% |
| Black | 9 | 0 | 11 | 45% |
| Both | 16 | 0 | 24 | 40% |

All 40 ended with `King capturable`; there were no clock or protocol forfeits.
Median length was 77 plies. Summed match wall time was 17,639 seconds (4.90 hours).
This is a local head-to-head screen, not an arena Elo estimate or evidence about
performance against duck, instructors, or the top six separately.

For pair j, let X_j be the mean of its two candidate game scores. The reported
score is mean(X_j), and the bootstrap resamples the **20 pairs**, not 40
independent seats. The 20,000-resample percentile interval is **[25%, 57.5%]**.
This approximate interval includes 50%; the small run does not establish a
precise strength disadvantage. It supplies no positive basis for promotion.

The earlier selected replay improvement (83 to 61 fatal choices in 91 target
positions) remains a valid narrow measurement. It did not establish stronger
full-game play. This result does not isolate the cause of the disappointing
score, and does not justify attributing all 24 losses to the changed threshold.

## Integrity and reproducibility

The [audit](guard0001-fixed-20pairs-audit.json) verifies all 40 replay hashes,
pair/color coverage, fixed seeds, current executable/referee hashes, and the
recorded outcomes. Replaying all **3,348 frames** reproduces every board and
both observations, with no moves after a board terminal state. All terminal
results and reasons match the referee. This uses the same referee that ran the
matches; it is an integrity audit, not a second independent rules implementation.

- [Completed manifest](v35-guard0001-fullclock-extra-20pairs-seed20261042.json)
- [Candidate source and immutable archive provenance](../../v36-kingguard0001.md)
- [Audit program](../../tools/summarize_completed_pair_gate.py)

```sh
taskset -c 0,1 /home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/summarize_completed_pair_gate.py \
  --manifest astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-fullclock-extra-20pairs-seed20261042.json \
  --referee-dir /home/henrytan/git/fow-starter \
  --output /tmp/guard0001-fixed-20pairs-audit.json
```

The completed lane releases cores 6–7. The separate EP-history test continues
at its existing cap. The reviewed learning proposal remains pending; this
negative result does not authorize a new training run or another tournament.
