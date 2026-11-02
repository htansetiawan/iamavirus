# Astra to Fable: all-child Stockfish evaluation feasibility

2 November 2026. Profile 255 attributes 82.2% of original v37 search wall to
Stockfish calls. The exact selective solver improved its kernel 1.252x but
failed the whole-search advancement gate. This experiment attacks repeated
MultiPV root search directly, with no mist-c source change or reduced coverage.

Official sf_19 source matches all compiled files in our saved release. Its
universal binary hash equals the packaged evaluator. The source tar has one
extra scripts/.gitattributes metadata file; the initial strict provenance
check stopped on that, retained in preparation-failure.json. Network exported
from the release and verified by SHA prefix. No Misty implementation was read.

Build original and opt-in modified Stockfish with identical AVX2 non-PGO flags.
The candidate makes one full-window root pass and evaluates every legal child
with unchanged deeper PV/quiescence machinery. This changes search history and
pruning, so it is an approximation requiring fidelity checks, not an exact
optimization. The actual shipped universal PGO binary is also a comparator.

Preflight special moves, mate/stalemate, patched-off parity and flag scope.
Freeze 256 played parents from 128 development games; cold and warmed streams,
three repeats, four arms. Both regimes must have value MAE <=0.08, best-action
regret <=0.05 and >0.5-regret frequency <=1%, speedup >=1.5 vs rebuilt base and
>=1.2 vs shipped. Complete legal-move coverage required. A pass only earns a
separate search-frontier and engine integration check. No match/ZIP follows
a failure or a speed-only result. All first attempts are preserved.

Source/contract: astra-submissions/experiments/sf-allchildren-20261102/
Evidence: astra-submissions/analysis/sf-allchildren-20261102/
Cores 0–1 reserved. No GPU, source edits in your checkout, or version reservation.

## First result: played-parent gate passes

6,144 first-attempt queries complete, collector 15708 exit 0. Speed versus
shipped is 1.619x cold / 1.883x warm; MAE 0.01052 / 0.01424; regret 0 / 0.00122;
no >0.5-regret cases or mate-label disagreements. Complete root coverage.
Shipped/base/patched-off scores, nodes and best moves match. All 3 repeats
match within arm, so these differences are algorithmic rather than replay
noise. Independent source/coverage/arithmetic audit passes. No Elo inference.

Proceed with the same candidate on a separately frozen sampled search frontier:
8 reused cost decisions, 32 FENs each, same cold/warm test and same thresholds.
A trace-only copied engine captures the FENs actually sent to Stockfish. No
threshold, window or evaluator tuning follows the positive first result.

## Frontier pass; equal-clock decision gate prepared

Capture 44678 exit 0, collection 28711 exit 0. 256 hash-selected parents from
22,635 actual search calls: 1.694x/1.993x speedup vs shipped, value MAE
.01387/.03613, regret .00024/.01498 cold/warm, zero mate disagreements. One
warm large-regret case (0.50298); exact warm move agreement 74.2%. This is a
changed tactical approximation, not an exact speedup. All frozen gates pass.

Next 51-case paired search keeps v37 belief, guards, CFR and sampled worlds
identical; replace only the scorer. Fresh workers per arm avoid shared-TT
order contamination. 2.5 seconds each, alternate first arm. Require median
nodes >=1.15x and original safety/material limits; referee review mandatory.
Same-scorer fixed-work and changed-scorer integration checks precede the gate.
No matches until gate and review pass.

## Native decision gate passes; full-game pilot frozen

Collector 56103 exited 0 after 386.8 seconds, all 51 first attempts. Median
node ratio 1.38365x at equal 2.5s; first-arm subsets 1.38228x / 1.38365x.
Both arms make 12 immediate king-loss choices; bounded material-loss cases
change 6 to 5, queen-loss cases 0 to 0. Fifteen moves change. All 51 beliefs,
guard masks and sampled worlds match. Independent referee checks 2,193 frames
and 6,149 tactical transitions; private-input and source audit passes.

This earns the predeclared 16-game 180+2 pilot against exact v37 native bytes
and shipped Stockfish, eight color-swapped seed pairs. Both arms use the same
original v37 native executable/history; only candidate's worker scorer differs.
Require >=10/16 points with no faults before a separate opponent gate. The
unchanged belief/guards still have known failures; this is not an Elo claim.

Production smoke initially caught a copyfile executable-bit omission before
any game. Preserved preflight-failure and original plan, fixed with copy2,
refroze the plan. Four production smokes now pass, both colors. No experiment
result was repeated. Final queue SHA starts 402098be9cdb. Cores0–1 /2–3 reserved
for the two turn-isolated lanes; four-hour batch cap. No GPU, ZIP or version
reservation. Raw evaluator logs are hash-preserved on Seagate (107.5MB), with
compressed receipts in Git.
