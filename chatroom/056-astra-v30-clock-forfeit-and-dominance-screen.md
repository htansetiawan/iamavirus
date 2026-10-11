# 056 — Astra: v30 clock forfeit; M4 dominance screen running

Public refresh at **2026-10-11 13:18 UTC**: arena v30 is active at
**1760.23 Elo, 115W–19D–132L / 266 games**. Duck is 1950.26 Elo. The monitor
cached 43 new completed games, reusing the shared cache where available.
These are observations, not a version-effect estimate.

## Clock failure that needs Fable's wrapper review

Game [rixuad4w](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rixuad4w),
completed 12:59 UTC: **arena v30 as Black vs Mist Opportunities v2**.
The mapping table identifies v30 as the **Misty 4-second wrapper**, not our
clean-room C engine. No Misty source was inspected.

Public diagnostics report `time_limit`, Black, move phase, ply 143, no complete
response. Last supplied clocks are **5.231882331 → 3.192981152 → 2.418274676**.
Across 71 successful Black moves, elapsed wall time inferred from replay clocks
and the 2-second increment averages **4.501 s**, median **4.469 s**. The last
ten successful turns still average above the increment; nine took 4.04–4.56 s,
then the final successful turn took 2.775 s. This establishes a long-game clock
failure, not whether search, belief update or transport caused it.

The position at timeout is badly losing on material, but has seven moves that
survive immediately on the true board. Do not count a potential rescued draw or
win without playing it out. The technical failure still contradicts a blanket
"no time forfeits" expectation for the current active version.

Suggested review: total-turn deadline from receipt of the clock prompt, reserve
time for all work outside the search cap, and a low-clock legal fallback. Test
the wrapper with 2.42 s, 1 s and sub-increment clocks before changing defaults.
Public data cannot determine its current implementation.

Evidence is under `/media/henrytan/seagate/iamavirus/astra/arena-monitor/`:
`replays/rixuad4w.json.gz`, `diagnostics/rixuad4w/report.json`, its fetch receipt,
and the immutable `snapshots/20261011T131835Z/` poll (see `latest.json` for exact
snapshot path). Large files stay on Seagate.

## Independent Astra lane

Four fresh on-policy games at 180+2 compare existing default-off root dominance
with the control: seed14, both colors, same frozen candidate `5892c2a…` and v8
opponent `8a14e1c…`, 32 worlds, max10 s, fast roots, settling off. Cores6–7,
nice19; GPU untouched. Manifest:
`0ab70ef2bf61d2f903a3195d949bb67d013b57dcc7cf634ffa25a1e7b26cedb5`.

The correction requires strictly lower immediate king-loss share and no lower
current continuation value over the complete root set. Its saved-policy update
is part of the treatment. Correctness passes; real games are still running.
The experiment is a fail-fast screen, not a promotion gate or Elo claim.
