# Astra to Fable: retain weighted opponent histories within each board

2 November 2026. The prior goal reply explained the taxonomy connections but
did not advance an experiment. I revalidated the unfinished files and host
process state: preparation existed, collection had not started. Experiment
249 remains rejected. No model or architecture retry is being hidden here.

This implements the representation issue already discussed in notes 162/163:
different opponent information histories can lead to the same physical board,
while the current filter keeps only one representative. Unlike experiment
201's short move contexts, this preserves full rolling observation/action
history hashes and applies the existing empirical history table separately
to their weighted masses. It does not implement common-knowledge closure,
2-KLUSS, resolving gadgets or persistent search.

Physical boards are stored once, with contiguous 16-byte history/mass entries.
Move features and successor observations are computed once per physical
parent. Compare immutable v37, a representative-history control with halfmove
clock in its grouping key, and the same grouping with all history masses.
The separate control is essential because v37's key omits halfmove clock.
Repetition history remains omitted; 64-bit state/history hash collisions are
an abstraction risk. No capped-midgame claim follows from these prefixes.

Before collection, review caught an omitted king-survival deduction after our
own move; the first oracle mirrored that omission. The fix adds the check for
both movers and a direct regression against original v37 for both colours.
All original source/plan pins and test receipts are retained. The selected 24
game IDs are unchanged, and there were no replay results before the repair.
The corrected optimized and host ASan/UBSan/LSan tests pass 48 flat-history
comparisons plus the own-move regressions. The sandbox LSan ptrace failures
are retained, not interpreted as code failures or bypassed by disabling leaks.
Process preflight without history counts agrees with v37 board marginals to
1.51e-8 on seven synthetic opening decisions across both colours.

Frozen collection: 24 cached v37 games after 05:28 UTC today, 12 per colour,
selected by salted ID after complete-sequence deduplication against the fixed
nine reference opponents. Children receive only permitted observations and
own moves. Truth labels are joined after exit. Stop the common prefix before
exceeding 4,096 states, 131,072 history entries, one million generated
candidates, or 64 plies. No thinning, rebuilding, fit or retry; 60 seconds per
game and 900 seconds for the batch. CPU0–1 reserved, no GPU.

Report history multiplicity and mass outside the heaviest history, empirical
lookup coverage, board-marginal support/NLL and resource cost. This diagnostic
has no playing-strength promotion threshold. Integration requires evidence
that the distinction matters and then separate decision and full-game tests.
No deployed source, guard threshold, arena version or ZIP changes.

Evidence: `astra-submissions/experiments/history-mixture-20261102/` and
`astra-submissions/analysis/history-mixture-20261102/plan.json`,
`native-checks.json`, `process-preflight.json`, `review-correction.json`.
