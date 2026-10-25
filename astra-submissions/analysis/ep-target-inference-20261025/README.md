# Astra experiment: infer en passant from the observation signal

2026-10-25. This is a move-generation correctness experiment against the
read-only v35 archive. It is not packaged, submitted, or an Elo claim.

## Finding

The v35 `view_moves` helper adds an en-passant action only when the adjacent
captured pawn is not attacked by any of our pieces. That misses a legal capture
when the pawn is already visible for another reason, even though the empty
capture destination is visible because en passant is available. The archived
referee confirms that the destination is added to the observation for a
pseudo-legal en-passant move, and that UCI input is accepted only if it is
pseudo-legal in the true position (`FowBoard.parse_uci`).

The bot first builds its safe `allowed` list with `view_moves`. At final move
validation, it accepts a move missing from that list only when the belief is
not overflowed and the move is legal in every belief board. With an overflowed
belief, an otherwise valid move omitted by `view_moves` is replaced by a move
from the allowed list. The omission therefore matters most when belief support
is capped or fallback logic uses this list; exact-belief decisions have an
additional legality check.

## Candidate change

The patch records the destinations already visible through ordinary legal
moves from the observation. It infers an en-passant action when the adjacent
enemy pawn is visible, the destination is visible and empty, and no ordinary
move could have revealed that destination. This is conservative: an unknown
intermediate square can prevent inference, but cannot create a false action.
The original captured-pawn visibility inference remains in place.

The patch is [belief-ep-observation.patch](belief-ep-observation.patch). It is
applied only to a temporary extraction of the v35 archive by
[`run_audit.py`](run_audit.py); the Fable archive is never modified. The audit
fixture reproduces v35's old `view_moves` and compares it to the patched
function on identical sampled positions.

## Result

Command: `python3 astra-submissions/analysis/ep-target-inference-20261025/run_audit.py --games 2500 --seed 1332956945`

| Measure | Result |
|---|---:|
| Random legal playouts / positions | 2,500 / 264,896 |
| True legal en-passant actions | 1,195 |
| Omitted by v35 `view_moves` | 655 |
| Recovered by patch | 554 / 655 (84.6%) |
| Still omitted | 101 |
| Baseline extra illegal candidates | 0 |
| Patched extra illegal candidates | 0 |

Of the 1,195 en-passant opportunities, removing the right while holding the
board fixed left the **current observation** unchanged in 101 cases and changed
it in 1,094. This does not determine whether the complete observation/action
history distinguishes those 101 cases; the engine tracks history and a full
belief. The random legal playout distribution is a rules probe, not a sample
of arena policy decisions. Zero false additions in this finite fixture is not
a proof over all positions.

The patched v35 archive builds successfully with its included `build.sh` and
GCC. Patched binary SHA-256:
`9a174cbd966f14b296896a233eb90a9f041c484eb2305d4fe7114377012d3d9e`.
The input v35 ZIP SHA-256 is
`24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`.

## Multiagent implication and next gate

This is a concrete example of why move generation belongs to the information
model: a move's availability can depend on an en-passant right that may not be
obvious from one observation. `gtcfr.c` expands each sampled world with
`generate_moves` on its full board. Its information-set map keys on the acting
player's observation/action-history hash, then handles a same-key action-count
mismatch by creating a separate information set. That is a possible strategy
fusion path if the *full* acting-player histories do not reveal the right. This
random-position audit does not prove that such full histories occur in the
actual tree; construct and test those histories before claiming a CFR defect.

Next, test two cases separately: (1) patch integration against exact referee
positions and archive protocol; (2) a bounded full-clock paired gate only after
the existing v35/v36 king-guard run frees cores. Also add an exact belief case
where all boards agree on en-passant legality and an overflowed belief case
where the observation alone proves it. Keep the v36 guard and en-passant arms
separate initially so any result remains attributable.

No release ZIP was changed and no arena version was reserved for this idea.
