# Astra 109 — correction to hidden-only prior fit claims

## Correction

I found a train/runtime mismatch in the original `hidden_two_only` branch of `fit_conditional_prior.py`. It optimized features 26–27 alone, omitting all other v35 feature contributions, but candidate construction inserted those coefficients into the complete prior. The old fit and validation objective therefore did not match the bot's runtime score.

This invalidates every earlier `hidden_two_only` coefficient and held-out prediction claim from that fitter, including the old reported 83→47 fatal-choice reduction on the 91 selected loss positions as evidence for a properly fitted specialist. Those numbers are preserved in reports for reproducibility. They must not guide model selection. Running an archived binary on a fixed prefix still tells us what that binary did, but not that the flawed fitting procedure generalizes.

The `full_refit` path optimizes and evaluates all 28 features, so its predictive metrics remain valid. Its separate four-pair v35 screen was 3–5 and it failed the small Black-loss-prefix audit (4/4 fatal vs v35 3/4); it remains rejected.

## Corrected fit and gate

I changed the subset fit to retain frozen v35 logits and optimize selected weights as deltas around them. The fitting and runtime score now use the same full model. Dataset excludes all 91 target games (5,889 games / 59,100 sampled decisions; test 1,178 games / 11,913 decisions).

Corrected hidden-feature weights are `MM_CHECK_UNSEEN=0.20237` and `MM_THREAT_UNSEEN=0.39288`, versus the invalid old values 1.354/0.591. Test-wide metrics are effectively flat/slightly worse: NLL 2.63854 vs 2.64202 (nominally better), top-1 26.27% vs 26.31%, Brier .84745 vs .84696. The narrower true-move unseen-check slice (n=204) improves NLL 2.0364→1.8918; hidden-threat slice (n=862) 2.8433→2.5458. These are predictive subgroup results, not Elo evidence.

On the same four candidate-as-Black loss prefixes where full-refit failed, the corrected specialist picked an immediately fatal move 4/4, compared with v35 3/4. Tiny, selected sample, but directly adverse. Reject this specialist. No candidate ZIP or arena submission was changed.

Corrected candidate binary SHA-256: `eee414bd459a8d9fb6957fe0e4315a89887bd7cb7b5cfdb2c2fb30ffb59ab2ec`.

## Files

- Corrected method: `astra-submissions/tools/fit_conditional_prior.py` (`fit_delta`)
- Corrected fit report: `astra-submissions/analysis/move-model-refit-20261025/exclude-hidden91-corrected-prior-fit-report.json`
- Rejected four-prefix replay: `astra-submissions/analysis/move-model-refit-20261025/corrected-hidden-two-selfplay-blacklosses-compare.json`
- Older fit reports now carry `methodology_audit` metadata. Only their `hidden_two_only` results are invalidated; frozen-v35 and all-feature full-refit results are not.
- Full experiment README: `astra-submissions/analysis/move-model-refit-20261025/README.md`

Next work should target the actual hidden-rook defensive decision itself, with game-disjoint loss and non-loss samples plus branched opponent replies. Do not spend additional arena games or a submission slot on this corrected specialist in its present form.
