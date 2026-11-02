# 248: Does the retired neural king predictor complement v37?

This is a bounded, frozen-predictor development screen, not a new network,
belief integration or strength test. Fable's old hybrid-era report found a
useful neural king-location prediction. It did not compare that predictor
with today's v37 belief. The two later v23/v25 archives contain identical CNN
observation graphs; use the v23 bytes and identify their exact hash, without
claiming they are identical to the earlier report's model.

Compare the v37 sharp king marginal, its flattened marginal, the archived CNN
king distribution, and a fixed geometric pool of sharp and CNN probabilities.
Normalize the CNN over hidden squares when the enemy king is unseen; when
visible, its location is known directly. The pooled distribution preserves
zero support in v37, so it cannot recover a discarded king location or a full
board. It is a diagnostic distribution, not a Bayesian update or a new guard.

Select 16 distinct v37 games, eight per colour, from the local 2 November
corpus after 05:28 UTC against the fixed nine reference opponents. Deduplicate
full move sequences and select by salted ID hash, without using outcomes,
king locations, likelihoods or taxonomy labels. One own seat per game. This is
a new comparison on the existing development corpus, not an untouched arena
strength test. Insufficient eligible games stops preparation without changing
the selection rule.

The collector receives only observations, own moves and clocks. It reports
king marginals at decision time without modifying the belief. Neural inference
uses the same permitted observations and own-move history. True boards are
joined only for offline scoring after the engine exits. Retain visible-king
controls, empty beliefs, missing king support, all phases and all outcomes.
Test both colour orientations and redacted-input invariance before collection.

Primary score: per-game mean hidden-king log loss, clipped at 1e-12; also
multiclass Brier, true-square mass, king-location support and phase breakdowns.
The fixed pool earns only a fresh confirmation proposal if it improves mean
log loss by at least 0.10 nat over both sharp and flattened baselines, has no
worse Brier than either, and improves log loss in the ply-30+ subset. Do not
select a new mixture coefficient or substitute standalone CNN performance
after seeing the result. Game bootstrap intervals are descriptive here.

CPU only, one core pair (0–1), at most 900 seconds total and 120 seconds per
game, no retries. No GPU, rollout search, model fit, large data copy, engine
default change, ZIP or release reservation. Instrumentation can influence
clock-based thinning, so report rebuilds/thinnings and do not claim exact
reproduction of the arena's original hidden memory.
