# Fix the active-archive path in the intelligence report

The real arena-v38 release-map row links to Astra's canonical numbered ZIP
and separately mentions the uploaded name `v38-review.zip`. The reporter
looked only for backticked ZIP names, selected the alias, and searched for
it under `fable-submissions/`. Thus the November 11 status incorrectly said
the active archive could not be found.

The resolver now reads Markdown ZIP links and code spans in source order,
resolves the first canonical reference relative to the registry, and retains
its existing repository-boundary and SHA-256-prefix checks. A missing or bad
canonical target is not replaced by an existing alias. The registry is unchanged.

Four focused tests pass, including both existing mapping tests and two new
regressions covering bare/backticked link labels, conflicting existing aliases,
missing canonical files and linked paths outside the repository. Before the
fix, the new cases produced four expected failing subtests. Real v35, v37 and
v38 mappings now all verify. V38's archive, model-member and 359,889-record
history hashes match its immutable manifest; v35 still reports its separate
151,316-record reference table. No API ZIP-hash verification is claimed.

[Before](before.json) · [Expected regression failure](red.json) ·
[Validation](result.json) · [Reporter](../../tools/daily_intel_status.py) ·
[Tests](../../tools/test_intel_refresh.py).

The shared source fix affects future reporter invocations. Today's already
published status is preserved as historical evidence; it was generated before
the fix. No daily-service restart, report overwrite, replay mutation, fitting,
new engine, game, release number or website deployment is part of this change.
This is a reporting correction, not evidence of higher playing strength.
