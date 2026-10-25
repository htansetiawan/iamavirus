# 103 — Astra: recent hidden-only prior improves the targeted fatal-choice replay

2026-10-25. The recent opponent corpus fit and exact replay gates are now
separated from the earlier 100-game pilot. No submission source or ZIP changed.

## Recent fit, frozen held-out games

The 5,940-game Oct 18–24 sample yielded 59,195 opponent decisions; the
chronological game-disjoint test has 11,931 decisions from Oct 23–24. The
full 28-feature refit improves broad held-out predictive metrics, but its
full+cheap research binary (SHA-256
`80328117723499564954a83ceb6c8e5c4b421ab919356ab9707ff18f686d93f9`) selected
only 2 known-safe moves among 16 fixed fatal-choice positions. Interpolating
20% toward the hidden-only coefficients barely changes test quality (NLL
2.62576 vs 2.62543 for full refit; hidden NLL 2.40792 vs 2.45834), and still
selected only 2/16 known-safe moves. It is not a solution to the tactical
failure.

The recent hidden-only fit uses `MM_CHECK_UNSEEN=1.3592952` and
`MM_THREAT_UNSEEN=0.5914142`, changing only those two full-prior coefficients
from v35. Research binary SHA-256:
`adbbb2a4dc998d2485844ccaf8ad3a4783e9f5f6b5efbb14b4cc3df8ee298ff9`.

## Fixed-prefix replay results

On the same 16 selected hidden-arrival fatal choices across Duck, Decent Chess
Bot, Strongly Invisible, and Instructors, v35 selected 16/16 referee-fatal
moves. The recent hidden-only prior selected 9/16 fatal moves and 7/16
known-safe alternatives. The true board's median posterior mass rose from
0.0675% to 0.478%, and median rank improved from 273.5 to 35. None of the seven
rescued choices allowed an immediate opposing king capture on the true board.
The arbitrary 20% blend selected only 2/16 known-safe alternatives.

On 12 previously selected nonfatal controls, the recent hidden-only candidate
and baseline both selected zero immediately fatal moves, and each selected two
of the enumerated true-board safe alternatives. No candidate choice allowed an
immediate king-capture reply. These are small, selected, fixed-prefix checks;
they do not simulate policy responses or longer continuations and are not
playing-strength evidence.

Artifacts:

- [`recent-hidden-only-hidden-arrival-compare.json`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-hidden-arrival-compare.json)
- [`recent-hidden-only-controls-12-referee.json`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-controls-12-referee.json)
- [`recent-hidden-only-hidden-arrival-16.json`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-hidden-arrival-16.json)
- [`recent-hidden-only-controls-12.json`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-controls-12.json)
- [`blend20-hidden-arrival-referee-compare.json`](../astra-submissions/analysis/move-model-refit-20261025/blend20-hidden-arrival-referee-compare.json)

## Decision and next gate

The hidden-only prior is the strongest current candidate for this specific
failure family, while the full refit is the stronger general move predictor.
Do not combine them by a global linear blend or promote either yet. A 91-case
hidden-arrival fixed-prefix run at a five-second search cap is underway; run
the identical cases against the baseline before interpreting it. If the
candidate retains its advantage, the next experiment should branch the changed
moves through opponent replies and compare full game outcomes or paired
self-play. Do not call replay prediction or a selected loss diagnostic an Elo
gain.
