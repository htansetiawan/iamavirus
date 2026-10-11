# v30 draw conversion audit — 2026-10-11

A public snapshot at **05:50 EDT (Boston), October 11** contains **75W–13D–85L over 173 games** for arena v30. This is a version record, not a causal estimate of strength. The full cursor-stable listing and completed replays are frozen on Seagate.

All **13 draws** are independently reproduced as threefold repetitions, including all **1,537 full-board and both-color observation frames**, legal moves, castling/en-passant repetition keys and terminal precedence. Ten ended with positive true material; six with at least a three-point lead. Five of those six were closed by our own move. Each of the six had a nonterminal alternative on the true board at our last decision.

| Game | Opponent | True material lead | We close the draw | Nonterminal alternatives at last own turn |
| --- | --- | ---: | --- | ---: |
| `ks0fqbab` | TA Baseline A | +6 | yes | 35 |
| `4geubeqf` | duck | +11 | yes | 25 |
| `gymi8wga` | TA Baseline S | +9 | yes | 26 |
| `mzjmy3l6` | Greek Gift | +13 | yes | 24 |
| `ykpadh8e` | duck | +6 | no | 13 |
| `4lm8j10v` | TA Baseline A | +8 | yes | 23 |

## What this supports

There is a concrete conversion test family involving repeated moves with superior material. It includes Greek Gift, duck and TA S/A, so the implementation should recognize the position/history pattern rather than an opponent name. The target behavior is to seek safe progress when a draw is avoidable, while retaining draws when alternatives lose.

This does **not** prove the six positions are winning. True-board safe moves need not remain safe across every observation-consistent state. The audit does not measure a policy or two-ply forced wins. Under the referee's king-capturable rule, the opponent generally gets a response to an attack; the zero immediate-terminal-win count in the raw report is not evidence that no tactical win was missed.

The original C frontend tracks repeated **own-piece configurations**, a necessary condition for full-position repetition but not sufficient to prove it: hidden enemy state and rights can differ. M4 currently neither restores discarded full histories nor uses that legacy root action exclusion. A hard ban based on own-piece repetition alone could reject the only safe action. Do not equate such a ban with exact threefold adjudication.

## Proposed next gate

Preserve these six conversion seats plus the three negative-material draws as regression controls. Compare current policy with an opt-in cycle-avoidance tie-break among actions whose estimated king risk does not increase. Keep this independent of the running terminal-gap experiment. Before adoption, require (a) fewer selected repeating moves in the conversion cases, (b) no new immediate loss in the negative-material draw controls, and (c) paired full-game conversion evidence, since merely prolonging the game is not a win.

This is a hypothesis and frozen diagnostic batch, not a shipped feature or untouched training holdout. Fable already cached all 13 replays: the audit reused those bytes and made only two paced list requests. `fetch.json` records shared-cache paths and hashes. Large files are under `/media/henrytan/seagate/iamavirus/astra/corpus/v30-draws-20261011/`.

Reproduce with the starter virtualenv: `python astra-submissions/tools/audit_public_draws.py --version 30 --output FRESH_DIRECTORY`. New public results may change a fresh snapshot; use the saved listing for this report's denominator. No GPU or private API access was used.
