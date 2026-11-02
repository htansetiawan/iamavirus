# Weighted opponent histories: implemented, predictive benefit unproven

Experiment 250 completed 24 first-attempt replay prefixes, 12 per colour,
in **12.58 seconds** on CPU0–1. The original collection handle 90290 exited
0. No GPU, model fitting, search, new games or arena ZIP was involved.

This is the full-history/hash representation question already raised in
notes 162/163, not a new discovery. It differs from experiment 201 by retaining
full rolling opponent observation/action hashes and applying the immutable
v37 empirical history table independently to each weighted history. Boards
are stored once; histories occupy contiguous 16-byte entries. Static move
features and successor observations are shared within a physical parent.

## Comparison and result

All three filters use the same permitted observations and own moves. The two
modified filters group by position hash **and halfmove clock**; their direct
comparison isolates retaining history masses. Original v37 omits the clock.
All filters omit repetition history. The common prefix stops before exceeding
4,096 states or 131,072 histories; 22 games stopped at a state/history limit,
and two reached the requested prefix end. No filtering run was repeated.

| Filter | Board marginal NLL, equal game weighting | CPU seconds through retained prefixes |
|---|---:|---:|
| Original v37 | 2.07236 | 1.2556 |
| New grouping, one representative history | 2.06934 | 1.5246 |
| New grouping, all history masses | 2.05882 | 1.7103 |

The history-mixture gain over its matched control is **0.01052 nats**, with a
descriptive game-bootstrap 95% interval **−0.02948 to +0.05369**. Nine games
improve, eleven worsen, and four differ by less than 1e-6 nats. Removing the
initial position gives 0.00977 nats; the subset after ply 20 is slightly worse
than the matched control. These are reused development prefixes, not a
predeclared playing-strength gate or independent population confirmation.

All 260 evaluated decisions retain nonzero truth **board/rule-state marginal**
support. Original v37 loses matching halfmove-clock support on some states;
the two clock-aware filters do not. This is not evidence about capped
middlegames or the mass of the exact true opponent history.

## What the representation changes

- Multiple histories occupy the same state at **201/260** decisions.
- Retention changes board probabilities by total variation above 1e-6 at
  **79/260** decisions. Mean total variation is 0.01783; maximum is 0.40675.
- Probability mass outside each state's heaviest history averages **10.8%**
  with equal game weighting and reaches 90.5% in one decision. This describes
  history mass reassigned by a representative approximation, not lost board
  probability or a measured strength deficit.
- One state carries **1,664** distinct history hashes. The largest mean
  histories per state at a decision is 152.8. State-array memory tops out at
  **1,450,784 bytes** in saved mixture snapshots. This excludes transient
  candidates, shared libraries, and process RSS.
- The mixture makes 314,568 empirical-table lookups and has 2,955 qualifying
  hits over retained prefixes; the matched control makes 30,986 lookups and
  has 2,172 hits. These are raw operations, not probability-weighted coverage.
- Retained-prefix filter CPU is **12.2% higher** than the matched control and
  36.2% higher than original v37. Including the final rejected update gives
  3.6135 / 2.7749 / 2.3282 seconds respectively. This unoptimized, fixed-order
  diagnostic does not establish production throughput or total-move cost.

Post-hoc attribution finds the largest distribution change in `u0oy4mzr`,
ply 10: truth log probability **falls** by 0.7630 nats. In `t8v0f24c`, ply 11,
it rises by 0.5096. Preserving histories is not automatically a better
empirical prior. All per-game effects are kept in `case-effects.json`.

## Correctness and limits

The independent course referee verifies **2,378 replay frames**. A separate
Python implementation of the native state hash reproduces truth joins;
**302,779 saved marginal rows**, normalizations, source hashes, and permitted
input reconstruction pass the audit. No true board, opponent move or result
was passed to a filtering child. Raw unlabelled outputs are retained.

Before collection, code review found that the new filter and its first oracle
both omitted the existing own-move king-survival deduction. That was repaired
and directly compared with v37 for both colours; all pre-review receipts and
the unchanged selected IDs remain available. Corrected native enumeration
tests pass 48 comparisons, with table on/off and two temperatures. Host
ASan/UBSan/LSan passes; sandbox ptrace failures remain recorded. Table-disabled
process checks match original v37 board probabilities within 1.51e-8.

`audit.json` is a replay/metric audit; it does not independently enumerate all
histories in these 24 games. The small-state native oracle covers that logic.
Hash collisions, omitted repetition history and bounded early-prefix coverage
remain explicit limitations. The stopped-update receipt does not distinguish
which of the state/history bounds fired.

## Decision for Fable and the human review

**Do not turn this representation on by default or claim a stronger bot.** The
implementation establishes that representative histories affect predictions,
but does not establish that retaining all of them is worth its cost. It is a
reusable native building block and diagnostic, not a release candidate.

The search question remains separate: v37 seeds opponent information sets
from a sampled board's representative history (`gtcfr.c`). This experiment
does not measure whether preserving that partition changes useful actions.
Any proposed search test must hold sampled physical worlds and the compute
budget fixed, record the changed information-set partition, then earn
decision and full-game evidence. A small posterior gain alone is not a
reason to launch that integration or repeat the same fit.

Prepared source/contract commit: `bebfdfb2fcb3b19b37202a0462fd251e5f7f4113`,
verified on both repository mirrors before collection. The source and plan
remain pinned; no production source, guard threshold or version changed.
