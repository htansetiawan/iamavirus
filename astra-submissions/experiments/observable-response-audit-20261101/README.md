# Observable losing-response audit

1 November 2026. Read-only diagnosis while experiment 209 plays its frozen
full-clock games. No trained parameter, tested search binary or benchmark
dependency is changed by this work. No GPU.

Question: does the fixed visible-response student place substantial probability
on moves that an actor can prove lose its king from its permitted view? That
would make data-biased search expect avoidable blunders, even when overall
next-move likelihood improves. It is a model-fidelity question, not a reason
to alter the ongoing match results or automatically reject all exploitation.

Construct a sufficient observable proof for each already-legal candidate.
Apply the actor's move to its own known pieces and visible enemy pieces.
Test known pawn/knight/king attacks, and slider attacks only when every
intermediate square is known empty after that move. Unknown squares prevent
a slider proof; they are never assumed empty for the proof. Account for
castling, en passant, promotion, captured attackers, and terminal king captures.

Audit the first 100 validation games from the frozen note-208 manifest,
selected before reading their labels. Measure predicted probability mass on
proven-losing candidates, whether the recorded action is one, and whether any
unproven alternative exists. Verify every positive proof against independent
full-board native rules; test targeted edge cases under sanitizers. These
validation games have already been used for model selection, so results are
development diagnostics, not new held-out strength evidence. Within this
audit, true boards only check proofs after model inputs are constructed.

No probability correction or zero-probability mask is fitted or deployed here.
Some observed opponents may make even visibly fatal errors; actual frequencies
must be measured before asserting they never do. If the discrepancy is small,
stop this line. If large, retain it as a specified model-calibration question
for a separate experiment, while finishing the unchanged full-game pilot.
