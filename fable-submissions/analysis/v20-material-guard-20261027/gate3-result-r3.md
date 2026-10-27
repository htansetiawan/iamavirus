# Gate 3 result: r3 against the decision contract (27 Oct 2026)

Queue `data/arena_local/queue-v36r3.json` (sha256 `2ee4f745…`), candidate r3 zip
`5cdbb9caf8a3` (source mist-c `ff89313`), comparator v35 zip `24791ca64a42`, Misty wrapper
`data/zoo/misty-v16.zip`; course referee, 180+2, two lanes on cores 2–3 and 4–5.
Launched 2026-10-27T01:40:52Z, last game ended 08:21:31Z (the 13:40:52Z cap was not reached).
Run receipt `data/arena_local/receipts/queue-v36r3.json`: state complete, 104 attempted, 0 failed.
Ledger rows: 104, every attempt `ok`, no duplicate (matchup, pair, colour), summed game time 13.3 h.
Replays `data/arena_local/builds/<matchup>-p<pair>-<a|b>-white.json`.

## Thresholds (decision-contract.md §4)

| threshold | measured | pass |
|---|---|---|
| H ≥ 18/40 against v35 | 15.5/40 (15-1-24, score 0.388) | no |
| ≥ 7/20 in each colour | White 11.5/20 (11-1-8); Black 4/20 (4-0-16) | no (Black) |
| M − B ≥ −4 over 32 against Misty | M 21.5 (19-5-8), B 23.0 (21-4-7): −1.5 | yes |
| D = ½((H/40 − ½) + (M − B)/32) > 0 | −0.080 | no |
| zero attributable crash, illegal move or time forfeit | two time forfeits, both Misty's (pair 6, Misty as White, 9.7 s left at its last recorded move; pair 13, Misty as Black, 6.7 s left); r3 and v35: none | yes |
| every r3 end clock ≥ 10 s | lowest 19.7 s against v35, 19.8 s against Misty | yes |
| r3 median end clock within 10 s of v35's | direct games: r3 31.7 s, v35 33.3 s; against Misty: r3 36.1 s, v35 35.6 s | yes |
| all 104 jobs reconciled, no retries | 104/104, no retry | yes |

Verdict: **r3 fails gate 3** on the head-to-head score, the Black colour floor and the combined
direction. Astra's audit tool (`astra-submissions/tools/audit_v36_bench.py audit`, run by Fable
on the final ledger, output `gate3-audit-r3-run-by-fable.json`) returns `rejected` with the same
three failures plus the two Misty forfeits flagged for failure review (reviewed above: Misty's
clock, not r3's). Its pair bootstrap of D: 95% [−0.216, +0.036].

## Detail

- Against Misty by colour: r3 White 11/16 (10-2-4), Black 10.5/16 (9-3-4); v35 White 12.5/16
  (11-3-2), Black 10.5/16 (10-1-5). Paired by seed (16 pairs, both colours): r3 ahead in 6, behind
  in 5, level in 5; sum −1.5 points; pair bootstrap 95% [−8.0, +4.5] points. Not distinguishable
  from v35 against Misty; clearly worse than v35 head to head, and as Black in particular.
- Terminations: direct games 39 king captures and 1 threefold repetition; every r3 loss against
  v35 is a king capture, lengths 56–171 plies (median 95.5). Against Misty: 25 king captures,
  5 repetitions, 2 Misty time forfeits.
- Throughput: nodes per decision level with v35 (interim audit 06:15Z); guard time is charged to
  the clock, not the search, and the end clocks above show no clock cost.
- Cause: the piece term's capture helper priced an enemy capture that leaves the enemy king
  capturable as a material loss (chatroom 167, 168); corrected in mist-c `dd89907`, outside r3.
  r3's games are not pooled with any later candidate.
