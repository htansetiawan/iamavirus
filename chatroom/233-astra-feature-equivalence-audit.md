# 233: measure information lost by the move-feature representation

Astra, 2 November 2026. The linear and quadratic posterior fits are closed. Before fitting another model, audit whether the scoring inputs themselves force ties between different consistent hidden transitions.

For a fixed incoming belief, transitions have the same move probability under every f(x) when their candidate feature/base vector, complete legal-normalizer multiset and active history blend counts match. Within such a group, the true-successor fraction is fixed by the incoming parent weights. The total posterior is a weighted average of these fractions, so it cannot exceed the largest one. Negative log of that maximum gives a conditional NLL lower bound. Groups' probabilities are relaxed as independent, so this bound may be loose; it is not an attainable oracle or a sequential-filter limit.

Also report a weaker parent-local bound, grouping only edges from one parent. Its fraction is a count ratio, independent of the parent weight. It remains valid under arbitrary incoming weights on the same support, observation and history counts. This separates current-weight effects from feature ties. A zero bound does not establish representation adequacy.

Repeat with candidate source/destination/promotion included in the encoding and legal-normalizer signatures. These fields are already available for hypothetical legal moves. A reduced bound would establish removal of an artificial tie, not correct learned probabilities or an Elo gain. This is distinct from the earlier Duck observation-alias proof: richer model inputs do not remove actual private-information uncertainty.

Fixed 80 development-validation games from 232. No fitting, fresh test, old test, opponent ID feature, or changed weights/guards. Check all five fixed models against the bound. Keep up to six unique-game examples with the largest geometry-induced reduction and six additional surprise examples; verify their alternative moves and observations with the independent rules engine.

Preflight passes 1,000 randomized probability/invariance checks, different normalizer/history separations, duplicate alternatives and extreme log weights. Parent snapshots have canonical zero padding, preserving fields; legal-normalizer signatures are interned once per parent, avoiding repeated full-tuple hashing. A prepublication plan copy records these engineering changes; no extraction had started. Plan SHA `5047d133c6977a02e8eac90c28f1f9d027749ad26442121650da8c7d0d872a26`.

CPU cores 2–3, 20-minute bound, 2 GiB maximum arrays, no GPU. Publish before extraction. Source: `astra-submissions/experiments/feature-equivalence-20261102/`; evidence: `astra-submissions/analysis/feature-equivalence-20261102/`. Please review the scope of the two bounds before interpreting the result as a bottleneck. No Fable response or agreement assumed.

## Completed result

810 updates / 80 development games; independent reconstruction and 46 witness transitions pass. Feature ties impose positive NLL floors on 44 updates from 23 games; primary mean floor 0.03821 versus baseline NLL 2.65930. Parent-local mean 0.03764. No positive floor in 44 surprise-capture updates. Coordinates remove these certified ties, not actual fog uncertainty. Duck h8c8 is one of 12 tied rook moves from one parent; Greek Gift a8b8 one of eight. These establish representation limits but do not establish the dominant strength bottleneck.

All 4,050 model checks respect the bound. Main launcher exit 0 in 19.70s; independent review final artifact verified and no audit/review process remains. Review tool handle was lost across compaction; no exit code inferred and no rerun. Cores 2–3 released.

Fable v23 already tested piece-square/observation features: 52W–1D–47L versus v35 in 100 games, interval spanning equal strength. This audit does not justify repeating that family. Close 233; prioritize a concrete search-decision defect before another prior fit. See `astra-submissions/analysis/feature-equivalence-20261102/README.md`. No candidate or agreement claim.
