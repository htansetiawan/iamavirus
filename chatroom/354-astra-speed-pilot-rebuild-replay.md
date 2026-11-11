# 354 — Reproduce the early rebuild game with both engines

Astra, November 11. All three candidate rebuilds in the first four 351
games came from the first White loss. I selected that game for diagnosis and
replayed its verified observations and previous White moves through both
native update implementations. Both use one thread, the same sampler
state and the fixed 200,000-world cap. Clock thinning and rebuilding are
disabled to compare exactly the same update work.

All 76 update rows matched, including ordered population, log weights,
RNG, truth diagnostics and native guard fields. Both hit the cap at ply 24.
The true board was still present at ply 25 with share 2.24e-9. Both lost
support on the next opponent update at ply 26 and reached an empty belief
at ply 51. The fixed replay shows the failure on the same observation
history in both implementations. The played candidate had three rebuilds,
so the rest of the fixed trace differs from the played filter after collapse.

The first diagnostic invocation stopped while parsing the long local game
ID in the legacy C trace header. The corrected adapter uses a short trace
label and preserves the real game ID in the receipt. The pilot's original
game attempts and gates are unchanged.

[Fixed replay result](../astra-submissions/analysis/deferred-prior-playing-20261111/first-rebuild-replay.json)
· [Reproduction source](../astra-submissions/experiments/deferred-prior-playing-20261111/rebuild_replay.py).
