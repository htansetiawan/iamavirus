# Original TRAIN feature recovery — complete

The original export and independent decoded scan pass on their first attempt
(tool session 21909, exit 0). Source/plan commit 6e8856e3 was verified on both
mirrors before execution. Cores 2–3 are released.

- 4,000 original TRAIN games, 356,161 native/cache-checked states.
- 92,940 original contexts; 3,080,303 actual candidate moves, maximum 92.
- All 22,444 capture targets and 692 immediate-self-king-fatal targets retained.
- Both passes reproduce original feature-stream SHA-256
  `e6e13cdae4ace28c848f84a1e9f61d7b906dec1678f23942ea206f923652a9b5`.
- Cache bytes 371,868,361, versus 1,001,521,440
  in the original padded arrays: 2.693× smaller, 62.87% reduction.
  These are stored-array sizes, not a peak-RAM, training-speed or Elo claim.
- Export stage 31.17 s; separate scan 3.52 s including process start.
- 20,480 promotion-code round trips and exact float32/uint32 byte checks pass.
- All 57 running307 dependency pins remain unchanged.

Private temporary files are under `data/astra-spool/ragged-train-20261110/`
on the checkout SSD; no binary dataset is added to Git. The pinned source
4000 TRAIN moves and native library make it reproducible. This stays within
the 512 MiB contract. The large external store remains unavailable.

Use `PriorCache.record(i)` for ragged candidates and their direct global
state-cache index. Features are privileged full-world opponent-prior inputs,
not actor-safe observations. `reconstructed_cache.actor_context` remains the
restricted actor path. No clocks or recorded results were reconstructed.

Wording clarification: the frozen plan's “no inference scores” means no new
learned-head prediction or accuracy evaluation. The existing native prior's
raw cheap/full logits are explicitly part of the recovered original inputs
and were computed by the original feature bridge, as the plan describes.
No quadratic/linear head was read or scored, and no model was fitted.

This is standard ragged storage, not learned compression. Old model tests
remain closed; no old validation/test or307 rows were processed, and no
model choice, GPU job, arena candidate, release number or ZIP is earned.
