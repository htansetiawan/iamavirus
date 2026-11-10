# Independent prospective cohort integrity audit

This verifies experiment295's existing selection contract. It is not a new
model, numerical gate, parameter variant or prediction result. The running
collector, frozen model weights, cutoff and300-game target are unchanged.

The prior independent score reviewer reconstructs eligibility using the
collector's helpers. Here a separate standard-library implementation reads
the captured API pages and raw source metadata/move sequences directly. It
checks complete cursor coverage, fixed filters, IDs, source hashes, listing
agreement, exact chronological order, all4,800old trajectory exclusions,
within-cohort deduplication, first-eligible prefix, owner deferral and final
selected mover plies. Mutable current-version labels are allowed to change;
historical played metadata must remain fixed.

API timestamps carry nanoseconds. Python datetime retains microseconds. A
synthetic counterexample shows that sorting tied truncated instants by ID can
reverse two timestamps998ns apart. This is a precision limitation, not proof
that the actual295cohort is wrong. The auditor preserves full RFC3339 precision
and requires agreement on the actual saved candidates. If an actual mismatch
appears, qualification stops: it cannot reselect games or change weights after
comparing model scores. The running code is not patched or restarted here.

All10tests pass, including timezone-equivalent instants, pre-epoch values,
submicrosecond ordering, cutoff/ID ties, incomplete pages, changed filters,
skipped earlier games, source corruption, duplicate training sequences,
sealed-cohort reconstruction, wrong mover plies and mutable versus historical
metadata. One earlier test-driver attempt failed with a misplaced fixture line
referring to another test's variable; its source/log and wrapper caveat remain
under attempt-01. The audit logic and production collector were unchanged by
that correction.

Actual tick0:100global rows, complete one-page coverage of the cutoff,
zero reference candidates/eligible games, no scores read or written. Exact
page ordering passes. A filled cohort is **not** verified yet. The next real
prefix should be independently audited after the07:35UTCtick, then the final
300must pass before probability scoring. This adds verification of the original
contract, not another predictive acceptance threshold.

Run after a completed tick:

```sh
.venv/bin/python astra-submissions/experiments/cohort-integrity-20261110/audit.py --out AUDIT.json
```

Before final scoring add `--require-sealed`. The script reads the last completed
tick from the atomically published execution state, avoiding partially written
page/tick/cohort files. It never imports Torch, a model or the collector helpers,
and performs no network request. Independent course-rules/observations and
scalar-likelihood review remain separate requirements after sealing.

[Tests](tests.stderr), [receipt](receipt.json), [initial live audit](tick000-audit.json).
No playing engine, GPU job, arena setting or release/version changed.


Later source-only audit: tick009 verifies196 eligible games /198 reference candidates /600 global listing rows, with2,493 immutable historical overlaps. No pending source, no NLL or model read, and the cohort is still not sealed. See tick009-audit.json.
