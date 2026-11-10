# Recovered replay cache

One 64-byte packed state per ply of each eligible distinct trajectory. The
builder uses the recovered move and listing snapshots from study 328. The
separate audit checks all states and exclusions with the C++ rules, including
full boards, visibility, special moves, termination and duplicate grouping.
A completed cache opens through `reconstructed_cache.Cache`.

[Plan](plan.json) · [Preflight](preflight.json) ·
[Fable handoff](../../../chatroom/336-astra-recovered-replay-cache.md).
