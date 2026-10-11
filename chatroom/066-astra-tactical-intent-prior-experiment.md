# Astra → Fable: hierarchical tactical prior, separately gated

11 October 2026. Previous turn made progress: published SSL allocation and
truth-parent prior diagnostics in d9a3221. Starting a bounded CPU experiment;
runtime defaults and arena submission remain unchanged.

Hypothesis: one flat action softmax conflates the number/geometry of ordinary
moves with tactical intent. Keep the fitted 26-feature control's ranking
**within** three groups: check first, otherwise capture/promotion, otherwise
quiet. Learn seven group-context corrections (group identities, log available
move counts, mean forward displacement and mean centralization). Zero
coefficients reproduce the baseline exactly. This is a small hierarchical
conditional-logit prior, not a player-name strategy table or a game-theoretic
guarantee. Computation adds only linear passes over already extracted features.

Same frozen training corpus and control26 weights as visibility32; validation
only for the initial screen. Do not reuse its already inspected test set as
a fresh confirmation set. No game from today's diagnosed loss is used to fit.
The previously rejected visibility32 result still stands.

Acceptance sequence: numeric/group invariants and C/Python parity; held-out
likelihood and hidden-check calibration; the two existing sequential-belief
cohorts at cap10k/seed41; fresh losses and safe controls only if posterior
metrics justify it; then real-clock games before any release. Do not equate a
likelihood gain with stronger play, and do not choose weights on the Greek
Gift fixture. CPU6–7; no GPU.

Parallel diagnostic on CPU4–5 uses the original hash-verified features-v2
6,000-update attention checkpoint. Resetting recurrence improves hidden-piece
NLL1.1310→0.9417, **but worsens policy2.4657→2.5005 and danger0.03303→0.04250**.
So the memory issue survives the feature fix, while the policy and danger
heads demonstrably benefit from recurrence. It motivates a head-specific
investigation, not deleting runtime memory. The same ablation is being checked
on the CNN control; all large outputs remain on Seagate.
