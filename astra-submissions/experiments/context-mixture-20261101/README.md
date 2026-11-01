# Marginalize recent histories within each physical board

This isolated experiment stores one board plus a contiguous array of eight-byte
`(recent_context, log_mass)` entries. A context is the previous experiment's
25-bit recent opponent action, piece, capture and continuation information.
The physical-board cap is applied to the sum of its context masses. No context
is discarded within a retained board. Learned coefficients are unchanged.

For board B, context h and opponent move m, the transition mass is

`mass(B,h,m) = mass(B,h) * P_model(m | B,h)^temperature`.

Keep only successors consistent with our observation and the game continuing;
sum masses reaching identical `(next board, next context)`. The exponent is
applied **before** marginalizing histories, preserving the earlier tempered
model. At temperature 1 this is the usual Bayesian transition update. At 2 it
retains the live engine's heuristic sharpening, not a calibrated posterior.

The representation also avoids repeated expensive feature extraction. Score
static board features once per board, then add sparse temporal terms and
normalize over **all** legal moves for each context. For one parent and move,
the new context has at most two values: continued the previous piece or not.
Accumulate those two masses before emitting successors. Each generated
successor costs 24 bytes; reconstruct full boards only after the cap. Six
stable 16-bit radix passes sort board and context keys in linear passes;
adjacent duplicates merge by log-sum-exp. Weighted selection and its retained
mass semantics are inherited unchanged from the previous engine.

Limits: a small context is not the opponent's complete information history.
This diagnostic omits the empirical history table and search information-set
integration. It uses inherited 64-bit board hashes, which exclude halfmove
counts; it does not claim collision-free full-game-history identity. Empty
beliefs are not rebuilt. The implementation is single-threaded; the reference
may use two threads. Do not interpret this as a deployable engine replacement.

Validation before the new panel: independently enumerate full board/context
paths through multiple own and opponent moves; compare masses at temperatures
1 and 2 for both fitted models; verify the board cap keeps every context of a
retained board; compare static marginals to the original filter; check empty
updates and immutable truth probes. Run optimized and ASan/UBSan binaries.

Then run a private-input pilot through ply 16, with original and redacted
truth labels, before the three-arm panel. It must retain identical posterior
checksums and risks and finish each pilot under five seconds of update time.
The panel uses 18 new outcome-blind games, excluding all earlier experiment
games, with cap 20,000, temperature 2, seed 11012026 and at most 80 plies.
Controls: original static board merge, compressed static mixture, compressed
temporal mixture. Gate: temporal improves clipped truth NLL by >=0.1 nat
against both controls, support loss <=2 percentage points, common nonempty
king Brier rise <=0.002 and total update time <=2x. Show clip sensitivity and
empty-belief coverage. Limits: 120 seconds/arm, one hour overall, 512 MiB
address-space cap and RSS check. Positive results earn larger-clock/cap tests,
not a ZIP or an Elo claim. No tuning against the previous or this panel.
