# 253 — Exact CFR workspace and strategy-cache optimization

Implement the unmeasured third opportunity from note 161 on immutable v37:

* Reuse the existing strategy array and a persistent instantaneous-regret
  buffer rather than allocate/free two vectors each iteration.
* Recompute a player's strategy only after that player's regret update.
  Alternating updates use precisely the same pre-update strategy as before.
  Growth/pending initialization invalidates the cache; external current-strategy
  queries copy it only when valid. No direct regret mutations exist outside
  cfr.c in this v37 engine. External clients that write arrays directly would
  need an explicit invalidation; this is not an M4 API migration.
* Grow solver storage geometrically while retaining `finalized_slots` as the
  initialized logical length. New actions still have zero regrets and the
  same best-child pending initialization.

This changes no utilities, solver update, sampled world, guard, trained model,
iteration count per round, expansion rule or root selector. A faster timed
search can build a different tree; only a fixed expansion/iteration trace is
expected to produce identical results. The main traversal remains linear in
visited nodes. Storage growth becomes amortized linear in total slots rather
than worst-case repeated copying; this is not an order-of-magnitude claim.

Correctness first: bit-identical regret, prediction, weighted average and
current strategies against original v37 after every tested update. Cover
unequal chance, zero-probability branches, shared infosets, both player signs,
large action sets, changing terminal values, growing trees and pending changes
without growth. Optimized and host address/undefined/leak sanitizer checks.

Then measure repeated fixed-work solves on actual v37 search trees, with
alternating timing order and frozen starting arrays. No tree generation cost
is charged to one arm alone. A geometric-mean solver speedup of at least 1.20x
and no semantic mismatch earns an equal-clock search comparison. The latter
must show where the saved time goes; extra final iterations alone failed the
earlier frozen-tree audit. No synthetic timing is an Elo result.

No GPU or learned coefficients. Keep all code isolated under Astra; no new
ZIP, version reservation or deployment before a separate decision/game gate.
