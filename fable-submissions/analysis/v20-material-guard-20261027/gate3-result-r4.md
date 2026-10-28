# Gate 3 result: r4 against the decision contract (28 Oct 2026)

Queue `data/arena_local/queue-v36r4.json` (sha256 `0b92a8cf16f2…`), candidate r4 zip
`1649dfbfe23b` (source mist-c `dd89907`), comparator v35 zip `24791ca64a42`, Misty wrapper
`data/zoo/misty-v16.zip` (`62d8d389c2ed`); course referee, 180+2, two lanes on cores 2–3 and 4–5.
Seeds `300000 + 2·pair` (direct, pairs 0–19) and `301000 + 2·pair` (both Misty matchups, pairs 0–15),
as pinned in Astra's gate-1 receipt. Launched 2026-10-27T22:21:06Z on the gate-1 PASS (note 173);
last game ended 2026-10-28T04:35:01Z (the 10:21:06Z cap was not reached).
Run receipt `data/arena_local/receipts/queue-v36r4.json`: state complete, 104 attempted, 0 failed.
Ledger rows: 104, every attempt `ok`, no duplicate (matchup, pair, colour), summed game time 12.4 h.
Replays `data/arena_local/builds/<matchup>-p<pair>-<a|b>-<colour>.json`.

## Thresholds (decision-contract.md §4)

| threshold | measured | pass |
|---|---|---|
| H ≥ 18/40 against v35 | 19.5/40 (19-1-20, score 0.488) | yes |
| ≥ 7/20 in each colour | White 11/20 (11-0-9); Black 8.5/20 (8-1-11) | yes |
| M − B ≥ −4 over 32 against Misty | M 23.0 (22-2-8), B 19.0 (19-0-13): +4.0 | yes |
| D = ½((H/40 − ½) + (M − B)/32) > 0 | +0.056 | yes |
| zero attributable crash, illegal move or time forfeit | six time forfeits, all Misty's (reviewed below); r4 and v35: none | yes |
| every r4 end clock ≥ 10 s | lowest end clock 20.6 s against v35, 20.5 s against Misty; lowest clock at any recorded r4 move 19.7 s (direct) and 19.4 s (Misty) | yes |
| r4 median end clock within 10 s of v35's | direct games: r4 36.8 s, v35 40.3 s; against Misty: r4 38.0 s, v35 37.3 s | yes |
| all 104 jobs reconciled, no retries | 104/104, no retry | yes |

Verdict on the local screen: **r4 passes every gate-3 threshold.** Astra's audit tool
(`astra-submissions/tools/audit_v36_r4_bench.py audit`, output
`astra-submissions/analysis/v36-r4-gate1-20261027/bench-audit.json`) reports D = +0.056 with the
same matchup totals and returns `rejected` for one reason only: its six forfeit flags require a
failure review. That review is below; all six are Misty's clock. Uncertainty, by pair bootstrap:
D 95% [−0.072, +0.194]; H/40 95% [0.375, 0.600]; Misty pair sum 95% [−3, +12] points. Every
interval spans zero: locally r4 is not distinguishable from v35, with a positive direction.

## The arena read overrides the local screen

The same bytes played 48 arena games as version 36 (27 Oct 23:23Z to 28 Oct ~02:05Z): 15-1-32,
15.5 points against 24.4 expected from v35's per-opponent scores, z −2.88
(`docs/v36-status-20261027.md`). Under contract §5 the rollback rule for strength is the upper
end of the 95% interval below zero relative to v35; here the upper end is about −2.8 points, so
the rollback Henry made at ~02:05Z is the contract's own outcome. **Decision: r4 stays rejected
for release.** The local pass does not reverse it; it means this screen (v35 and local Misty as
opponents, 104 games) did not predict the arena result, so it cannot be the release gate on its
own. Astra's 174 sets Instructors and HYPOTHERMIA (both v4) as the minimum reference bar for the
next validation, with v35 as the control; the local screen keeps its place as the regression and
reliability check, which r4 cleared.

Do not re-upload r4. No further candidate of the piece term until a local setup reproduces the
arena deficit (next: unforced games of r4 and v35 against proxies of the weak bots v36 lost to,
both colours, on cores 2–5; the arena-only hypotheses in the status doc).

## Detail

- Direct games by pair (20 pairs, both colours): r4 took both games in 2 pairs, neither in 3,
  1.5 in 1 and split 14. Terminations: 39 king captures, 1 threefold repetition. r4's 20 losses run
  16–273 plies (median 81.5), its 19 wins 50–129 (median 85). The 16-ply loss (pair 0, r4 as
  Black, `builds/v36r4-vs-v35-p0-b-white.json`) is the kind of opening loss v36 took in the arena
  and is the first replay to run.
- Against Misty by colour: r4 White 11.5/16 (11-1-4), Black 11.5/16 (11-1-4); v35 White 11/16
  (11-0-5), Black 8/16 (8-0-8). Paired by seed (16 pairs): r4 ahead in 6, behind in 4, level in 6.
  On board terminations alone (forfeits removed) r4 21/30, v35 15/28; same direction.
  Terminations: r4's games 28 king captures, 2 repetitions, 2 Misty forfeits; v35's games 28 king
  captures, 4 Misty forfeits.
- Forfeit review (loser's clock at its last recorded move, from the replay): r4 games, pair 3
  Misty as Black 3.0 s at ply 153, pair 13 Misty as White 7.1 s at ply 24 (Misty spent its clock in
  12 moves, as in r3's pair 6); v35 games, pair 7 Misty as White 4.3 s at ply 116, pair 10 Misty as
  Black 10.9 s at ply 119, pair 12 Misty as Black 5.8 s at ply 145, pair 14 Misty as Black 9.4 s at
  ply 93. Misty's forfeits count as its losses under the contract; none is attributable to r4 or
  v35, whose lowest clock at any move was 19.4 s.
- Clock cost: r4's direct median end clock is 3.5 s below v35's (36.8 vs 40.3 s), inside the
  10 s allowance; against Misty r4 ends with 0.7 s more than v35. The guard time is charged to the
  clock and shows no reliability effect.
- Comparison with r3 (same queue structure, note 169): H 15.5 → 19.5, Black 4 → 8.5, M − B
  −1.5 → +4.0, D −0.080 → +0.056. The terminal-aware capture events (mist-c `dd89907`) removed the
  Black collapse on this screen; the arena did not confirm the bytes.
