# 226: full-prior belief quality and runtime over whole games

The fixed-state 225 screen makes the stronger existing prior affordable on
three correlated captures. This gate asks whether using it from the start of
real observation histories improves the posterior without spending the saving.

Freeze 24 IAmAVirus games completed on 1 November before 20:00 UTC: four each
against Instructors, duck, HYPOTHERMIA, Greek Gift, Knight Vision and Strongly
Invisible. Select by fixed salted game-ID hash, without outcomes, and exclude
all 25 games in the fresh taxonomy diagnostic plus all 224 games. Both colours
are eligible; do not force a colour balance or choose cases by belief failure.
The selected window follows the recorded v37 model/history training export.
This development panel is disjoint from those named tests, not claimed unseen
by every previous project analysis.

Three arms, fixed cap 200,000 and two threads: original v37 with ordinary
10,000-world feature cutoff; the exact optimized 225 source with that cutoff;
the same optimized source with full features at all belief sizes. Coefficients,
history table and temperature 2 stay fixed. Reconstruct only our actual own
moves and observations for belief updates; true state is decoded after each
update for labels. Opponent moves are omitted from input. Validate replay
boards/views/legality with the course referee before freezing input traces.

Process every nonterminal recorded frame. No clock thinning, root search,
recovery after collapse, true-world insertion or fitted calibration is used.
After a collapse, count all remaining decisions as missing support. This
isolates the capped-filter question; real-clock decision/strength tests remain
necessary even after a pass. Matching truth means board/turn/castling/EP key,
not equality of private histories or repetition counters.

First require original versus optimized ordinary fingerprints, counts and
weights to agree after every update. Hashes include ordered world keys,
history hashes, float weight bits, halfmove counters and filter RNG/state.
This supplements 225's literal canonical-byte equality; it is a fingerprint
test, not serialization of every intermediate belief. No uncapped support
loss may occur. Technical/parity failures stop the run and retain all evidence.

Primary decisions are our turns after own move eight. Compare full with
ordinary on support retention and truth negative log share, with missing/zero
share floored at 1e-12. Report 1e-9 / 1e-15 sensitivity too. Use 2,000 fixed whole-
game bootstrap draws, stratified within the six opponent groups; never treat
plies as independent. To advance: support must not decline; mean NLL gain
>=0.15 nats with 95% lower bound > 0; at least six games must exercise the large-
belief regime; total full-update time <= 1.2× original ordinary; and full p95
update <= max(0.1 s, 1.5× original p95). All conditions are required.

This permits a separately frozen timed-decision candidate test, not a release
or immediate match batch. No thresholds, model or gate are tuned afterward.
One first execution per game/arm (72 calls), rotating arm order, cores 2–3,
3 GiB and 120 seconds per child, 45-minute total cap. No GPU. The 219 match trial is
unchanged. Publish source, plan and referee receipts before execution.
