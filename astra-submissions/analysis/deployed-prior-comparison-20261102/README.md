# Deployed-prior comparison

Prepared, not scored. The frozen plan selects 222 later opponent games and
retains 233 exclusions. It compares the existing actor-visible response model
with v37's actual full and cheap move priors, each using the same history table.
The main candidate is fixed in advance; taxonomy slices cannot select another
winner after the test. No fit, posterior integration, live engine change or
strength claim is part of this screen.

See the [design](../../experiments/deployed-prior-comparison-20261102/README.md),
`plan.json`, `preflight.json` and `build.log`. The native bridge uses the exact
v37 extraction under experiment221; all sources, binary, table and student
weights are hashed before execution. Build artifacts are local and ignored.
