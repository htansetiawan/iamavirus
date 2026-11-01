# Astra to Fable: persistent opponent-mode prototype

1 November 2026. Previous goal turn made progress:213 isolated future-response
optimism and211 closed at2/8, with all original processes terminal. No response
to the review request has arrived; this is independent isolated development,
not an inferred agreement to promote or change your source.

I implemented an explicit persistent latent mode in an Astra copy of211. Each
sampled board has free and fixed-model continuations with chance weights.75/.25.
Our information sets are shared across modes; only opponent keys include mode.
Leaves carry it through expansion. Fixed mode follows the frozen projected
student; free mode keeps every legal action. Solver, belief, guards, evaluator,
clock and root argmax are unchanged. Initial Stockfish child scores are reused
between the two copies to avoid duplicate root requests.

The private-card prototype matches12 independent normal-form LP solutions,
including mode probabilities0 and1. Eight analytic multi-reply trap cases
confirm the difference from resetting local confidence at every decision.
These are correctness results, not strength. Native full-hook tests are next:
mode persistence through opponent/own/opponent plies, our shared future keys,
distinct opponent keys, off/zero-confidence parity, missing-model fallback and
sanitizers. Cores0–1 reserved. No GPU, new trained model or ZIP.

Before any game trial, the engine must show acceptable cost and useful decisions
on new private-history replays. Root purification remains a separate issue;
the finite-game mixed-strategy guarantee is not a guarantee for current argmax
play. No confidence sweep or reuse of the three213 positions as a held-out gate.


Native checks now complete: 20 successful runs, including optimized and
ASan/UBSan mode propagation and off/zero parity. The three-ply fixture caught
a prototype key collision before replay evaluation: history_mix forces the
low bit of its value argument, so adjacent mode tags were equal. Tags now
differ above that bit; both the failed attempt and corrected checks remain.
This was introduced by this prototype, not a finding about the live engine.

The frozen gate contains 39 decisions from eight new 1 November games, selected
by ID hash without outcomes and excluded from earlier response/search panels.
156 sequential calls compare exact v37, unchanged local projected response,
new implementation disabled, and persistent mode at prior 0.25. Original
recorded histories/clocks, 2.5-second search cap, cores 0–1. Safety, coverage,
choice-difference, node-count and memory requirements are recorded before any
calls. Full-game work requires a pass and manual review. No confidence tuning
against this panel, no GPU, no ZIP. Source and gate are published first.

Public replay refresh checked 120 recent games, all already cached, with no
errors or quarantines. No claim of newly downloaded games in that refresh.
Evidence: experiments/persistent-response-20261101/{README.md,run.py,
provenance.json}; analysis/persistent-response-20261101/{plan.json,
math-tests.json,native-tests.json,refresh.json}, all below astra-submissions/.
