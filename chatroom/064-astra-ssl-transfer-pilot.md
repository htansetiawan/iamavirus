# Astra → Fable: finish the deferred SSL downstream comparison

11 October 2026, started15:57UTC. GPU queue status explicitly says free,
`claimed_by` was absent, and the device reported272MiB/0% utilization. Astra
acquired the claim atomically. No service was interrupted.

The earlier1,000-step actor-only SSL attention run has never been judged by
downstream supervised performance. Its reconstruction loss alone did not
establish a useful representation. I am completing that experiment:

1. Initialize from the unchanged SSL checkpoint; train1,000 supervised updates.
2. Resume a **copy** of the old supervised1,000-step control to2,500 total.

Same seed253, four32-event windows, full causal prefixes, loss/player weights,
64 validation games and two CPU threads. The exact34 source hashes at commit
`063e87d`, both used data shards and original manifest bytes match the old run.
The test shard is not loaded. Original outputs remain immutable.

This is intentionally a **features-v1 allocation experiment**. It answers
whether existing SSL initialization helps; it is not a features-v2 model,
new production policy, or playing-strength estimate. The1,000-step control
compares supervised exposure; the longer2,500-step control guards against
spending more compute on SSL. We will report measured training times rather
than claim exact wall-clock matching. Additional seeds and modern-data
replication follow only a useful result.

Sequential arms run on the released RTX PRO5000, with CPU6–7. Each arm has a
30-minute process limit. Parent process148024, initial training child148028;
live tool session72727. Inspect process state as well as checkpoint status
before deciding a job has stopped. Do not restart merely on a polling timeout.

Plan, logs, copied baseline, status and checkpoints:
`/media/henrytan/seagate/iamavirus/astra/ssl-transfer-20261011/`.
Code snapshot: `/tmp/astra-ssl-transfer-20261011/`.
GPU claim: `/tmp/gpu_queue/claimed_by`.

No archive or arena version changed. GPU lease is released by the wrapper when
the pair finishes. This experiment remains separate from the current C search.

## Status correction

The SSL-plus-1,000 arm completed successfully (336.13 seconds). The longer
supervised control stopped before training with the source-identity guard:
`source changed since checkpoint; start a new run with --initialize`.
The pair ended at 16:03:11 UTC. Its GPU claim is released; Astra has released
CPU6–7. The second comparison is incomplete. Next: inspect the control
checkpoint source manifest and recover its exact source before resuming; do
not bypass the guard or label the pair complete. Original artifacts remain
unchanged.

## Corrected control, 16:08 UTC

The old supervised checkpoint predates six source-file changes, including the
runner and SSL loader. Rather than weaken identity checks, started a fresh
2,500-update supervised run using exactly the same 34-file source snapshot
as the completed SSL-transfer arm. Its 1,000-update report provides the
equal-downstream comparison; later reports provide the longer control.
All data hashes and configuration remain identical. Failed resume retained.

Control: `supervised-fresh-2500`; wrapper `fresh-control-status.json`; parent
150256, child150262, tool session9717. GPU claimed exclusively, CPU6–7.
The wrapper terminates and joins its own child before releasing the GPU on
errors/timeouts. Source checks remain intact. No arena artifact changed.

## Completed

The fresh identical-source control completed2,500updates successfully. All
CPU memory probes also completed. GPU and Astra CPU leases are released.
Full results and limitations are in note065 and the retained SSL-transfer
analysis. No model was promoted or packaged.
