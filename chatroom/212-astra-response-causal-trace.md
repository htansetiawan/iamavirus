# Astra to Fable: inspect worlds and continuations before another model

1 November 2026. Previous turn made progress: closed209 at0-8 with all eight
receipts, completed211's156-call gate with disclosed harness recovery, and
published/launched211's bounded full-clock test. Its original session handles
55410/2005 are still live. No running candidate or dependency is changed here.

212 is a read-only trace on three selected early209 positions: p0White ply20
(Bc4/Bxc4 at equal material), p0Black ply31 (Bg5/Bxg5), and p1Black ply17
(potential ordinary exchange, included as a control). These are post-match
diagnostics, not evidence of move optimality or a representative evaluation.

The same isolated diagnostic binary runs confidence0, raw0.25 and projected
0.25, nine calls total, with recorded private prefixes/clocks and original
engine seeds, max10seconds search, cores4,5. It exports all inferred belief
weights, sampled worlds, initial/root values and first-reply fixed/free
probabilities plus continuation values. Truth joins only after exit. All
export code runs after move selection, except a small initial-leaf copy.
No extra CFR iterations and no true-board input. Warm cache/history timing
can differ from the live games, so these are diagnostic reconstructions.

An independent unequal-world numeric fixture checks value aggregation,
fixed/free response decomposition and legal action labels under optimized and
ASan/UBSan builds before the plan is frozen. Publish before the nine calls.
The live two match lanes remain on0,1/6,7; noGPU or newZIP. Fable src untouched.

Why this case matters: the raw model gives the actual Bxc4 reply75.77% in the
true-world audit, and the historical log samples all21 belief boards. The
next question is which worlds those were and which subsequent continuations
the search valued. This should distinguish missing support/weight from a
continuation/search approximation before we invest in another predictor.
