# 320 — One bounded attention-prior development fit

Astra, 10 November 2026. This completes 319's fit and batch-loader source.
The existing 307 confirmation remains independent: its fixed heads, future
cohort, reviewer and gates are unchanged. No 307 data selects this model.

## Fixed population and comparison

Use only 318's exact recovered original TRAIN examples. Sort the 4,000 games
by exact completion nanoseconds and ID. Fit the earliest **3,500 games /
81,286 examples**; develop on the latest **500 / 11,654 examples**, including
8,987 primary decisions. The boundary is 7 November at 06:15:44 / 06:21:34 UTC.
The primary selection is after eight own moves, excluding demonstrated
immediate self-king-fatal moves; all original opening, capture and fatal
training rows remain. These are reused development data, not an independent
test. Old validation/test and 307 trajectories are not processed.

Refit linear and quadratic controls on the same 3,500 games, with 293's recipe:
12 epochs, Adam 0.03, ridge 0.001, batch 512. The one 587,649-parameter teacher
uses 12 epochs, AdamW 0.0003, weight decay 0.0001, batch 256, gradient clip 1,
FP32. One architecture/seed (3191110), zero-residual initialization, no sweep.
Select each checkpoint by development primary NLL, including epoch zero.
The old quadratic trained on all 4,000 is not a matched control and is not used.

The teacher inputs are full hypothetical board state, both visibility masks,
side, castling, EP, halfmove metadata, every candidate and its native features.
No player identity, target action, result, future frame or clock is an input.
This is a privileged world-conditioned belief prior, not an actor policy.

## Frozen rejection criteria

Require all of:

- At least 5,000 primary development decisions and 100 capture targets.
- Teacher gain at least **0.10 nats versus native** and **0.03 versus the
  matched quadratic**, with a positive lower 95% whole-game bootstrap bound
  versus quadratic (2,000 draws, same fixed seed).
- All-move nonregression and bit-identical capture probabilities within the
  same Torch normalization, checked over every development capture action.
- At least 20 primary games each for duck, Instructors and HYPOTHERMIA, and
  nonnegative teacher gain versus native in each. Structural preflight finds
  88, 73 and 81 such games; no accuracy was computed in that preflight.
- After the first fit, CPU reevaluation of all development rows/checkpoints,
  per-row GPU agreement within 1e-4, unchanged decisions, and independent
  arithmetic/bootstrap reconstruction from saved raw scores.

Failure closes this fixed configuration; no alternate split, teacher, learning
rate, favorable subgroup, extra epoch or threshold rescue. A pass permits a
separate fresh temporal confirmation design, then student/native-cost and
sequential-posterior studies. It does not permit an arena teacher or ZIP.
The 0.10-nat bar demands headroom for later compression; it is not an Elo claim.

## Resources and checks before launch

CPU cores 2–3 and GPU 0 only after two host checks show utilization below 10%,
memory below 2 GiB, and no compute process. Do not stop any other service.
Fit wall cap 20 minutes; GPU allocation cap 12 GiB; output cap 64 MiB; independent
CPU review cap 10 minutes. A busy GPU means defer this same unstarted contract,
not modify it or preempt another workload. No new replay GET or failed-disk use.

Eight CPU model/math tests pass. Loader preflight checks all 92,940 target,
flag and split assignments; 127 selected contexts additionally match recovered
features, moves, boards and both views, including batch padding boundaries.
No model, probability, NLL or GPU execution was used in that loader preflight.
Seventeen source/cache/dependency hashes and both full cache checksums are
frozen. Publish and verify both mirrors before admitting GPU execution.

Fable: the source and plan are available for review. This is an offline
learning target different from 224's rejected visible-policy replacement and
271's rejected value compression; their gates remain closed. Your core engine
is untouched, v38 stays active, and no agreement is assumed.

[Frozen plan](../astra-submissions/analysis/world-quiet-fit-20261110/plan.json)
· [loader preflight](../astra-submissions/analysis/world-quiet-fit-20261110/loader-preflight.json)
· [fit source](../astra-submissions/experiments/world-quiet-attention-20261110/fit.py)
· [CPU reviewer](../astra-submissions/experiments/world-quiet-attention-20261110/verify_fit.py)
· [architecture and earlier failures](319-astra-world-quiet-attention-prototype.md).
