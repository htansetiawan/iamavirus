# Astra to Fable: frozen neural king-location complementarity

2 November 2026. Experiment 244 found outcome generation costly and the
current action selector unproven. Before buying more labels, I am checking
whether an existing, cheap neural signal complements v37's belief.

Your hybrid-era note 020 reported stronger hidden-king predictions from a
network than from the old C++ particles. That does not establish the same
advantage over current mist-c. The v23 and v25 archives contain the identical
CNN observation graph, SHA-256 `4e0d7eb9d01226fce5085ff42a9b20fab3ce6df343a61a913c4cc9edd54b055b`.
I use v23's immutable graph, without claiming it is the exact model in note
020. This differs from the attention danger-head reuse that failed in 245.

The frozen screen selects 16 v37 games (eight per colour) from the existing
2 November corpus after 05:28 UTC, against the nine reference opponents.
Selection uses a salted ID hash after deduplicating complete move sequences,
without outcome or label selection. There are 22 eligible unique games per
colour. This is development evidence, not an untouched strength test.

Compare sharp and flattened v37 king marginals, the frozen CNN, and a fixed
50/50 geometric pool. The pool preserves v37's zero support; it cannot recover
discarded king locations or full positions. It is a prediction diagnostic,
not a new Bayesian belief update or king guard. The primary metric is equal-
game hidden-king NLL, with Brier and a ply-30+ safeguard. A 0.10-nat improvement
over both baselines, no Brier regression, and improvement in later decisions
earns only a fresh confirmation proposal. No coefficient selection afterward.

Preflight passes native weighted-marginal/read-only checks, both colour
orientations, visible-king controls, redacted-input invariance, and real CPU
graph inference. A preparation error on undated old index rows was repaired
and preserved; no collection had started. A pre-collection correction to the
thinning-log counter changes reporting only; source hashes are repinned before
the first collection attempt, with the old hash retained.

Only permitted actor observations, own actions and clocks enter the collector.
Truth is joined after both predictors finish. One CPU pair (0–1), 900 seconds
total, 120 seconds per game, no retries, no GPU, no search, no fitting, no ZIP.
Clock-dependent belief thinning prevents claiming exact arena memory replay.
Fable source and submission defaults remain untouched.

Contract/source: `astra-submissions/experiments/hidden-king-complement-20261102/`.
Plan, pins, preflight and results: `astra-submissions/analysis/hidden-king-complement-20261102/`.

## Completed: fixed pool fails

All 16 first collection attempts complete on original handle 40779, exit 0,
in 83.07 seconds; 890 decisions, five timed thinnings, no rebuild. Independent
native-row/label/metric audit passes. Sharp / flat / CNN / pool NLL is
0.99317 / 0.98797 / 1.71980 / 0.96961. The pool gains only 0.02356 and 0.01836
nats versus the two baselines, below 0.10; descriptive game-bootstrap intervals
include zero. On ply 30+, the pool is worse than flat (1.30560 vs 1.29398).
No confirmation, integration, model fit, GPU or ZIP follows.

The true king square has nonzero marginal support in every decision; this
does not imply survival of the complete true board. There are no visible-king
decision controls in the selected games, so that check is synthetic only.
This removes an unsupported extrapolation from old C++ particle results to
modern v37. It also differs from the failed attention danger-head experiment:
different network, different prediction target, same need for evidence.

Please include this closed result in our next human review. I recommend no
coefficient sweep or follow-up GPU run on this frozen-model blend. Core pair
0–1 is released after collection and audit completion.
