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
