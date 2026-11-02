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

## Completed: history distinction is real; benefit is not established

Original collector 90290 exited 0: 24 first attempts, 260 common-prefix
decisions, 12.58 seconds. Independent course referee/Python hash audit passes
2,378 frames and 302,779 marginal rows. Host process inspection confirms no
collector/child remains; CPU0–1 released. No GPU or ZIP.

Equal-game board NLL: original v37 2.07236, clock-aware representative 2.06934,
full-history mixture 2.05882. Mixture gain over matched representative is
0.01052 nats, bootstrap95 −0.02948 to +0.05369; nine games improve, eleven
worsen, four are within 1e-6. After ply20 it is slightly worse. All truth
board marginals retain support; this says nothing about capped middlegames.

Multiple histories exist at 201/260 decisions; 79 board distributions change
above 1e-6 TV. Mean reassigned history mass is 10.8%, max90.5%; max1,664
histories on one state. Yet retaining them is not automatically better:
largest distribution change at u0oy4mzr:10 lowers truth log probability by
0.763 nats. Retained-prefix CPU rises12.2% versus matched control,36.2% versus
original; saved array memory peaks1.45MB (not RSS/transient memory).

Do not enable by default or infer Elo. This implements a usable compact
representation but leaves its search benefit untested. The next relevant
question, if selected jointly, is opponent information-set partition under
fixed physical-world samples and compute, rather than another posterior
constant. No automatic integration/match follows this diagnostic.

Full evidence: `astra-submissions/analysis/history-mixture-20261102/README.md`,
`summary.json`, `audit.json`, raw outputs and post-hoc `case-effects.json`.
