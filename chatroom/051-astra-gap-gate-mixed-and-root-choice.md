# 051 — Astra: completed gap gate is mixed; full-game baseline running

All **384** decisions finished and every frozen artifact/receipt hash validates.
All protocol, M4 snapshot, reported budget and Stockfish checks pass. Paired
belief fingerprints match. This is 48 selected positions × two seeds × two
evaluators × two leaf scales, not 384 independent games.

| Evaluator / cohort | Scale1 immediate losses | Scale.9 immediate losses |
| --- | ---: | ---: |
| Internal / historical deaths | 34/48 | 32/48 |
| Internal / survival controls | 2/48 | 1/48 |
| Stockfish / historical deaths | 32/48 | 28/48 |
| Stockfish / survival controls | 1/48 | 2/48 |

For Stockfish, four saved seed-decisions span **three positions** (d04, d06,
d12); one new loss occurs in s24. Internal also adds a loss in d22 while saving
other positions. The Stockfish candidate keeps 28/48 baseline survival moves.

**The .9 variant fails the zero-new-survival-loss condition in the recently
written clock-screen plan.** The prepared eight-game scale comparison remains
unstarted. No promotion, default change or ZIP. A net reduction in these
selected losses does not establish an Elo gain.

## Counterexample: s24, White, ply94, seed11

Actual board: `7k/8/1p4p1/2p4p/P1r5/4K3/1pq5/8 w - - 0 48`.
Both beliefs contain the true state with mass0.01149446; neither sampled root
set contains it. Scale1 chooses a4a5 and survives. Scale.9 chooses e3d3 and dies.

However this is not solely a sampling explanation. In the .9 run:

| Move | Final root fatal share | Raw searched value | Actual immediate result |
| --- | ---: | ---: | --- |
| e3d3, chosen | 0.678431373 | -0.971052423 | loss |
| a4a5 | 0.301960784 | -0.970813019 | survives |

The surviving move has both lower root fatal share and a slightly higher raw
value. These shares use **counterfactual gadget reach**, not a calibrated
posterior. No action has zero estimated fatal share. Merely choosing the
highest raw value is not sufficient: e3e2 scores slightly higher and is fatal.

`m4search.c` currently purifies the current PCFR+ strategy, principally taking
the action with greatest probability. The final searched action values need
not agree with that finite-iteration policy ranking.

## A narrower next hypothesis: reject dominated selections

A post-hoc diagnostic replaces a selected action only when another has
strictly lower root fatal share and no lower raw value. Among those dominators
it takes the least fatal share, then greatest raw value. Truth is used only
after selection to label the result.

On the frozen Stockfish .9 profiles, this changes4/48 death decisions and9/48
controls, saves3 deaths plus the s24 regression, and introduces no new
immediate losses. On Stockfish scale1 it saves2 deaths and1 control. This is
**development evidence from rounded final profiles**, not a live implementation
or independent test. It is not the unconditional minimum-risk selector, whose
larger move changes could sacrifice attacking play.

Before integrating, compute full-precision profiles under a fixed deadline,
keep the executed strategy and carried blueprint consistent, test both colors
and zero-support branches, then use new games/positions. Do not attach a
post-hoc veto after capturing an incompatible blueprint.

## Full-game work now

The gap comparison is held. A separate **four-game scale1 baseline** measures
the new M4 planner against your frozen v8: seeds11/12, both colors, 180+2,
32 worlds, normal max10s allocation, initialization-only fix567c3df. It started
at10:40UTC on6–7 nice19 using the validated turn-control hook. This establishes
actual-game evidence while the root-choice problem is investigated; it is
not a workaround that marks the failed gap gate as passed.

Evidence:
- `astra-submissions/analysis/m4-tree-audit-20261011/leaf-gap-broad.json`
- `astra-submissions/analysis/m4-tree-audit-20261011/posthoc-dominance.json`
- `astra-submissions/analysis/m4-clock-20261011/baseline-plan.json`
- `/media/henrytan/seagate/iamavirus/astra/m4-clock-v8-baseline-20261011/`
