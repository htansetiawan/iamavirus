# M4 tactical information-set scheduling pilot

An opt-in search variant prioritizes expanding future own information-set
aliases when at least one sampled board has an attacked king. It changes
expansion order only: leaf values, terminal rules, gadget and final policy
selection are unchanged. A bounded hash index and heap avoid repeated tree
scans. See the C branch's `docs/M4_FRONTIER.md` for limits and complexity.

All M4 correctness suites pass. Enabled internal and real-Stockfish chess
integration checks pass in both colors with actual priority expansions and
blueprint carry-over. Enabled internal integration also passes address,
undefined-behavior and leak sanitizers (`sanitizers.txt`).

`pilot-plan.json` freezes the development cases and compute-screening rule
before examining the paired pilot's output. The 32 decisions run sequentially
on cores 6–7 at nice19, without GPU use. Full per-run source hashes, frozen
binaries, protocol outputs and receipts live on Seagate. These are deliberately
selected failure/control seats, not a held-out corpus or independent games.
No ZIP, on-policy strength claim, or arena activation follows from this pilot.

## Result: reject the enabled scheduler

Published C source: [8d6a969](https://github.com/htansetiawan/mist-c/commit/8d6a9691339ffc6c0a2a7ce0c79294e39622d380).
The feature remains disabled by default. All **32/32 decisions** validate,
retain snapshots, and report no M4 overrun or Stockfish request failure.
Paired belief fingerprints agree. Enabled runs perform **287–1,535** priority
expansions each; capacity drops are zero. This exercised the intended scheduler.

| Case / metric | Closure off | Closure on |
| --- | ---: | ---: |
| White prevention: avoid forced loss by next own turn | 2/4 | 2/4 |
| Black prevention: avoid forced loss by next own turn | 0/4 | 0/4 |
| d01 control: immediate survival | 4/4 | 2/4 |
| s18 control: immediate survival | 2/4 | 2/4 |

Each denominator combines two seeds and two evaluators. White's two surviving
prevention decisions use Stockfish with either flag setting; internal choices
still permit a forced loss. Every Black prevention decision chooses e7f6,
allowing c1c8. The new d01 losses occur at internal seed11 (b7b6) and Stockfish
seed12 (d5c4). These counterexamples fail the predeclared compute screen;
**do not launch a larger gate or release this enabled variant**.

The independent referee recomputed every legal candidate in both prevention
positions, including historical repetition. Merely surviving the current
move would have incorrectly counted all of those decisions as successes.
`decision.json` records the paired labels and checks; `pilot-final.json`
retains all receipts and manifests. Full logs remain at the frozen external
run path. These data were used for development, not held-out evaluation.

This result does not prove that the relevant forcing reply was expanded in
each sampled world. Counts alone cannot establish that. The next diagnostic
should inspect the chosen move's actual reply subtree, distinguishing an
unexpanded threat, a misvalued frontier, and a represented loss the gadget
still accepts. Do not respond by tuning the priority fraction on these seats.
