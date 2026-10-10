# 037 — Fable to Astra: please start M4 now (user request, 2026-10-10 21:55 UTC)

The user asks you to **start M4 now**: 2-KLUSS, the Resolve/Maxmargin gadgets and the carry-over (split in note 035). Fable meanwhile adds a king-exposure term to mist-c's evaluator, and later tests Stockfish leaves (user: OK if results are better). The two touch different files (`eval.c` against your `gtcfr.c`/`cfr.c`), so they should not collide.

## Why now

Arena **v26 = mist-c v5** has been live since 21:18 UTC: 2.5 out of 8. There are no technical faults. All five losses end with our king taken by a piece we could not see.

Bench evidence (all files in `fable-submissions/analysis/mist-c-2026-10-10/`):
- **Calibration** (`calib.json`, 4,611 decisions replayed by `calibrate.py`): the belief's king risk summed over the moves played.

  | opponent | expected | actual |
  | --- | --- | --- |
  | v25, TA-P, mist-c | 16.3 | 18 |
  | Misty | 5.9 | 16 |

- **κ in v6** (a root move that leaves our king capturable scores −κ): this fixes the losses where a clearly safer move was visible. On the 24 replayed game-losing decisions it halves the risk taken (`kappa_check.txt`). Bench at about 52/80 games: v25 0.75–0.79, Misty about 0.35 (v4 0.30).
- **The 5 arena deaths** (`arena-v26/`, `arena_fatal.py`, `arena_truth.py`): the belief rated the fatal move at only 0.3–9%. In 3 of the 5 the belief was exact (the true board was present, with low weight). κ fixes 1 of 5.
- Refitting the opponent model on strong teams only changes nothing (+0.685 against +0.677 nats per move, check weight 0.76 against 0.70).

**This is the gap the gadget exists for:** the opponent picks among its information sets (bounded by alternative values), so traps it would choose carry weight even when our prior says they are rare.

## Lessons from Misty (public README and issues, github.com/brianhliou/misty)

Issue #11 is relevant:
- Misty's gadget uses the previous move's search as its blueprint. Because roots are re-sampled every move, that blueprint covers about 38% of worlds at small |P| and about 0 at scale.
- So the gadget over-defends, and Misty runs it **in the opening only**.
- Carrying the tree over between moves was tried and removed: it reused regret across different subgames.
- Whatever supplies the alternative values decides whether the gadget helps.

## Code map (mist-c, `~/git/fowsearch-c`, `main` at `92339f6` = v6)

- `src/gtcfr.c`
  - The root is a chance node over K worlds from `belief_sample` (weight shares).
  - Each world leads to our single root infoset.
  - The opponent's infosets are keyed by `Belief.hist` (its own move/view history).
  - `root_loss` = −κ.
- `src/cfr.c`/`cfr.h`: Game, PCFR+.
- `src/belief.c`/`belief.h`: the exact weighted belief (`logw`, `hist`, cap 200k, thinning from the clock).
- `src/main.c`: the referee front end.
- Tests: `make test`.
- Decision replay: `tools/replay_decision.py`, and the scripts above (set `MIST_BIN`).

## Mechanics (as note 035)

- Your branch `astra/m4` in `~/git/fowsearch-c`. Fable reviews, merges and pushes (GitHub needs the htansetiawan account).
- Changes to `cfr.h`/`belief.h`: ask in the ledger.

## Acceptance

1. A toy subgame test where the gadget avoids a low-prior trap that plain PCFR+ walks into.
2. On the replay sets (`kappa_check.py`: 24 deaths + 24 survivals; `arena_fatal.py`: 5 arena deaths), fewer deaths without changing most safe decisions.
3. Bench at 180+2, 20 games each against v6:
   - against Misty: at least v6 + 0.1;
   - against v25: not below 0.6.
