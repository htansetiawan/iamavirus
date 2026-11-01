# Fresh taxonomy gate, 1 November 2026

**The taxonomy now produces executable replay tests. This small first test does
not show v37 improving on v35.** It also identifies concrete positions for
diagnosing the belief/search boundary rather than changing guard thresholds
from an aggregate exposure rate.

## Frozen comparison

The sampling window is 1 November, 00:00–10:15 UTC, after the 31 October corpus
used for Fable's all-games fit. We used v35 seats against Instructors v4, duck
v6 and HYPOTHERMIA v4, including wins and losses. Of 29 validated games, 25
contribute 51 selected decisions. Cohorts are king-fatal moves, unseen queen
exposure, material loss after our next response, exchanges recovered by that
response, and controls. Selection is deterministic, with at most two examples
per opponent/color/cohort and one decision per game within each cohort.

This is deliberately stratified diagnostic sampling, not an unbiased sample of
play or an estimate of overall calibration. Multiple decisions from one game
are correlated. The frozen 1,379-decision suite is unchanged.

The original ZIPs are pinned in `run-pins.json`: v35 `24791ca64a42…`, v37
`41e02e280b61…`. Each decision ran v35, v37, and a repeated v35, in rotated order,
on cores 0–1, seed 11012026, at a 2.5-second search cap. The complete permitted
input history and recorded remaining clock were reconstructed. Previous own
moves were forced. No true board, opponent moves, or opponent views went to
the bots in these 153 policy runs.

| Diagnostic | v35 | v37 | v35 repeat |
|---|---:|---:|---:|
| Immediate king losses, all 51 decisions | 10 | 12 | 10 |
| Material loss of at least 2 in the one-exchange probe | 5 | 6 | 5 |
| Queen loss of at least 4 in the probe | 0 | 0 | 0 |
| Opponent capture with no king-safe response | 1 | 1 | 1 |
| Protocol errors / illegal moves | 0 / 0 | 0 / 0 | 0 / 0 |

There were 48 decisions with at least one truly king-safe move. Relative to
v35, v37 fixed zero and broke two on immediate king safety, and fixed zero and
broke one on the material diagnostic. The repeated v35 changed three moves
but none of these failure labels. V37 changed 14 moves. These counts do not
establish a strength regression, and do not override the arena trial.

Material scoring examines the true position after the candidate move, each
non-suicidal opponent capture, and our best safe response. It keeps the worst
net material result. It is an omniscient, limited-horizon tactical diagnostic;
it does not assume the real opponent chooses that capture. Longer combinations
and quiet replies are outside its scope. There is no replay continuation after
a changed move. The recorded material labels compare both armies at the same
frame, including our response, to avoid the earlier mid-exchange error.

## What the differences actually mean

Post-hoc follow-up used two additional policy seeds and four component arms
(old/new weights crossed with old/new history table). Print-only truth tracing
is confined to the component diagnostics, outside the policy comparison.

- **`i3xv2i71:79`, HYPOTHERMIA, Black.** `Kg6-h6` loses immediately; `Kg6-h5`
  does not. Across three policy seeds v35 loses once, v37 twice. A same-seed
  diagnostic rerun changes v37's move, so this is unstable. The new weights
  actually increase the true board's reported share from 0.113% to 0.231%.
  Both moves survive the guard; the fatal move is assigned *less* king risk
  under both models. More mass on the single true board is not a complete
  measure of action-risk quality.
- **`r82lsby1:80`, HYPOTHERMIA, White.** `b2b4` leaves the king capturable;
  `Ka2-b1` escapes. V35 escapes in all three policy seeds; v37 fails in two.
  The weights-only component reproduces the failure; the table-only component
  does not at the diagnostic seed. Both moves pass the guard. Under v37 their
  king risks are 4.98% versus 3.54% with fitted weights, 2.39% versus 1.16%
  with sharpened weights. Those differences fit inside the two-point margin.
  The true board remains present but low-ranked: 298 of 355, share 0.023%.
- **`u4mpjzah:41`, Instructors, Black.** `Rg8-h8` permits `Rh2xh8` and a
  five-point net loss; `Qd8-e7` avoids it within this horizon. The difference
  occurs in the original seed and disappears in the two additional seeds.
  Both candidate moves have zero king/queen guard risk. This is rook safety,
  not a missed queen veto. Truth is present at rank roughly 38,000 of 59,180;
  printed `0.00000` is rounding, not zero support.

The guard traces came from isolated diagnostic copies with one stderr-only
addition. `guard-audit-v35.patch`, `guard-audit-v37.patch` and `guard-traces.json`
record the patch, binary hashes and already-computed per-action probabilities.
Logging can change wall-clock search, so their moves are not added to the gate.

## Recommended next experiment, not yet implemented

These examples do not justify a new threshold. One algorithmic opportunity is
to use the larger belief scan to reduce noise in the search's estimate of
immediate terminal losses, instead of using it only for a hard veto.

For a **fixed continuation policy**, let `L` be the existing immediate-loss
utility (currently -2 at the root), `p_B(a)` the loss probability from the
larger belief scan under the actual draw weighting, and `p_S(a)` its frequency
in the sampled worlds. A control-variate action-value estimate is:

```
V_corrected(a) = V_sampled(a) + L * (p_B(a) - p_S(a))
```

The subtraction of the sampled component matters: simply adding another risk
penalty would double-count it. The guard's strided scan is itself approximate
above 20,000 boards; its weighting must match the search distribution. This
does not fix a wrongly ranked posterior, does not provide a new equilibrium
guarantee for an adaptively searched tree, and does not justify applying the
same formula to queen/material exposure, whose value depends on continuation.

Before any candidate: verify the value estimator against exact small games,
measure variance and mean over seeds, then test a frozen implementation on the
old suite and an independent fresh supplement. Implement the correction inside
root counterfactual action values, not as an unexplained post-search override.
Only a promising result earns full games. This is a proposed experiment for
Fable's review, not an implemented or promoted strength improvement.

## Validation and reproduction

`rules-audit.json`: observations and outcomes at all 2,578 frames, and legal
move sets at nonterminal frames, agree with the course referee; all 1,368
candidate immediate-loss labels at selected
decisions agree. Seven targeted harness tests cover FoW castling, en passant,
same-frame material accounting, suicidal recaptures, terminal loss and private
protocol inputs.

```
PYTHONPATH=.:astra-submissions/tools .venv/bin/python -m unittest astra-submissions/tools/test_fresh_taxonomy_gate.py -v
taskset -c 0,1 .venv/bin/python astra-submissions/tools/fresh_taxonomy_gate.py freeze --out NEW_DIRECTORY
taskset -c 0,1 .venv/bin/python astra-submissions/tools/fresh_taxonomy_gate.py run --out NEW_DIRECTORY
taskset -c 0,1 .venv/bin/python astra-submissions/tools/summarize_fresh_taxonomy.py NEW_DIRECTORY
```

Use a new output directory to preserve immutable cases and results. The default
window, versions, opponents, seed and budgets are explicit in the scripts;
future supplements should record new arguments and remain separate.
