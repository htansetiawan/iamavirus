# 230: feasibility of training the transition posterior

This implements the bounded extraction in review proposal229. It is not a
model fit, playing candidate, or a continuation of rejected predictor228.

Select24 IAmAVirus games against nine reference teams,12 per colour, all
outcomes, by a fixed hash among games completed1 November10:00–20:00 UTC.
Exclude every game and complete sequence in228,226,224 and the fresh taxonomy
panel. No selection uses a tactical label or result.

Reconstruct the baseline from permitted observations and our own earlier
moves. Never send the actual hidden opponent move or truth to the belief
exporter. Stop a trajectory once its belief exceeds4,096 worlds, caps, or
empties. Export every opponent update with1–256 parents before that stop.
This measures an early/small-belief regime; it is not a middle-game coverage
claim. Full26-feature prior, original history table, temperature2. No pruning,
weight, guard, sample-count or model changes.

For each parent retain all legal actions for the softmax denominator, including
incompatible actions. Save the incoming weight, base logit,26 features,
history counts, consistency mask and successor grouping key. Then call the
unchanged native update and compare its merged posterior with the reconstructed
one. True labels are joined afterward from independently validated replay
states. No forced true board or appended positive, including in missing cases.

The production grouping key includes pieces,side,castling,EP and ignores
halfmove/history. Match that exact equivalence, verify equal keys have equal
included fields, and retain halfmove separately. This is not a claim that the
belief represents complete history-dependent game states.

Before extraction, synthetic tests must cover history-table gradients,
multiple parent worlds, duplicate positive histories, all-action normalization,
and rejection of missing positives. During extraction require exact successor
key sets and posterior probability agreement within5e-6, log probabilities
within5e-5. Finite-difference gradients on up to12 real nontrivial examples
must agree within2e-6. No optimizer or fitted parameter is used.

Report coverage of natural truth, nontrivial alternatives, different parent
worlds, merged histories, history-table hits, both colours, extraction time,
uncompressed bytes and saved bytes. At least100 multi-parent, multi-successor
natural-positive cases across at least12 games, correct gradients/parity and
no faults permit a separate training-plan review. Failing coverage closes this
sampling regime, not every posterior-learning method. The feasibility sample
is development evidence, never a held-out strength test.

Use cores2–3, no GPU,20-minute bound,256MiB total uncompressed case arrays.
Large arrays stay in ignored `build/data/`; track their hashes and all
reproducible source. External storage is read-only. Publish this plan before
the single extraction run. No retry, fit, ZIP or arena action is implied.
