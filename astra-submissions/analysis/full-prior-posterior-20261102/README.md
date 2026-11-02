# Full-prior posterior and runtime gate

Astra, 2 November. The taxonomy audit rejected the neural predictor as a blanket belief prior, especially on surprise captures. The 225 implementation makes the existing full tactical prior cheaper than the old cheap path on three fixed large states. This is the next question: does that saving translate into better hidden-board probabilities over entire observation histories?

The frozen panel contains 24 IAmAVirus games completed on 1 November before 20:00 UTC: four each against Instructors, duck, HYPOTHERMIA, Greek Gift, Knight Vision and Strongly Invisible. Selection uses a fixed salted ID hash, not outcomes; it excludes the 25 fresh-taxonomy games and the 222 games in experiment 224. There is no claim that every selected game was previously unseen by the project. The course referee validates all 2,627 frames before selection is frozen.

Three arms retain the exact v37 coefficients, history table, temperature 2, cap 200,000 and two threads: original ordinary cutoff; optimized ordinary cutoff; optimized full features at all belief sizes. No clock thinning, search or recovery after collapse. Truth is labelled only after each update and never inserts or weights a world. Exact ordinary-control fingerprints must match on every step, and no pre-cap truth-support loss is accepted.

The primary comparison covers our decision frames after own move eight. It requires nondeclining truth support, at least 0.15 nats mean truth-log-share improvement, a whole-game stratified bootstrap 95% lower bound above zero, at least six games in the large-belief regime, total update time at most 1.2 times original ordinary and p95 time at most max(0.1 second, 1.5 times original p95). Missing truth counts as zero share with a predeclared floor and sensitivity report. Passing only permits designing a real-clock decision test, not a ZIP.

Preparation handle 73164 exited 0. All three six-ply fixtures retain truth; original and optimized ordinary fingerprints agree. Plan SHA: `6ab528c4f83c4c929a672525ad1398da232627353f3c9db1340a5899b5f1ad9c`. Source and plan will be published before the first of 72 calls. One attempt per game/arm, rotating order, cores 2–3, 120 seconds and 3 GiB per child, 45-minute total limit, no GPU. Technical or parity failures stop and retain evidence; no retries.

This experiment is independent of the 219 match batch, now closed after a Misty control timeout. No live engine, guard threshold or Fable source is modified.

Source: `astra-submissions/experiments/full-prior-posterior-20261102/`. Evidence: `astra-submissions/analysis/full-prior-posterior-20261102/`.

## Result: exact speed improvement; full-prior setting below the advance threshold

All 72 first attempts complete, original handle 88398 exit 0. The independent aggregation verifies all 7,737 update rows and output hashes, exact ordinary-control fingerprints throughout, unchanged dependencies, and no pre-cap truth loss. All owned processes are gone; cores 2–3 are released. No recovery or search was part of these runs.

| Measure | Original ordinary | Optimized ordinary | Optimized full |
|---|---:|---:|---:|
| Total update seconds, 24 games | 119.818 | 60.337 | 78.048 |
| 95th percentile update seconds | 0.13400 | 0.05154 | 0.06687 |
| Maximum update seconds | 1.76487 | 0.94218 | 1.28786 |
| Truth present, 1,111 primary decisions | 1,087 | 1,087 | 1,089 |
| Mean truth negative log share | 6.04674 | 6.04674 | 5.92107 |

Full scoring improves mean log share by **0.12568 nats**, with whole-game stratified bootstrap 95% interval **[0.01972, 0.28422]**. Sixteen games exercise the large-belief regime. It passes the support, confidence-interval and runtime conditions but misses the predeclared minimum gain of **0.15 nats**. Thus the frozen decision is `close_full_prior_configuration`: no automatic timed-decision trial or ZIP follows. This is a positive posterior result below our advance threshold, not evidence of no effect.

The four-game-per-team slices are descriptive: Instructors +0.19796, duck −0.08712, HYPOTHERMIA +0.07960, Greek Gift +0.04606, Knight Vision −0.00060 and Strongly Invisible +0.57362 nats. They are too small for opponent-specific tuning; especially do not hide the duck regression or fit to these cases. The floor-sensitivity gains are +0.10996 / +0.12568 / +0.13811 at 1e-9 / 1e-12 / 1e-15.

What remains useful independently is the **1.986× faster ordinary update with identical output**, without changing weights or thresholds. Full scoring is also about 35% cheaper than original ordinary in this panel. These timings cover the belief updater, not whole-move or match speed; real-clock thinning/search can change decisions. Fable can review the isolated 225 performance implementation separately from the unpromoted full-prior setting. Do not claim an Elo gain or silently merge a full-model switch.

Next review should separate the proven computation saving from posterior-policy choices. Preserve this panel as an evaluated development set; no additional games or modified thresholds are appended to rescue its result. The learning-loop documentation now records this distinction.
