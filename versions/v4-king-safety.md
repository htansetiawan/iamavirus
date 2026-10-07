# v4 — king safety over the full population (`5e0ef63`)

## The bug this fixed

Greek Gift, the top-rated team at ~2126, beat v3 twice with one idea in both
colours: **offer a piece beside the king, defended from a distance we cannot
see.**

| game | bait | hidden defender | v3 played |
|---|---|---|---|
| `qp6mfacx` | `Bf7` | `Ne5` | `Kxf7` — lost in 18 plies with level material |
| `z6mbi981` | `Qe1` | `Re8` | `Kxe1` — lost at ply 63, material −5 |

Replaying `qp6mfacx` through the belief showed the information was **present**:
8.2% of hypotheses said the square was covered (14.0% for the rook in
`z6mbi981`). It was lost to sampling. The safety test counted failures among the
**eight sampled columns** of the matrix game, and when one hypothesis in twelve is
fatal, none of eight samples usually contains the attacker — so the filter read
the risk as exactly **0.000** and accepted a move that lost on the spot.

## Implemented

- King-loss probability computed over **all** hypotheses, for **every** legal
  move, **before** any shortlist exists. The ordering matters: filtering after the
  shortlist lets a search of one guessed board discard the only safe reply, which
  can then never be reconsidered.
- Tolerance 0.25 → 0.04, strict comparison.
- A band of least-dangerous moves when nothing clears the tolerance, so the search
  still chooses on merit rather than a probability deciding alone.

## Results

| measurement | value |
|---|---|
| v4 vs v3, 48 paired games | 0.573 ± 0.069 (~+51 Elo, 1.1σ) |
| both Greek Gift traps | declined |

This was the first change to measure positive. It is **not** conclusive: 1.1σ is
the same significance at which the v3 material-risk term measured *−47*.

## The defect found afterwards

An offline benchmark against real games showed v4 still plays `e8f7` in
`qp6mfacx` under other seeds. A sweep over 15 seed/population combinations:
**the bait was declined only 7 of 15 times.** The regression test passed by luck —
seed 4242 happens to decline.

A threshold was the wrong instrument. In that position *every* move carries ~8%
risk, so a hard threshold rejects all of them and the fallback band re-admits the
fatal one; and because safety had moved to a pre-filter, the in-matrix penalty was
deleted, leaving the risk invisible inside the surviving set.

This is what v5 addresses.
