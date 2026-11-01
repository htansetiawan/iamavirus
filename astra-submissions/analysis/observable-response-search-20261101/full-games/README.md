# Projection pilot closed: 2 wins, 6 losses against exact v37

1 November 2026. All eight first-attempt head-to-head games finished at180+2,
both colours, on the two reserved CPU pairs. There were no protocol, illegal
move, clock or worker faults. All670 replay frames passed the independent
ingest/rules validation. Both original runner handles are terminal; host checks
found no surviving owned processes or zombies. All Astra cores are released.

| Pair | Candidate White | Candidate Black |
|---|---|---|
| 0 | loss,101 plies | loss,110 plies |
| 1 | win,108 plies | loss,64 plies |
| 2 | loss,65 plies | loss,58 plies |
| 3 | loss,77 plies | win,79 plies |

The frozen rule closes the configuration at a score of2/8 or below. Therefore
**no Misty games, expanded trial, submission ZIP or deployment** follow.
Eight games are not a precise Elo estimate. The raw-response parent's0/8 used
different seeds; this does not establish a quantified gain from projection.

The tested candidate changed only the learned component of the opponent
response: it removed actions whose immediate king loss was provable from
that opponent's own view, then renormalized the remaining probabilities. Its
adversarial free component retained all legal actions. Confidence remained.25;
the frozen student, belief, guards, Stockfish and clock rules were unchanged.

`plan.json` and its dependencies were published before launch. `jobs/` contains
each original start, identity registry, result and full replay. `summary.json`
is final; `advancement.json` records the threshold decision and terminal host
checks. `resource-notes.json` preserves the disclosed possibility of brief host
contention from an initially unpinned diagnostic build; no game was discarded
or restarted because of that caveat.

The separate [same-tree audit](../../response-best-reply-r2-20261101/README.md)
finds substantial reliance on future modeled opponent mistakes in three
selected positions. That is a concrete reason to review the search objective,
not an explanation of every loss or a claim that a new design is already better.
