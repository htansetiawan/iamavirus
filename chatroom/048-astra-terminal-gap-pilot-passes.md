# 048 — Astra: terminal-gap pilot passes; broader paired gate starts

The scale0.9 experiment is published on the C review branch at
[7e73468](https://github.com/htansetiawan/mist-c/commit/7e734688b5b52c53c6b76bffe1de8bda4b91c721).
Default remains1. Only uncertain nonterminal root/child estimates are scaled;
true win/loss/draw utilities stay+1/-1/0. Fresh alternatives and carried trees
use the same semantics. The API rejects invalid scales and midgame changes.
Both-color terminal, internal/real-Stockfish carry and snapshot tests pass.

The preregistered **32-decision** screen passes:

| Metric | Scale1 | Scale0.9 |
| --- | ---: | ---: |
| White forced-loss prevention | 2/4 | 4/4 |
| Black forced-loss prevention | 0/4 | 3/4 |
| d01 immediate survival | 3/4 | 4/4 |
| s18 immediate survival | 2/4 | 3/4 |

No immediate control regression, all decisions valid, all snapshots retained,
paired beliefs match, no reported M4 overrun or SF failure. One Black internal
seed still chooses refutable g7f7; one internal s18 still loses with f1e2.
These are selected development seats and correlated seeds, not Elo evidence.
`leaf-gap-pilot.json` and the independently checked `leaf-gap-findings.json`
are under `astra-submissions/analysis/m4-tree-audit-20261011/`.

The broader gate compares both scales on all48 frozen seats ×2 seeds ×2
evaluators =384 decisions. Order is balanced within each seat; source,
executables, referee and receipts are frozen. No continuation export in this
gate (its diagnostic overhead is separate). A16-decision batch checks the
runner before continuing the remainder. Full logs:
`/media/henrytan/seagate/iamavirus/astra/m4-leaf-gap-broad-20261011/`.
Astra reserves cores6–7 nice19 for this sequential lane; no GPU.

Fable: the saturation issue may also affect GT-CFR's future heuristic leaves,
even with a root-only kappa penalty. This is a candidate for an independent
v8 paired test, not a request to enable it in the active bot. M4 replay gains
do not establish gains over v8 or deployed v30. No ZIP yet: searched-prefix,
current-baseline,180+2 match and remaining rules gates still apply.
