# Frozen neural king-location reuse: no advancement

2 November 2026. The fixed blend fails its predeclared screen. No integration,
new model, confirmation match, release number or ZIP follows from this test.

Sixteen v37 games (eight per colour), selected by salted ID hash after complete
move-sequence deduplication, supply 890 decisions. All enemy kings were hidden
at these decision points; visible-king behaviour is covered by the synthetic
preflight only. Selection uses the nine reference opponents and the existing
2 November corpus after 05:28 UTC. This is development evidence, not a fresh
arena-strength sample.

| Predictor | Hidden-king NLL, lower is better | Brier, lower is better | Mean probability on true square |
|---|---:|---:|---:|
| v37 sharp belief | 0.99317 | 0.45210 | 0.59780 |
| v37 flattened belief | 0.98797 | 0.43832 | 0.54950 |
| Frozen v23 CNN | 1.71980 | 0.65952 | 0.40892 |
| Fixed geometric pool | 0.96961 | 0.43749 | 0.59859 |

Scores average within each game, then equally across games. The pool's NLL
improvement is 0.02356 nats over sharp and 0.01836 over flat, below the required
0.10 over both. Descriptive whole-game bootstrap intervals span zero:
[-0.08643, 0.13892] and [-0.11207, 0.14337]. In the 650 decisions at ply 30 or
later, pooled NLL is 1.30560 versus sharp 1.33401 and flat 1.29398. It therefore
also fails the safeguard requiring improvement over the flattened belief.

The CNN does not reproduce the advantage reported against old hybrid-era
particles. Those were different beliefs, and we have not established that the
old report used this exact network. Here the v23/v25 observation graphs match
SHA-256 `4e0d7eb9d01226fce5085ff42a9b20fab3ce6df343a61a913c4cc9edd54b055b`.
The v37 source and history table come from ZIP `41e02e280b61`.

The true king square has nonzero sharp/flat marginal probability in all 890
decisions. This does **not** mean the complete true board survives, or that
hidden attackers are correctly weighted. King-location prediction is one
component; it cannot stand in for whole-belief quality or guard safety.
The geometric pool preserves v37 zero support by construction and is not an
independent likelihood factor or a justified Bayesian update.

All 16 first collection attempts complete on original handle 40779, exit 0,
in 83.07 seconds. No retry, GPU, search or model fitting occurs. The forced
histories contain five clock-based thinnings and no belief rebuilds. The
logger does not mutate positions, weights or RNG, but timed reconstruction
does not reproduce the arena's original hidden memory. Stockfish is unused.

Preflight verifies the native weighted-marginal calculation, both colour
orientations, known visible kings, redacted-input invariance and finite CPU
inference. The preparation failure on undated index metadata and a reporting-
counter correction are preserved; both precede the first collection attempt.
The separate audit reproduces all native rows, truth joins, fixed pooling,
equal-game scores and the failed gate. Full replay validity is checked with
the course-compatible referee after the predictors have finished.

Evidence: `plan.json`, `preflight.json`, `receipt.json`, `summary.json`,
`audit.json`, and `games/`. Implementation and frozen gate:
`../../experiments/hidden-king-complement-20261102/`.

This closes reuse of these frozen CNN bytes through this fixed king-location
pool. It does not reject learning stronger history-conditioned beliefs. The
next belief change needs a different mechanism and a demonstrated advantage
over the actual v37 baseline, including attacker support and probabilities.
