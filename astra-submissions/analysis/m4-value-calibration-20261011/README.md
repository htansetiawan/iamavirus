# Stockfish value calibration against public FOW outcomes

**No evaluator change is justified by this diagnostic alone.** One seeded
nonterminal position per distinct recorded move trajectory was reconstructed
and checked against both replay observations. Stockfish depth1 evaluates the
current FEN. Labels are final White scores (1, 0.5, 0) under the recorded
players' policies, not equilibrium values.

The 1,000-game pilot and expanded 10,000-game audit use the same frozen cached
game order. Exact move-trajectory duplicates are excluded. A trajectory hash
assigns 80% to calibration and 20% to evaluation. Repeated positions and related
player versions can still cross this split; this is not a strict generalization
benchmark. Public data and CPU only; no API calls or GPU training were needed.

| Expanded audit | Raw Brier | Calibrated Brier | Raw log loss | Calibrated log loss |
|---|---:|---:|---:|---:|
| 1,968 held-out games | 0.14730 | 0.14642 | 0.48063 | 0.46037 |
| 617 held-out named-elite pairs | 0.17973 | 0.17453 | 0.58255 | 0.55177 |

The fitted map is `sigmoid(0.69407 * clip(cp/200,-20,20) + 0.02484)`.
It softens the orthodox score's certainty, but the small overall Brier change
does not demonstrate better decisions or stronger play. Single-PV scores at a
position are also not identical to parent-MultiPV child values used by M4.
The follow-up feature screen has separate position-group splits and excludes
the first 1,000 inspected games; see `../m4-fog-value-screen-20261011/`.

## Corrected engine-input defect

The original run stopped after 95 samples. Next game `qsijccp6`, selected ply37,
has a valid current orthodox board but contains `e8g8` at ply30 while castling
through attack. That historical move is legal in FOW. Sending the historical
move stack to orthodox Stockfish terminates the engine. Sending the current
FEN returns +701 cp for White. See `failure-reproduction.json`.

The failed run remains untouched on Seagate. Corrected runs rescore the frozen
selection via FEN snapshots and enforce a 10-second analysis timeout. All 95
old positions and cp values reproduce exactly. The original sandboxed
diagnostic stalled in subprocess handling; the bounded host reproduction above
provides the history-versus-FEN evidence, not that stall.

`positions.jsonl` retains the 1,000-game pilot. `10k-manifest-summary.json`
records paths and hashes for the larger dataset and full selection manifest on
Seagate. The FEN encoding is orthodox-canonical; it can omit an EP square when
no orthodox-legal EP capture exists. A future rules-exact fog-feature corpus
should additionally retain raw FOW EP state. No policy is trained or deployed
from this audit.
