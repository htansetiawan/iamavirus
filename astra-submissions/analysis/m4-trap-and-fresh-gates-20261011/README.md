# Structural traps and fresh-game regression gates — 11 October 2026

**No runtime change or new release is justified by these probes.** The six
structural trap positions pass the current C candidate. Fresh arena losses
still expose missing belief support and poor weighting/decision quality even
when the true state is retained. Increasing root coverage alone did not fix the
new Greek Gift failure. These are offline diagnostics, not Elo estimates.

## Frozen control

- Candidate SHA-256: `5892c2a9015395de2f541f954d3d3edc06b9217d9c7291913fd01d9d23949ab0`.
- Stockfish SHA-256: `0f83d24cc46d2c66c60f16001af5444873bc112b7d028594513426894c12da19`.
- Seed 21, configured one-second decision budget, 100,000 iteration ceiling,
  20,000 replay-parent limit, 32 sampled roots. Search itself uses about 75%
  of that budget. Experimental closure/dominance/settling/witness modes off.
- The parent limit applies before an opponent update; successor population can
  exceed it. Thus the 137,962-state duck result is not a cap-invariant failure.
- Bounded Stockfish leaves, fast carried-root initialization, exact historical
  own moves. Only recorded protocol observations enter the bot. Full boards
  and structural labels remain in the offline audit.

Raw immutable outputs are on Seagate under `m4-dilemma-search-20261011` and
`m4-fresh-20261011-1544`. [inventory.json](inventory.json) records hashes of
every retained source and compressed copy. Binary hashes and command/config
records are retained; binary files and the full 8,839-action label table remain
on the data drive. The earlier native-label report contains that table's
provenance. No test data was used to fit a change here.

## Six setup positions: 12/12 avoid the labeled traps

Selection was declared before execution: all six positions with genuine
information-conflict actions in the existing 352-game validation scan, taking
the first recorded origin for each. There are 29 dangerous setup actions;
none was historically selected at those sampled decisions.

| Position / source decision | Cold choice | Searched-prefix choice | Highest conflict policy mass |
| --- | --- | --- | --- |
| `2c6a7576f2050ad9` / `eynqrj2j`, ply 8 | Nc3xd5 | Nc3xd5 | 0 |
| `31bbbb7f484dd46d` / `2p7kaz8z`, ply 6 | Nb1c3 | Nb1c3 | 0 |
| `387004b563862dde` / `pxccdifc`, ply 5 | Nb8c6 | h7h5 | 0 |
| `45bbf7b085cd9816` / `eynqrj2j`, ply 6 | Nb1c3 | Bc1e3 | 1.851% |
| `5d91ce48460c8e47` / `sslos3zm`, ply 10 | Ng1e2 | Qd2e2 | 1.362% |
| `6b21b567f075c87c` / `g2me9kso`, ply 10 | Bc1b2 | Qd1e2 | 0 |

Every final belief is the single true state. All chosen moves are legal and
immediately surviving. No evaluator call failed. All saved continuation traces
are complete. The actual played distributions place zero mass on the 29 setup
actions; two average policies retain small residual mass. Cold/warm also changes
prefix search and evaluator context, so it is not a clean carry-only ablation.
Total measured subprocess time: 29.50 seconds on cores 6–7.

The nearly similar `31bbbb…` and `45bbf7…` positions have different pawn
structure: the former retains the e2 pawn; the latter retains c2 instead.
Opening the e-file creates additional incompatible hidden-queen defenses.
The current search already handles this distinction in the sampled decisions.
Do not add an unconditional setup penalty or claim a newly acquired skill.

## Seven new arena games, independently reconstructed

Public snapshot at 15:44:31 UTC: active arena v30, Elo **1766.9958**,
**136W–23D–163L / 322**. Duck: **1904.0734**. The seven new results were
2W–1D–4L, including wins over Instructors (`3dfayxek`) and duck (`p63nhuqc`).
These are results of the active arena submission, not this C experiment.

All **700 frames** across these games were checked against the independent
referee: true boards, both observations, move legality and terminal outcome.
One Instructors loss (`hp7svdvm`) has no physically surviving final action and
was excluded from final-decision search probes for that explicit reason.

| Fresh loss | Historical move | C choice | Immediate survival | True-state belief share |
| --- | --- | --- | --- | --- |
| Greek Gift `gf2qssqu`, ply 82 | d6c7 | d6d7 | No | 1.266% / 119 states |
| duck `0x9ew96y`, ply 102 | Kb2a1 | Kb2c1 | No | 0 / 137,962 states |
| Greek Gift `9aij6zfq`, ply 59 | Kg8h8 | Kg8f8 | Yes | 0.283% / 34 states |

In `gf2qssqu`, an unseen rook moved b8–b1 after d5–d6 without changing
White's observation. Ke2 is the sole true-board survival. The 32-root control
misses the true state. Two additional arms isolate whether coverage fixes it:

| Arm | True state among roots | Chosen move | Adaptive-root fatal share |
| --- | --- | --- | --- |
| 32 roots | No | d6d7 | 0 |
| 128 requested, all 119 retained roots used | Yes | d6d7 | 3.544% |
| 32 roots with tactical witnesses | Yes | d6d7 | 3.237% |

Both treatment arms still select a fatal pawn move. In the all-state arm,
the safe-in-truth Ke2 has **12.403%** fatal share over adaptive root reaches.
These shares are search/gadget quantities, not the original posterior or
calibrated real-world probabilities. There is no evidence that simply
increasing a generic fatality charge would favor the actual escape.

Witness scanning covers all 119 states and adds three witnesses. The same
arms preserve the surviving Kf8 choice in `9aij6zfq`. This is one failure and
one safe control, not a broad strength gate. The additionally exported f1f2
trace is an unsafe comparison; **f1e2** is the actual surviving move, recorded
in the referee audit and full action profile.

## Won-game conversion remains a separate question

TA-A draw `e7j8nr8c` ends with Black about **820 centipawns ahead** (rook,
knight and pawns against king and pawns). Historical Rg7–h7 repeats; the C
control chooses Kg5–h6 and does **not** immediately repeat or lose. Its belief
contains 29 states and the true state at 2.458% weight. This does not establish
that C will convert the endgame; it only rejects this final repetition as a
reproduced C failure. No repetition patch was made.

## Next use

Keep these as separate fixtures: avoided information traps, missing posterior
support, supported but misweighted danger, and a won-endgame continuation.
The existing witness option remains experimental. A fresh learned model must
earn posterior/calibration benefit on held-out histories before integration.
The now-free GPU is running the separately declared SSL-transfer pilot, which
tests an existing representation hypothesis without changing production.
