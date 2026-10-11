# 046 — Astra: bounded tactical scheduler built, tested, rejected by pilot

C branch `astra/m4` now has opt-in threat-alias scheduling at
[8d6a969](https://github.com/htansetiawan/mist-c/commit/8d6a9691339ffc6c0a2a7ce0c79294e39622d380).
It uses a bounded hash index plus min-heap: future own-history aliases become
eligible together if any member has an attacked king. It changes expansion
order only and is **disabled by default**. Existing M4 suites and enabled
both-color/internal/Stockfish carry checks pass, as do enabled integration
address/undefined-behavior/leak sanitizers.

The 32-decision paired pilot **fails the predeclared screen**. At the two
forced-loss prevention seats, no net improvement: White 2/4 survives the
short horizon with either flag (Stockfish only), Black 0/4 (all e7f6, c1c8
refutes). Control d01 regresses from4/4 immediate survivals to2/4; s18 stays
2/4. Independent referee all-legal oracles distinguish immediate survival
from actually preventing forced loss. No failures, reported overruns or SF
request errors; all snapshots retained. Enabled runs really perform287–1535
priority expansions, with zero capacity drops. Paired beliefs agree.

Evidence and immutable source/input receipts:
`astra-submissions/analysis/m4-closure-20261011/README.md`, `decision.json`,
`pilot-final.json`, and both prevention oracles. Full logs are on Seagate.
No broad rerun or ZIP justified. Preserve default-off if reviewing this code.

Next diagnostic: export the selected move's continuation subtree and verify
whether the specific forcing reply remains unexpanded, is misvalued at a
frontier, or is correctly represented but accepted by the gadget. Priority
expansion counts alone cannot distinguish these. This should precede another
policy change. Completed gate/opening results are in045. No GPU service was
changed; the sequential pilot is terminal.
