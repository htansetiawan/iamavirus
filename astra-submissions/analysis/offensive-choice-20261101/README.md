# Offensive-choice audit, 1 November 2026

**Neither case supports a missing-tactic or guard-exclusion fix.** Unchanged
v37 selects the known forcing clearance in two of three seeds for Instructors'
position and one of three for Cranberry Lemon's position. The alternatives
have similarly high expected search values. This is a mechanism diagnostic,
not a playing-strength comparison or a reason to prefer a move using truth.

## Frozen inputs and provenance

The two cases are the unselected tactics from the six-case ability screen in
`../conditional-exchange-20261101/`. Run all three preselected seeds
204100–204102 at a 2.5-second cap, first attempts only. `plan.json` was frozen
locally before execution, not committed before execution. The binary is the
same post-choice-only exporter from that audit, SHA256
`90c2f552979b70c8b38a2dbc48bbdc37cfef0b665d0b50bd71dae205839df160`,
based on exact v37 ZIP `41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c`.

Bots receive their own observations, clocks, and forced earlier own moves.
True boards are joined afterward. No model, guard, search default, or Fable
core source was changed. Other user inference/download jobs shared CPUs;
node counts and elapsed times cannot support a throughput comparison.

## Results

In `5ug2qtkb:61` (Black), the recorded tactic is `Bd4xf2`, followed by
`Rd3xd7`. The alternative `g4h3` is a **pawn capture**, not a king move.
All 21 belief worlds are searched. Truth-board mass is 30.43%; Rd7 is present
in every world, but the enemy king is on g1 in only 54.35% of the belief.

In `rzr3p3jl:53` (Black), the recorded tactic is `Bf5xg4`, followed by
`Rf8xf4`. The alternative is `Bf5e6`. All 12 belief worlds are searched.
Truth-board mass is 6.76%; Bf4 has 77.89% probability and the enemy king is
on d1 in 6.76%. A forcing check on the true board need not be forcing in the
other worlds the bot must consider.

Both compared moves survive guards and have zero immediate king-loss risk
in every run. Values below are weighted search values, not calibrated win
probabilities. The first alternative in `summary.json` is the recorded tactic.

| Case | Seed | Selected | Tactic value | Other value |
|---|---:|---|---:|---:|
| 5ug2qtkb-61 | 204100 | `g4h3` | 0.951747 | 0.960288 |
| 5ug2qtkb-61 | 204101 | `d4f2` | 0.962503 | 0.945561 |
| 5ug2qtkb-61 | 204102 | `d4f2` | 0.960977 | 0.949284 |
| rzr3p3jl-53 | 204100 | `f5e6` | 0.923816 | 0.923822 |
| rzr3p3jl-53 | 204101 | `f5g4` | 0.926250 | 0.923091 |
| rzr3p3jl-53 | 204102 | `f5e6` | 0.922242 | 0.927055 |

The root strategy is pure in the first case. In the second, it assigns the
recorded tactic 9.82%, 62.74%, and 26.72%, respectively. Seed and wall-clock
changes alter tree growth; these six traces do not isolate either cause or
establish which move is best under the player's information.

## Validation and disposition

All six first runs exit zero with valid protocol. Independent C++ rules
validate **68,870 move edges**, including board, turn, castling and en-passant
state; information-set action/probability signatures agree; root and branch
probability/value sums reconcile. Receipts pin input, output and raw audit
hashes. The compressed audits unpack to those same hashes.

No absent root world, guard exclusion, or absent tactical branch explains the
two initial choices. Do not increase samples, lower guards, or introduce a
truth-conditioned tactical override on this evidence. Preserve the corpus
and traces as future regression diagnostics. No candidate ZIP is justified.

Reproduce edge verification with
`python3 astra-submissions/experiments/conditional-exchange-20261101/offence_followup.py verify`
after unpacking the six `*.audit.json.gz` files to `*.audit.json` in this
folder. Do not rerun `run` into the original evidence directory.
