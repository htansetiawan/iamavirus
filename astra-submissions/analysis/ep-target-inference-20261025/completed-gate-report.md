# EP-history gate closed: no strength-based promotion

Astra, 26 October 2026. The existing 20-pair, 180+2 run completed at its
original 40-game cap. No additional games were started for this review.

| Candidate seat | Wins | Draws | Losses | Score |
|---|---:|---:|---:|---:|
| White | 10 | 3 | 7 | 57.5% |
| Black | 8 | 0 | 12 | 40% |
| Both | 18 | 3 | 19 | 48.75% |

The whole-pair bootstrap 95% interval is **37.5–60%** (20,000 resamples,
seed 20261026). This is a small local comparison with v35, not an arena Elo
estimate or proof of equivalence. It provides no positive promotion evidence.

The independent referee reproduced all **3,374 frames**, including both
observations and terminal results. All replay hashes, executable/referee
hashes, pair/colour coverage, and candidate/opponent seeds match the manifest.
See [audit output](completed-gate-audit.json) and
[reproducible auditor](audit_completed_gate.py).

The candidate selected **zero en-passant moves**. The audit separately lists
candidate-turn legal en-passant opportunities, excluding terminal frames.
Those opportunities are not all necessarily newly recovered by the patch.
This match result therefore does not measure successful exploitation of the
recovered action or show that EP omission caused the previous arena losses.

The earlier rules and action-coverage evidence remains valid. The patch can
be considered as a separately verified correctness change in a later candidate;
do not advertise this run as an Elo improvement or start another gate to seek
a favourable score. The old cores 4–5 reservation is released after verifying
the runner is no longer present.
