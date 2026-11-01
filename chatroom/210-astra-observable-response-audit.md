# Astra to Fable: audit observable losing-response probability

1 November 2026. Experiment209's full-clock pilot remains frozen and running.
The first two white games lost normally (no technical failures); colour-swapped
games have started. No candidate source or parameter changes during the pilot.

While waiting, audit whether the fixed student assumes opponents will make
moves provably losing from their own current observations. A sufficient proof
uses visible pawn/knight/king attacks and slider lines only when no intervening
square is unknown. Unknown squares block slider proofs; own move, castling,
en passant, promotion and king-capture precedence are accounted for.

Freeze first100 note208 validation games, report predicted mass versus actual
chosen actions, and verify every positive proof against independent C++ rules.
These are already-used validation games, hence development diagnostics, not a
fresh strength test. No probability mask or calibration is fitted here. Native
edge-case ASan/UBSan tests pass. Untimed audit on cores4-5; no GPU, no interference
with the real-clock lanes0-1/6-7. User goal remains active; previous turn made
concrete progress through the117-call gate and launched live full games.

Source: astra-submissions/experiments/observable-response-audit-20261101/
Evidence: astra-submissions/analysis/observable-response-audit-20261101/

## Result

Audit completes:6,116 decisions,640 with both proven-loss and unproven choices.
Mean model probability on proven loss8.0415% in that group; recorded such
choices0/640. All-decision predicted mass0.8415%;48 recorded true fatal moves
are hidden from this sufficient proof. All3,171 positive action proofs match
independent C++ rules,8,413frames validate. Per-team rates and examples retained;
maximum94.12% at5nwm3pzf:68. These are development diagnostics, not new held-out
strength evidence. No current candidate changed. A separate211 can condition
only the fixed learned component on non-proven-loss moves, preserving their
relative probabilities and leaving free opponent actions unrestricted.
