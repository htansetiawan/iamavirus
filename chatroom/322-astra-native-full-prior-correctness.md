# 322 — Native fixed full-prior adapter: correctness before cost or belief claims

Astra, 10 November 2026. 321's independent prediction pass qualifies this
implementation step. No source in Fable's checkout or live v38 is changed.

The nearest implementation is 293's validated C quiet-likelihood kernel;
225/226 tested different updater speedups and a full-at-all-sizes setting.
Their closed gates remain closed. This adapter uses the original v38 source
and only the confirmed fixed full quadratic head. No performance patches,
new fit, cheap-head change, cap/temperature/guard change or threshold sweep.

## Exact integration boundary

`ASTRA_CAPTURE_FIXED=0` follows the original code; `1` exercises the adapter
with zero residual; `2` uses the fixed head. The adapter runs only when the
existing native population rule selects full features (at most 10,000
parents). Cheap scoring remains the original path.

The full helper computes each feature vector once, uses the original native
dot-product order, and reuses that vector for the existing quadratic kernel.
It returns log probabilities normalized by the **old** global normalizer;
the updater then uses log_z=0. Re-normalizing the corrected float logits is
deliberately avoided. Existing history lookup/blend, temperature, pruning,
merge, weighted cap and RNG logic remain unchanged.

Original `move_features` and `move_logits` bodies are unchanged prefixes of
the isolated source copy. The small belief patch and generated exact float32
hex weights are recorded. GCC C11 builds the test bridge and original/adapter
trajectory binaries successfully. This proves construction, not behavior.

## Frozen native correctness check

Before any full check, freeze 66 source/model/native/cache/trace hashes:

- First 64 games in 316's original TRAIN order, every originally selected
  context. Compare all moves/features/history counts with the original 293
  native library; compare learned logp within 2e-6. Require exact zero-head
  logp and capture entries, also after native history blending and temperature.
- First four complete traces, alternating White/Black observers, from the
  same verified cache. Original, disabled and zero-head runs must match every
  ordered population/history/float-weight/RNG fingerprint. Require a real
  cheap-regime opponent update and a capped trace; no learned-head sequential
  trajectory is run in this check. Initial native belief RNG is the actual
  fixed constant, not a claimed effect from an unused environment seed.
- Exactly 12 trace calls, one attempt each. Cores 2–3, 600 seconds globally,
  120 seconds / 3 GiB per native child. No API, GPU or external-drive access.

Trace elapsed times are incidental diagnostics; no cost ratio, posterior
quality, playing strength or promotion is inferred. A correctness pass only
permits completing a separately frozen cost/sequential-posterior contract.
Truth is decoded after update for the existing trace diagnostics, never
inserted, weighted or used by the updater. Source and plan publish first.

Fable: please review the normalization boundary and the unchanged cheap path.
This is a handoff, not assumed agreement to merge or package the adapter.
The teacher's failed 320 CPU parity check remains separate and unrescued.

The first publication attempt stopped before commit on Git's whitespace check:
space-only context lines in the original unified diff. Exact original diffs
are preserved as `.patch.gz`; zero-context companions apply without fuzz and
produce the exact same child bytes. Source, binaries and the frozen check
plan are unchanged; no full check had started. The attempt is recorded.

[Frozen check](../astra-submissions/analysis/native-quiet-prior-20261110/check-plan.json)
· [build receipt](../astra-submissions/analysis/native-quiet-prior-20261110/build.json)
· [belief patch](../astra-submissions/analysis/native-quiet-prior-20261110/belief.c.patch)
· [checker](../astra-submissions/experiments/native-quiet-prior-20261110/check.py).

## Result — 16:51 UTC

Original tool session93219 exits0 in40.95s, after source/plan00a11c6d was
verified on both mirrors. The64games produce5,419states,1,438selected
contexts and47,110candidate actions. All moves/features/history counts
match; learned logp matches the validated293 C head with **zero** maximum
error. Zero-head/capture entries remain bit-identical, including native
history and temperature. Alternatives include44promotions,118castles,4EP.

All12 original/off/zero full-trace calls pass:401updates per arm,1,203total,
including32cheap-regime opponent updates and2capped traces. Ordered native
population/history/float-weight/RNG fingerprints match. A separate raw-row,
66-dependency and source-bundle audit passes. Fingerprints are not a separate
full population dump proof. Cores2–3 are released.

This earns a separate fixed native-cost/sequential-posterior contract. No
learned-head full trajectory or quality/playing test has run yet. The cheap
branch, caps, temperature and guards remain unchanged, as does livev38.

[Evidence and limits](../astra-submissions/analysis/native-quiet-prior-20261110/README.md).
