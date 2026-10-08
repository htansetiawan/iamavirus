# Posterior expectation at the root

An isolated research experiment; no default or arena release changes. The
motivation is the [changed-choice audit](../../analysis/grouped-belief/choice-audit.md):
some known escapes reach the shortlist but lose to the final adversarial
comparison over hidden-board hypotheses.

| `FOW_ROOT_MODE` | Columns | Final selector |
| --- | --- | --- |
| 0, default | Existing representative plus strided population entries | Existing matrix regret matching |
| 1 | Posterior-distributed population entries | Existing matrix regret matching |
| 2 | Same sample as mode 1 | Highest mean payoff; uniform exact ties |

The primary comparison is mode 2 against mode 1. Mode 1 against mode 0 measures
the sampling change. All existing safety costs, shortlist rules, search depth
controls and belief updates are retained. Disabling `FOW_MATRIX_GAME` still
skips this entire stage; that setting is not the expectation control.

The resampled population encodes posterior mass in multiplicities. If it fits
the column budget, every entry is used. Otherwise, sample entry indices
uniformly with replacement. Identical boards are intentionally not deduplicated.
This makes the sample mean unbiased with respect to the represented posterior,
not with respect to the unknown true state. Eight samples can have high variance.
An independent seeded RNG leaves the belief and move-choice streams unchanged;
modes 1 and 2 use the same sample when driven through the same observations and
recorded own moves.

For row `a` and sampled boards `s[j]`, the new objective is
`Q(a) = sum_j payoff(a, s[j]) / K`. Full-population king-risk and other row
charges are already subtracted in each payoff and remain present after the
mean. This does not alter their prices, calibrate the belief, or resolve
strategy fusion inside the determinized alpha-beta searches. The old minimax
objective might still perform better with a misspecified posterior; testing
will decide.

`basis.json` pins the original root revision, Astra overlay revision and every
baseline source hash. The builder reconstructs this basis using Git, checks
all hashes, then applies only these four candidate source files. Root and
Fable sources are never written. Shared C++ objects are compiled once and
linked into the benchmark and test binaries.

```sh
taskset -c 2 python3 astra-submissions/tools/build_posterior_runtime.py \
  --output astra-submissions/build/NEW_DIRECTORY
```

`FOW_DEBUG_ROOT=1` records sampled indices, node counts and full-precision payoff rows for
paired diagnostics. It is off in the broader replay comparison.

`design.json` was written before the new selector results. First verify
analytical objectives, population mass, default parity, legal moves and equal
payoff inputs for modes 1/2. Then use the 453-game development set with three
frozen arms. A positive replay result still needs additional seeds, new
reserved games and complete clocked matches. No improvement is established yet.

The r2 build passes 129 focused checks and 622 original engine checks. Tests
run from the isolated build using the pinned historical `book.txt`; running
them against the evolving shared checkout originally caused two book-format
failures, recorded in the r1 receipt. The replay benchmark does not load a book.
Six control decisions match the previous runtime exactly. Modes 1/2 have
identical sampled indices, searched node counts and all 496 payoff cells on
the three diagnostic histories, with no clock fallback. They produce the same
three terminal choices, including one fatal choice; this check is not a safety
improvement. Receipts are in `../../analysis/posterior-root/`.

The three-arm 453-game development comparison is complete: modes 0/1/2 make
165/160/166 fatal choices over 432 terminal positions. All paired intervals
cross zero. [Full results](../../analysis/posterior-root/README.md) retain the
comparisons and the expanded default-parity check across all 1,338 decisions.
Keep mode 0; the new selector is not promoted.
