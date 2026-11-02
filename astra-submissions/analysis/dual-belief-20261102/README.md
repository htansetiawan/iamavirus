# Dual belief measures: implemented, diagnostic failed, no promotion

2 November 2026. **Do not enable this variant or launch its match gate.**
Separately accumulating the untempered measure differs mathematically from
taking a power of merged sharpened weights, but it predicts the true board
worse on this fixed development panel.

| Measurement | Existing power transform | Separate untempered measure |
|---|---:|---:|
| Equal-game true-board NLL, lower better | 2.14233 | 2.17856 |
| Mean per-decision action king-risk Brier | 0.00132859 | 0.00131639 |
| Mean per-decision action king-risk log loss | 0.00481323 | 0.00480789 |
| Immediately fatal actions excluded by combined guard | 69 | 69 |
| Actually king-safe actions excluded | 1,708 | 1,682 |

All **24 first attempts, 308 decisions** completed in **16.92 seconds**.
There are 10,231 candidate actions and 141,944 retained world rows. Seven
decision masks change, with no new decision that excludes every actually
king-safe action. The NLL gain is **−0.03622 nats**, descriptive whole-game
bootstrap 95% interval **[−0.06873, −0.00343]**; seven games improve and 17 worsen.
The predeclared minimum was +0.05. The other three diagnostic conditions pass,
but the joint advancement gate fails. Do not change that gate after observing
the result or claim the 26 fewer safe exclusions establish stronger play.

These are all view-legal action risks, not the deployed policy's chosen-action
distribution. “Safe” here means the true king survives immediately, not that
the move wins material or is good. All 69 fatal actions were already excluded
by the baseline, so this panel gives no new fatal-action repair opportunity.
Queen risk uses v37's existing predicate; no new claim of queen correctness.

## What changed

For a board reached by paths with masses 0.3 and 0.4, the untempered mass is
0.7. Squaring each path, adding, then taking a square root gives 0.5. A different
board with one 0.3 path retains mass 0.3 under both. Their normalized flatter
probabilities are therefore 0.700 versus 0.625 for the first board. The old
transform does not invert path tempering after merging.

The native implementation carries both measures through the same deployed
transition graph. Every retained step checks exact identity of board keys,
piece placements, clocks, representative histories and sharpened log-weights
against original v37. Both guard versions also report identical sharpened
king/queen risks. Search sampling, trained model and history counts do not
change. Production code adds an opt-in `MIST_DUAL_GUARD` switch; default off.
No full-game candidate or ZIP is released.

The second measure is still conditional on the model, retained support and
chosen representative history. Correct accumulation does not make the model
correct. Capping retains the existing selection bias; reconstruction resets
both measures. This diagnostic scores uncapped prefixes only and stops above
4,096 boards or 64 plies. These are the 24 reused experiment-250 games, but
there is no separate history-count limit, so more decisions fit here than in
250. Cross-experiment aggregate NLL comparisons are therefore inappropriate.

## Verification and provenance

- 97 native independent transition-oracle comparisons, maximum probability
  error 2.83e-7; both colours, temperatures 1/2, synthetic empirical histories,
  capped selection, threaded updates, shrinking, rebuild and empty filters.
  Host address/undefined/leak sanitizer runs pass the same checks.
- Independent course referee verifies 2,378 actual frames and both views.
  All 10,231 hypothetical true-position king-loss labels agree with the local
  rules reference. This does not independently recompute all hypothesis risks.
- Input privacy checks remove the true board, opponent views/moves and result
  before native filtering. Original hashes and return codes are retained.
- Collection handle **44357 exit 0**, audit **1777 exit 0**. A separate arithmetic
  review recomputes the aggregate result from saved cases. Host process audit
  finds no remaining experiment process; cores 0–1 are released.
- Original v37 rebuild SHA `14ac30b34999a6a667e4dcdfb1b4606b184dbacbdc2fcfdf7f6b257513543fcd`.
  Candidate SHA `c3747e6cf2ac4c11bca67946cf9580b62bfb367a08dc1ade4a1f2c8f55c0254d`.
  Preparation commit `0fb00eb7460f77b506c1d505d503ddd36e6af052` verified on both
  remotes before collection. Plan SHA `8d7bc1ebf65cf96509483823009c23d803c76eb32e1192f048603ea9377c6ff9`.

Retained filter CPU totals are 1.560 versus 1.555 seconds, including stopped
updates 3.002 versus 2.992 seconds. This single fixed-order, tiny timing panel
does not establish a speed gain or absence of runtime overhead.

The first publication attempt stopped at Git's whitespace check on blank
context lines of the generated unified diff, before commit/push or collection.
The diff is preserved losslessly as `candidate.patch.gz` with its raw hash.
No collection or model was restarted. There was no GPU work, coefficient
fit, threshold sweep, arena operation or new version reservation.
