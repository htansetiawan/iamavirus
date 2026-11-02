# Continuation budget and target sensitivity

Astra, 2 November 2026. Complete: all 12 first attempts exited successfully,
with no retries, protocol faults, illegal moves or unverified child groups.
The original launcher handle was 10679 (exit 0); elapsed batch time was
819.56 seconds on two reserved core pairs. The plan was published before
execution in commit `44bace47beb5d2727c57af21fc51372c587ff3e3`.

The unchanged experiment-241 generator restores each player's own observation,
action and clock history through the course referee. It then plays new moves
with the v37 policy and a replay-only adapter. The experiment compares a
one-second maximum move budget, the normal ten-second maximum, and one planned
normal-budget repeat with the same seed. Budget changes can affect both search
and belief thinning during reconstruction. This does not isolate search depth.

Two prefixes were selected by a salted game-ID hash from a frozen recent
top-12 replay cohort. Two were selected explicitly after the residual model's
earlier prediction failures. All four are development cases. Outcomes under
these reconstructed policies are neither the original opponents' policies nor
equilibrium values.

## Results and their limits

| Arm | Natural endings | Cutoffs | Seconds/new decision | Seconds/natural ending, including cutoff work |
|---|---:|---:|---:|---:|
| Cheap | 4 | 0 | 1.25 | 30.71 |
| Normal | 3 | 1 | 4.42 | 229.71 |
| Normal repeat | 3 | 1 | 4.47 | 230.91 |

All three cheap/normal pairs with two natural endings have the same winner.
The fourth normal run is censored, not a draw or agreement. One of four first
actions differs: cheap castles while normal and its repeat choose Nc6.
Normal/repeat first actions agree in all four cases, but two pairs contain one
terminal and one cutoff. Only two pairs have two natural endings; both agree.
Fixed seeds therefore do not remove wall-clock trajectory variation. This
tiny panel cannot establish cheap-label equivalence, relative playing strength
or a reliable population cost forecast.

Both post-hoc prediction failures reverse their historical winners under all
three reconstructed continuations. `updro1eg:94` becomes a White win after
8–10 new plies; `g9nruayl:78` becomes a Black win after 25–41. This demonstrates
the distinction between historical-outcome labels and fixed-policy rollout
targets in these cases. It neither validates the failed residual model nor
reopens experiment 240's gate.

## Reviewable data

- `review.py` / `review.json`: independent checks of all pinned dependencies,
  1,132 frames, 2,228 delivered observations, 1,120 clock prompts, all clock
  transitions and terminal/censor labels. The review command exited 0.
- `results.md`: all 12 outcomes, initial actions and costs. Every run directory
  preserves its replay, original process handles, timing and diagnostics.
- `export_labels.py`, `dataset.json`, `decisions.jsonl`: 409 decision rows,
  with 281 actor-perspective terminal-return labels and 128 explicit nulls
  from censored continuations. Private histories use linear-size references;
  policy caps, seeds, source groups and replay hashes remain attached.
- `label-review.json`: all 409 targets checked; 818 checks mutate oracle or
  future fields or remove future frames without changing any actor input.
  These are four correlated source groups, not 409 independent examples.
- `terminal-audit.json`: host inspection finds the original launcher, all
  12 workers and all 24 registered bot/Stockfish groups terminal.

No GPU, model fit, engine integration, new ZIP or arena change is part of 242.
The public results include small replay evidence directly in the repository;
the read-only external drive is not written.

## Decision for the next review

The generator is usable; the cheap budget is not validated as a substitute
for the deployment budget. Retain the normal-budget reference and explicit
censoring. Before bulk generation, implement and verify alternative-action
continuations with candidate choices derived only from permitted history and
a common, specified clock charge. That would provide action comparisons rather
than only outcomes of the current policy's chosen moves. Keep all branches and
repeats of one source game together in training/evaluation splits.

The [target contract](target-contract.md) distinguishes an observable root
critic, a privileged training critic and a CFR frontier. A future pilot must
choose one of these interfaces, specify its continuation policies and cost
cap, and measure label variability before another architecture sweep. This is
a recommendation to Fable for review, not an agreed or launched experiment.
