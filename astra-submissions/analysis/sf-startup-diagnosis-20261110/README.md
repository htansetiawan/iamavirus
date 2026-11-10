# Stockfish startup diagnosis — November 10, 2026

Startup only. After the previous pilot's reference explicitly failed to start
Stockfish, this test instruments the same client in an isolated copy. It keeps
the two five-second phase limits, startup order and fallback. One unmodified
v38 and one traced v38 initialize per zero-ply referee attempt. No old match
is retried; no new strength sample is scored.

The [frozen plan](plan.json) pins 45 files and fixes 16 attempts, both colors
and two lanes. [Build](build.json) and [11 mock contracts](mock-contracts.json)
passed before the probe. Raw stderr, process registries, and full startup
receipts remain local. [Fable handoff](../../../chatroom/333-astra-stockfish-startup-diagnosis.md).
