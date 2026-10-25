# 104 — Astra: broad hidden-prior replay is promising but overlaps training

2026-10-25. Research-only; no submission ZIP changed.

The recent hidden-only coefficients (`MM_CHECK_UNSEEN=1.3592952`,
`MM_THREAT_UNSEEN=0.5914142`; binary SHA-256
`adbbb2a4dc998d2485844ccaf8ad3a4783e9f5f6b5efbb14b4cc3df8ee298ff9`) were
replayed against all 91 positions in the saved hidden-arrival audit. Search was
capped at five seconds per position. Both baseline and candidate completed
91/91 with no errors.

| Opponent | Cases | Baseline fatal | Candidate fatal | Baseline safe alternatives | Candidate safe alternatives |
|---|---:|---:|---:|---:|---:|
| Duck | 27 | 25 | 18 | 2 | 9 |
| Strongly Invisible | 22 | 22 | 7 | 0 | 15 |
| Decent Chess Bot | 24 | 20 | 10 | 2 | 14 |
| Instructors | 18 | 16 | 8 | 3 | 10 |
| **Total** | **91** | **83** | **43** | **7** | **48** |

No selected candidate move enabled an immediate king-capture reply when
checked on the true board. These are loss-selected fixed prefixes. This does
not measure a response policy, multi-ply continuation, win rate, or Elo. The
candidate also changed its choice much more often, so strategic costs outside
the immediate fatality label remain unknown.

## Independence audit

The 5,940-game training sample overlaps 26 of the target games. Because the
dataset sampled every eighth opponent decision and excluded IAmAVirus moves,
only four of the 91 immediately preceding opponent decisions were themselves
sampled training labels. That is enough overlap to treat the current result as
provisional rather than held out. Next, refit after excluding all 91 game IDs
and rerun the exact same 91 cases with the same search budgets. Then test a
larger nonfatal control set and branch rescued actions through multi-ply
opponent responses. No arena release until the independent and continuation
gates are clean.

The excluded-game fit is complete: 5,889 games / 59,100 positions remain.
On its fresh game-disjoint test split, hidden-only coefficients are
1.3541158/0.5908292. Frozen-v35 vs hidden-only metrics are overall NLL
2.64202/2.64749 and hidden-action NLL 2.71751/2.22285 (1,037 hidden-action
positions). On the same 91 fixed-prefix cases at five seconds, the independent
candidate selected 47 referee-fatal moves and 44 known-safe alternatives,
versus baseline 83 fatal and 7 known-safe. The candidate had no immediate
king-capture reply after its selected moves. Median true-board mass changed
0.036%→0.078%; median rank 418→151. This removes direct game-overlap, but the
set is still loss-selected and the test is one-ply only. Candidate choices
changed in 58/91 cases, so nonfatal controls and multi-ply continuation checks
remain necessary.

Artifacts:

- [`91-case paired comparison`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-wide-compare-91-5s.json)
- [`baseline trace`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-wide-baseline-91-5s.json)
- [`candidate trace`](../astra-submissions/analysis/move-model-refit-20261025/recent-hidden-only-wide-candidate-91-5s.json)
- [`independent paired comparison`](../astra-submissions/analysis/move-model-refit-20261025/exclude-hidden91-wide-compare-91-5s.json)
- [`independent candidate trace`](../astra-submissions/analysis/move-model-refit-20261025/exclude-hidden91-candidate-wide-91-5s.json)
- [`recent training manifest`](../astra-submissions/analysis/move-model-refit-20261025/recent-game-sample.jsonl)
