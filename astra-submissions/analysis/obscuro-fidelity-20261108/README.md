# Obscuro fidelity review and local-opponent repair

8 November 2026. See the [human review](../../obscuro-comparison-20261108.md).

| Receipt | Check | Result |
|---|---|---|
| adapter-audit.json | Frozen wrapper helper on all 29 recorded games, including the unanswered timeout turn | 398/1,158 incorrect action sets; course tracker 0/1,158 |
| adapter-integration.json | Corrected actual stdin loop with a spy policy returning the recorded move | 29 games, 1,157 completed turns pass |
| adapter-smoke.json | Installed Misty 0.1.3, profile v1.6, Rust required, two own turns in each color | Pass; startup below 0.56s, each turn below 0.084s; no faults, fallback or live child |
| review-manifest.json | Exact archive, source anchors, public-source provenance and local dependency hashes | Reproducibility metadata |

The helper audit gives the old adapter correct own castling rights, so it is an optimistic test of that helper. Extra/missing counts count affected turns, and overlap. The integration test uses hidden truth only as an external oracle; it is not sent to the adapter. The real smoke configures a 50ms search with two-second prompts; it does not test full-game clock behavior or playing strength.

Sources are in [experiments/obscuro-fidelity-20261108](../../experiments/obscuro-fidelity-20261108/). The three checks preserve first receipts with exclusive creation. Do not overwrite them to rerun. The original frozen adapter and all benchmark results are untouched. The new adapter depends on the course tracker; future runs must pin that source, the referee, package sources, native extension and Stockfish. A hash of an installed dependency is not a review of its implementation.

Brian Liou's Misty and Brian Hu Zhang's original Obscuro are different programs. No original-Obscuro executable was located or played. No new strength games were run in this review.
