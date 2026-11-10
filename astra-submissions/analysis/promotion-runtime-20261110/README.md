# Promotion-ledger production build acceptance

2026-11-10T13:09:32.268951+00:00.310's complete promotion-ledger patch is now compiled into an
isolated copy of the production source, not merely the function probe.
Only `src/main.c` differs from the immutable v38 ZIP; its hash251cf64d7075
is exactly the helper-equivalent patch previously checked. All other source,
launcher/build scripts, Stockfish and history are unchanged. No Fable-owned
source, release ZIP or live arena setting was edited.

| Archived build path | Host13.3.0 build seconds | Opening protocol |
|---|---:|---|
| Actual packaged build.sh, GCC C11 |1.57|White and Black legal|
| G++ C front end, separate objects |1.58|White and Black legal|
| G++ C++20 permissive fallback |2.51|White and Black legal|

All six patched protocol processes and two parent controls exit0, return
`ready` then one legal move, load the unchanged Stockfish and leave no owned
worker. GCC choices match the parent in both opening fixtures, where no
promotion arithmetic applies. Longest whole protocol process0.57s locally.
Zero timed growth fixes20final CFR iterations; these are acceptance tests,
not full-clock play or a course-machine timing guarantee.310supplies the21
arithmetic fixtures;311supplies opportunity and real fixed-belief masks.
No new playing gate or candidate qualification follows. Original17448 exits0;
cores2–3 are released. Full logs, inputs, settings and binary/source hashes
are preserved. Host binaries stay local; no new version number is reserved.

[Acceptance result](../astra-submissions/analysis/promotion-runtime-20261110/result.json) ·
[local timing](../astra-submissions/analysis/promotion-runtime-20261110/local-build-timing.json) ·
[reproduction source](../astra-submissions/experiments/promotion-runtime-20261110/check.py) ·
[exact patch](../astra-submissions/experiments/promotion-ledger-20261110/promotion-ledger.patch.gz).
