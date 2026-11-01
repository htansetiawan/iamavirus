# Persistent learned/adversarial opponent mode

1 November 2026. Experiment214 follows the failed local-response pilots
(209:0/8;211:2/8) and213's fixed-tree continuation diagnosis. This changes the
opponent uncertainty model, not the frozen neural predictor or its confidence.

Each sampled physical board branches once into free and model-fixed modes,
with prior weights.75/.25. Our history keys and information sets are shared
across modes. Opponent keys include the latent mode, which persists through
every descendant leaf. In fixed mode the projected visible-response student
sets the entire opponent strategy; free mode is unrestricted. With fixed
strategies x and y, the finite-game objective is

`0.25*u(x, model) + 0.75*u(x, y)`.

This is the whole-strategy mixture distinction in
[Computing Robust Counter-Strategies](https://poker.cs.ualberta.ca/publications/NIPS07-rnash.pdf).
It is not guaranteed to outperform local data-biased responses: the
[DBR paper](https://proceedings.mlr.press/v5/johanson09a/johanson09a.pdf)
specifically studies model error and evidence-dependent local confidence.
The213 findings motivate this test; they do not establish the better method.

## Invariants and cost

The CFR solver, belief weights/cap, physical world draw, guards, Stockfish,
clock and root argmax are unchanged. The initial Stockfish child scores are
computed once per physical world and reused in both modes. Later trees are
distinct and can cost more; node growth by mode and peak memory are measured.
The root still purifies the highest-probability move. Therefore theoretical
claims about an equilibrium's mixed strategy are **not** claims about this
deployed action rule. Root sampling is not quietly added to the experiment.

At zero mode probability or without a model, the code falls back to ordinary
search. A missing model is a test case, not an acceptable result in the gate.
The existing `history_mix` forces its value argument's low bit on; the mode
tags consequently differ above that bit. The first implementation used adjacent
tags and merged modes. The three-ply integration fixture caught this before
any replay run. Its binary/source and failed receipt are retained. An earlier
fixture-only missing assert header is also recorded.

Validation before freeze:12 independently solved normal-form Kuhn games,
8 analytic multi-reply trap examples, and20 native runs, including off/zero
parity, endpoint probabilities, missing-model fallback and a three-ply
opponent/own/opponent propagation fixture. Optimized and ASan/UBSan pass.
These verify construction and integration, not strength.

## Frozen fresh decision comparison

Select four new v37 arena games per colour by an ID hash, excluding every game
from the frozen-tree, exact-history-response, learned-response and projected-
response panels. Selection uses no outcome. On each game, test own turns9,
17,25 and the final two own decisions, deduplicated. All games are1 November;
the frozen student's train/validation/test games end31 October. Inputs contain
only the player's permitted history and recorded clock. Ground truth and
taxonomy labels join after completion.

Four arms, rotated per position, same seed2141101 and2.5s search cap:

- Exact v37 archive.
- Unchanged local projected-response211 binary, confidence.25 (negative control).
- New binary with response confidence0 (control for implementation/timing).
- New persistent-mode binary, model prior.25 and projection enabled.

One sequential process at a time on cores0–1. CPU and peak RSS are captured
with `/usr/bin/time`. No observation timeout is treated as a completed game;
any diagnostic error stops the run, and no completed/failed call is silently
repeated. Source, binary/model/input hashes and this gate are published first.

Candidate must satisfy every condition before any full-game plan:

1. No protocol/legality/model/key errors; prior and doubled root branches must
   match the construction. Projection must actually be used.
2. No more immediate king or >=4-point net queen losses than either exact-v37
   or confidence0 control. No more than one additional >=2-point short exchange
   loss beyond the worse of those two controls. The local negative control
   is reported but does not set the safety threshold.
3. At least3 changed choices versus confidence0, exceeding its difference from
   exact v37 by at least2. This is only a crude timing-noise check.
4. First restricted-reply reach >=.125 on at least75% of applicable cases:
   that is half the.25 model-mode prior, not half the entire game. Root-only
   trees with no expansion are recorded and excluded from this reach metric.
5. Median neural-query time <=.25s, median total nodes >=60% of exact v37,
   and every process's peak RSS <3,500,000KiB. Raw node count does not by itself
   demonstrate equivalent depth or useful coverage in each mode.

Passing earns manual review of changed choices and a separately frozen small
full-clock trial. It does not earn a ZIP or an Elo claim. Short material labels
do not prove optimal moves; repeated exchange/quiet-tactic limitations remain.
Failure stops this configuration without confidence tuning against the panel.
