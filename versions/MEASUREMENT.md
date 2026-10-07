# Measurement

How changes are evaluated here, what each instrument can resolve, and the
mistakes that made this document necessary.

## The mistake this is a response to

Three consecutive changes were measured by self-play A/B over 48–60 games:

| change | result | what was concluded at the time |
|---|---|---|
| belief consistency (v3) | 0.479 ± 0.072 | "self-play is blind to symmetric flaws" |
| material risk term | 0.433 ± 0.064 | "mildly harmful" |
| king safety (v4) | 0.573 ± 0.069 | "first positive result" |

Every one is about 1σ. At 48–60 games the resolution is roughly **±90 Elo**, so
none of them supported a direction, and a story was supplied for each anyway. A
fourth attempt then compared three king-safety configurations that turned out to
be statistically indistinguishable (9.09%, 10.05%, 8.61% against ±2%).

The lesson is not "measure more." It is that **the scale of the experiment has to
match the size of the effect being sought**, and at Elo 1468 against leaders near
2100 the effects worth chasing are large:

| edge | games to detect at 2σ |
|---|---|
| +15 Elo | ~2,100 |
| +50 Elo | ~195 |
| **+100 Elo** | **~50** |
| +200 Elo | ~14 |

Tuning constants at ±15 Elo was the wrong activity for this position in the field.

## Instruments

### 1. Offline benchmark against real arena games — `tools/benchmark_corpus.cc`

The most useful of the three. It replays real games from the public API: rebuild
the truth from the recorded moves, render the observations the seated player
actually received, drive the belief through them, ask the engine what it would
play, and check **against the true board** whether that move leaves our king
capturable. The engine's answer is discarded and the real move played, so the
position stays on the rails of the real game.

- Thousands of labelled decisions from opponents several hundred Elo stronger.
- No opponent executable, no self-play, no Elo inference.
- Current corpus: 164 seats, 14,064 plies, ~7,000 decisions across Greek Gift,
  Strongly Invisible, Decent Chess Bot, Knight Vision and the TA baselines.
- Resolution: 209 decisions gives ±2%; ~3,200 gives ±0.5%.

**Limit:** a low king-blunder rate is necessary, not sufficient. It says the bot
stops throwing games away, not that it plays well. Elo still needs games.

### 2. Sequential A/B — `harness/sprt.py`

Node-limited, so a result does not depend on machine load, and sequential, so it
stops as soon as the evidence justifies a decision between two explicit
hypotheses with bounded error rates. This replaces reading a direction out of a
fixed batch.

### 3. Harness self-test — `harness/selftest.py`

Plays a configuration **against itself**, where the answer is known: it must score
0.500. This was never run for the first four versions. When finally run it
returned 0.562 (within 1σ, no detectable bias) and showed 32/32 games distinct,
which **refuted** a standing suspicion that duplicate games were inflating
confidence.

## Why node limits matter

The engine is time-limited, so its strength changes with CPU contention. That made
the number of parallel workers a hidden variable in every A/B, and running more
games to reduce noise introduced a different bias instead. `FOW_NODE_BUDGET`
bounds a decision by nodes with the clock demoted to a safety net.

Verified: identical node count and identical move across runs, and ~20× faster
than the 4-second budget. Every core can now be used without distorting anything.

## Rules conformance

Any engine change is re-checked against `referee.py`, the arena's own rules, via
`tools/conformance_main.cc` and `tests/conformance_test.py`: move generation,
perft, both sides' observations, exact legal moves from an observation, and en
passant inference. Current status **47,875 / 47,875**.

One caveat found the hard way: the en-passant *helper* passed 100% of these checks
while the engine *integration* was broken, costing a legal move. Testing a
component is not testing its caller.

## Practices adopted

- Write the regression test **before** the fix, and confirm it reproduces the bug.
- Sweep seeds and population sizes. A single-seed regression test passed by luck
  for a fix that was a coin flip (7/15).
- Report malformed configuration loudly. A silently swallowed environment value
  once disguised a broken harness as a bot that could not win a game.
- State the resolution alongside the number, and call an inconclusive result
  inconclusive.
