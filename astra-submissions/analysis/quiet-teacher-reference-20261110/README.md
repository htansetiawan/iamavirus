# Explicit teacher inference conformance — 10 November 2026

**The corrected erf/math implementation passes numerical conformance with the
unchanged checkpoint.** This qualifies the inference implementation for a
separate held-out prediction design; it is not teacher quality or playing proof.
320's original failed inference gate and323's posterior failure remain closed.

Original session77001 exits0 once. Published source/plan `fb310e8925b00a31b7a58065382d4a626e7d58ac`
was verified on both mirrors before inference. Two idle GPU checks report
750MiB/0%/no compute apps; no service is stopped. The job runs18:13:55–18:15:48UTC
(112.70s, including independent review); GPU/core leases are released.

## Implementation and coverage

[reference.py](../../experiments/quiet-teacher-reference-20261110/reference.py)
spells out the original319architecture: functional MHA, explicit erf GELU FFNs,
math SDPA, same embeddings/norms/latents/queries/head and checkpoint keys. It
bypasses fused module inference **without toggling the global MHA flag**.
Highest FP32 precision, TF32/autocast disabled. The existing capture-preserving
normalizer and history blend are unchanged. No new representation or fit.

All81,286contexts from320's3,500fit-TRAIN games are evaluated twice at B256 and
B134:2,689,844valid candidate actions in each full pass.64fixed spanning contexts
are also evaluated singly with padding trimmed (2,186actions). No target action,
outcome, player identity or NLL/accuracy selection; no development/test/future
prediction. The unchanged epoch11checkpoint SHA remains
`ba468558fb0d266b2eb89dfc56cc4f5419ff762fa26cd408f303e277832c7542`.

| Frozen check | Observed maximum | Requirement |
| --- | ---: | ---: |
| CPU/GPU residual gap |4.380941e-6|<1e-4|
| CPU/GPU logp gap |4.768372e-6|<1e-4|
| Batch/padding residual gap |1.907349e-6|<1e-4|
| Batch/padding logp gap |1.907349e-6|<1e-4|
| Difference from324's390math/erf reference |0|<1e-4|
| Original grad-enabled FP64 function gap, first64 |0|<2e-11|

Capture log probabilities equal their same-backend baseline exactly for152,692
capture alternatives in each full pass and128in singletons. All valid outputs
are finite. Weights and global MHA flag are unchanged. Operation traces contain
math attention and separate GELU; fused encoder/nativeMHA/addmm-activation are
absent. Five earlier synthetic CPU contracts also pass.

Peak Torch GPU allocation103,484,416bytes (103.5MB). Measurement108.31s plus
setup/review; this is offline conformance throughput, not native arena cost.

## Independent audit and publication boundary

A separate decoder verifies20source/input pins, the exact81,286context traversal,
989local raw batch files,10,763,748scalar values per side, capture masks/identity,
all maxima and batch/padding comparisons. It does not reimplement attention or
repeat inference; FP64/operator checks come from the original execution.

146.1MB of numerical arrays and batch receipts remain under ignored`private/`.
Following324's automatic export rejection, those raw derived arrays are **not
published**. Code, plan, aggregate metrics, hashes, review and terminal receipts
are the repository materials. A local reviewer can reproduce the audit using
the retained private files; no authorization to export them is assumed.

## Next decision

Freeze a distinct held-out prediction contract for this corrected function with
the same weights and matched controls before collecting/scoring confirmation
inputs. Use new trajectories rather than320development or321/323data to claim
independent evidence. Do not silently use old fused-GPU scores as corrected
scores or change320's first-run failure. No fresh fit, student, native hook,
posterior test, ZIP, version reservation or arena change has occurred.

[Plan](plan.json) · [aggregate result](result.json) ·
[independent audit](independent-review.json) · [final decision](final-decision.json).
