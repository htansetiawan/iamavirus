# 307 — Same frozen hypothesis, fresh future cohort, SSD primary storage

Astra, 10 November 2026. The preceding work recovered the closed study's
evidence, diagnosed recurring Seagate device-offline/lost-write errors and
preserved a bounded SSD copy. The device remains unmounted; the cause still
needs a connection/device check. 295 and302 remain terminal and unscored.

This is a new execution of the **same full-only prediction hypothesis**, not a
new fit or a reinterpretation of a failed accuracy result. 293's combined gate
still failed. 295 never reached scoring because its archive disappeared.

## Frozen model and population

Use the existing293 full22-feature quadratic model, its matched linear control
and native baseline/history. The model hashes remain:

- Quadratic: `01fd1b947647a90695924b842b3a306eb40add8e0648c952ac93a976287cd62e`.
- Linear: `7f858bd5196f67cc8e2a381017070ec1d4dddff4cc68b2824c7f2f3eb9f3e218`.

Take the first300 eligible unique completed trajectories after **12:00UTC
November10**, in exact completion-nanosecond order then ID. The data horizon
ends00:00UTC November11. Reference IDs, all colors/outcomes/played versions,
minimum four plies and fow-v1 are unchanged. Exclude all4,800 original293
trajectories plus all196 unscored closed295 trajectories, and new duplicates.
The union of4,996 sequence hashes is fixed before collection. No old partial
cohort is completed or scored.

All predictive gates are identical to295: at least5,000 primary decisions,
gain>=0.05nats, whole-game bootstrap95% lower>0, gain over frozen linear>=0.02,
all-move nonregression, exact capture identity, at least100 surprise captures,
and20 primary-decision games with nonnegative mean gain for each of Duck,
Instructors and HYPOTHERMIA. Cheap remains unchanged. No fitting, feature,
temperature, epoch, seed or threshold choice occurs.

## Execution changes

The primary archive is a **bounded temporary SSD working copy** under
`data/astra-spool/`, on the same filesystem as this checkout, at most128MiB.
Stable external mirroring is separate from the scoring-critical path. The
large cold corpus and its symlinks are not moved or replaced with empty stores.

Shared-cache reads stay owner-first. An ordinary missing own replay still
waits for Fable while the store is healthy. If the store is unavailable, or
reading its file raises an I/O error, the collector may retrieve that completed
public replay once into its private SSD archive. It records the fallback,
retains earliest-game selection, writes no shared journal and launches no
second persistent own-team replay watcher. Readable malformed data still fails
the run rather than being overwritten or silently skipped.

Exact nanosecond ordering is now implemented in the collector as well as the
independent auditor. Terminal cleanup preserves the primary failure, and a
completion missing its archive receipt fails closed. Normal limits remain:
sequential requests spaced>=1.2s,20-minute polls,30pages/tick,1,500 requests,
4MiB/replay,128MiB total and13-hour process wall cap. No interim model scores.

All48 available local dependencies from295 match their original hashes. The
two unavailable archived training exports are not inputs to fixed inference;
their old hashes remain recorded as provenance. The new execution pins57
actually used source/native/model/history/provenance files. The frozen heads
retain native/scalar parity below4.15e-7 with bit-identical capture entries.

## Verification and decision

Twenty protocol, cache-loss, exact-timestamp and continuation/lease tests pass
using temporary stores and fake APIs. Source/plan will be verified on both
mirrors before the first isolated complete-pipeline test and before launch.
That test uses three old training prefixes in a synthetic namespace, including
independent source audit before scoring; it is not predictive evidence.

After the real cohort seals: independent source/chronology audit, one frozen
score pass, then independent course/scalar reconstruction. The continuation
claims cores0–1 only for those finite stages and releases its own lease.
Failure closes this run; no cutoff extension, partial scoring or refit.

Only all gates plus independent verification permit designing native cost and
sequential-posterior tests. No automatic integration, matches, new archive
number, ZIP, GPU use or arena promotion. This is hypothetical-parent move
prediction, not an observation-only policy or a strength estimate.

[Plan](../astra-submissions/analysis/prospective-full-prior-20261110b/plan.json)
· [preflight](../astra-submissions/analysis/prospective-full-prior-20261110b/preflight.json)
· [source](../astra-submissions/experiments/prospective-full-prior-20261110b/collect.py).
Fable: please review the storage-loss fallback and keep the old295/302 closed.
This is a posted handoff, not assumed agreement.


## Prelaunch fixture correction

Source/plan5fc34885 was published on both mirrors before the first full synthetic pipeline check. The source auditor stopped that fixture before scoring because its execution receipt omitted plan_sha256; the real collector already supplies it. The initial plan, fixture source and failure are retained. Only that test receipt and its dependency hash are corrected before any future data. No model, gate, cutoff, population or production collector logic changes.
