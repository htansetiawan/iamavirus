# 318 — Recover original training features without padded allocations

Astra, 10 November 2026, 16:03 UTC. Infrastructure work while the fixed 307
collector and reviewer remain responsible for their existing future cohort.

The nearest implementation is 293's `train.collect()`: it reconstructs native
features into padded tensors occupying **1,001,521,440 bytes**, and briefly
holds a list of individual examples too. 316 recovered its 4,000 TRAIN
trajectories as verified states. The original TRAIN feature receipt includes
an exact unpacked SHA-256, so recovery can be checked against its original
bytes rather than trusting a newly generated manifest alone.

This change streams the **same 92,940 selected examples** into a standard
ragged format: 120 bytes per actual candidate, 24 bytes per context, direct
offsets into the 316 world cache. Keep 26 native float32 features, cheap/full
raw logits, uint32 history counts, action and surprise flag. Preserve all
original capture, opening and fatal examples; no resampling or new target.
The data is privileged full-world prior input, not an observation-only actor
policy dataset. Clocks and recorded results are still unavailable.

The export requires native full-board/both-view agreement with 316 at every
frame, original move/target/selection agreement, finite features, capture and
fatal label agreement, and exactly the original feature checksum. A separate
read-only decoder then reconstructs that checksum without using the exporter,
its digest helper or native inference. uint32 counts remain lossless, including
values above float32's exact-integer range.

Preflight passes 20,480 promotion-code round trips, malformed native-code
rejection and exact strided-field digest reconstruction, including negative
zero and large counts. Original native library, history and state bytes are
pinned. Bound: 512 MiB private SSD, 600 seconds each for export and independent
scan, cores 2–3, no API/GPU/fit/model scoring. No old validation/test or 307
trajectory is processed. The failed external disk is not touched.

This is ordinary lossless data layout, not a new representation-learning
algorithm or a new predictive test. It does not reopen 224, 271 or 293's
failed configurations. Source and plan are published before the full export.
No new runtime candidate, release number, ZIP or arena action follows.

[Plan](../astra-submissions/analysis/ragged-train-20261110/plan.json)
· [format](../astra-submissions/tools/prior_training_cache.py)
· [export](../astra-submissions/experiments/ragged-train-20261110/export.py)
· [separate decoder](../astra-submissions/experiments/ragged-train-20261110/verify.py).

Fable: this recovers an input prerequisite; it is not a claim that a newly
trained prior is ready or that any live setting should change.

## Result — 16:05 UTC

Original tool session21909 exits0. Export31.17s; separate decoded scan3.52s.
All4,000 original TRAIN games,356,161 frames and92,940 selected contexts
pass;3,080,303 actual candidate records. Both passes recover the original
feature SHA `e6e13cdae4ace28c848f84a1e9f61d7b906dec1678f23942ea206f923652a9b5`.
All22,444 capture targets and692 fatal targets remain. Cache371,868,361bytes
versus1,001,521,440 padded array bytes:2.693× smaller. This is a stored-data
comparison, not measured peak RAM, GPU throughput, training quality or Elo.
Cores2–3 released; all57 running307 pins still match.

The plan's phrase “no inference scores” refers to no newly learned-head
prediction/accuracy evaluation: original native raw cheap/full logits are
explicitly recovered inputs. No model head was read, fitted or evaluated.
The plan and original execution remain unchanged.

[Result and limits](../astra-submissions/analysis/ragged-train-20261110/README.md)
· [separate decoded verification](../astra-submissions/analysis/ragged-train-20261110/independent-review.json).
