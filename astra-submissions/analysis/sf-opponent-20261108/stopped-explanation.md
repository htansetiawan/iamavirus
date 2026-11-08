# What the Misty gate changed

Post-hoc description; original advancement threshold and all results remain unchanged.

| arm | clean losses | draws | clean wins | technical | lowest final clock |
|---|---:|---:|---:|---:|---:|
| base | 3 | 1 | 10 | 0 | 29.7s |
| candidate | 4 | 2 | 8 | 1 | 24.6s |

## Loss patterns

| arm / game | final move | pattern | truth-safe replies |
|---|---|---|---:|
| candidate / block 1 black | f8g7 | king_move_into_attack | 2 |
| candidate / block 2 black | f7e7 | king_move_into_attack | 0 |
| base / block 2 black | g6h6 | king_move_into_attack | 5 |
| base / block 4 white | b4b5 | ignored_existing_attack | 1 |
| base / block 4 black | f8e7 | king_move_into_attack | 15 |
| candidate / block 5 black | f5f4 | ignored_existing_attack | 3 |
| candidate / block 6 black | g6h5 | king_move_into_attack | 3 |

Zero truth-safe replies means the final move was already forced on the true board. It must not be labelled a missed escape. A positive count does not establish that the actor could infer the danger.

## Paired-game matching

First differing actor across 14 available paired histories: {'arm': 12, 'Misty': 2}. 2 pairs have a missing game and are explicitly unassessed.

A first difference in Misty before our actions diverge demonstrates residual opponent/search variability. It does not invalidate randomized comparisons, but same seed must not be described as an identical opponent response stream. The stopped audit makes no statistical comparison from outcome-dependent missing games.

Full attacker visibility, safe replies, replay hashes and divergences are in stopped-explanation.json. None is a deployed feature, fitted threshold or strength claim.
