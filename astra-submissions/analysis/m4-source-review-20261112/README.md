# M4 source inventory and generic-core compatibility

Astra, 12 November UTC. This review distinguishes absent deployment from
already implemented, tested and rejected experimental configurations.
The human-readable [architecture and next-plan memo](../../../docs/m4-review-20261112.md)
is the primary reading packet.

## Inputs and result

- Experimental M4 commit: `a521bf8c14a1253c3effc87dae15e55de47b4e13`.
- Immutable v38 archive SHA256:
  `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
- The old M4 `cfr.c/h` differ from v38; v38 adds pending best-child
  initialization state and APIs. `fow.h`, `search.h` and `eval.h` match exactly.
  Belief and Stockfish headers have additional interfaces. Hash differences
  alone do not establish a source-incompatible API.
- Six original generic fixture sources from M4 were compiled unchanged with
  its `gadget.c/h` and `kluss.c/h`, but exact archived-v38 `cfr.c/h`.
  **All six compile and pass.** No `NDEBUG` flag was used.

Original session 26045 exits 0. The independent read-only reviewer verifies
22 pinned files, both archived core files, 12 compile/run receipts, source
identity and 132 assertion sites. The fixtures cover fixed gadgets, order-two
selection, adaptive controller arithmetic, full-cut Kuhn, two successive
captures and blueprint preparation. The count of assertion sites is not a
count of independent proofs or distinct game situations.

The Kuhn output includes a fixed-Resolve diagnostic gap during adaptive
solving. That number is not the adaptive controller's full-game exploitability.
No broader theorem is inferred from these fixtures.

## What remains outside this result

No chess frontend, position tracker, move selector, Stockfish client or game
was started. The existing fixtures do not exercise v38's new pending-start
paths, asynchronous evaluation or resource limits. The check does not port
the old chess adapter, reproduce the original Obscuro agent, validate a new
reference distribution or estimate playing strength.

Older on-policy carry tests and the repaired M4 four-game 0–4 screen remain
as recorded. The 250/251 history-only result and 292's failed forced-prefix
reference gate remain closed. A later current-engine design must address
those boundaries rather than describe the underlying components as new.

## Evidence

[Frozen plan](plan.json) · [Inventory and interface hashes](inventory.json) ·
[Raw compile/run records](commands.jsonl) · [Result](result.json) ·
[Independent review](review.json) ·
[Collector](../../experiments/m4-source-review-20261112/check.py) ·
[Read-only reviewer](../../experiments/m4-source-review-20261112/review.py).

Fable's repositories and the archive are read-only inputs. No core source,
model, GPU, candidate, numbered package, arena action, service or deployment
changed. Source inventory and component compatibility are review evidence;
the campaign's strength objective remains unachieved.
