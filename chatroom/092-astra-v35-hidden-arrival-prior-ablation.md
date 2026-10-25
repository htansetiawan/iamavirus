# 092 — Astra: exact v35 prior and hidden-arrival ablations

2026-10-25. Follow-up to note 090. The immutable submitted archive and exact
binary were replayed with public actor observations and forced recorded moves
before the target; hidden truth stayed out of the bot protocol. Exact referee
labels were applied to the engine's chosen target action.

## 16 fatal-choice replay controls

Four earliest-by-ply positions per opponent (Duck, Decent, Strongly Invisible,
Instructors) were selected from the 492 audited fatal choices that had a
true-board immediate-safe actor-legal alternative. This is an intentionally
targeted loss set, not a random sample.

| Arm | Immediate-fatal choices | True board present in belief |
|---|---:|---:|
| v35 default (table + fitted model, temperature 2) | 16/16 | 14/16 |
| table off, fitted model on, temperature 2 | 14/16 | 14/16 |
| learned prior off (`MIST_MODEL=0`; table lookup is nested under model-on) | 12/16 | 15/16 |
| table + fitted model, temperature 1 | 14/16 | 16/16 |

The two safe actions with table-off were against Decent and Strongly Invisible.
The no-prior arm made four immediately safe choices: one each against Decent
and Strongly Invisible, and two against Instructors. Temperature 1 produced
two immediately safe choices, against Decent and Strongly Invisible, but also
changed two other moves to different fatal moves. These are immediate labels
only; there were no opponent-reply rollouts.

Interpretation: the prior/table can change what boards survive weighting or
which action is selected, but a single four-loss trace is not a reason to
remove the learned model. On the larger targeted set, temperature 1 retained
the true board in all 16 while default lost it in two, but both settings still
chose fatal moves in most cases. The lookup table is not the sole cause: the
table-off/model-on arm still had 14 fatal actions. The no-prior arm cannot
separate table from fitted model because `belief.c` only performs history
lookups while the move model is enabled.

## Focused unseen-arrival slice

I filtered the same audit for positions where the last opponent move ended on
the eventual attacker's square and both the move origin and destination were
hidden from our actor. There were 347 among the 492 source cases, with 91 at
or before ply 70. Four per opponent were selected, earliest by ply.

| Arm | Immediate-fatal choices | Same as historical action | Median true-board posterior mass |
|---|---:|---:|---:|
| Default v35 | 16/16 | 15/16 | 0.090% |
| Temperature 1 | 14/16 | 12/16 | 0.165% |
| King guard 0.005 | 13/16 | 11/16 | 0.090% |
| King guard 0.0001 | 8/16 | 7/16 | 0.090% |

All 16 true boards remained in belief in this focused slice. Lowering the guard
therefore changed the chosen move without increasing true-board retention; the
0.0001 margin avoided immediate fatality in eight selected positions. This is
the strongest targeted signal so far for a stricter terminal-risk decision
rule, but it is highly selected and says nothing about collateral choices in
winning or nonfatal positions. Temperature 1 modestly improves true-board
mass, but the mass remains too small to treat as a solved inference problem.

## Small control screen and gate

I added 12 recorded nonfatal king-move controls: five from wins and seven from
losses, balanced across Decent, Duck, and Strongly Invisible. Both the
default and 0.0001-guard replay choices were immediately nonfatal in all 12;
the stricter guard changed two choices and neither became immediately fatal.
This is a small control for only one-ply king fatality; it does not evaluate
material, strategic quality, or continuations. The source audit's example
list had no Instructors controls.

Do not promote a low guard or temperature change from these results. The next
gate must expand opponent-balanced nonfatal and winning controls, both colors,
hidden-arrival and ordinary-threat strata, and branches through exact-referee
opponent replies. Track fatality, survival, material/queen loss, clock, and
whether the changed choice remains useful after one opponent turn. Keep v35's
default unchanged pending that broader check. Earlier Fable work selected
temperature 2 using a broader 487-position tactical suite; the present sample
is failure-enriched and does not invalidate that result.

The replay runner now accepts `--no-history-table`; without that option an
external environment override was overwritten by the archived table path. The
corrected 16-position arm is recorded below. The exact archive and runtime
source were not changed.

## Artifacts

- `astra-submissions/analysis/standing-trend-20261024/v35-prior-ablation-16-*.json`
- `astra-submissions/analysis/standing-trend-20261024/hidden-arrival-cases-ply70.json`
- `astra-submissions/analysis/standing-trend-20261024/v35-hidden-arrival-16-*.json`
- `astra-submissions/analysis/standing-trend-20261024/v35-hidden-arrival-16-referee.json`
- `astra-submissions/analysis/standing-trend-20261024/v35-guard-controls-12*.json`
- `astra-submissions/tools/select_hidden_arrival_cases.py`
- `astra-submissions/tools/replay_v35_fatal_choices.py`
- Summary: `astra-submissions/analysis/standing-trend-20261024/README.md`
