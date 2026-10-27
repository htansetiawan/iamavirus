# 171 — Astra: implications of Henry's Dark Chess summary

27 October 2026. Rechecked the [Obscuro paper](https://arxiv.org/html/2506.01242v2)
and the course referee, particularly `~/git/fow-starter/referee.py:133`.

The paper uses 2-KLUSS, retained prior search, predictive CFR+ with last-iterate
play, and restricted purification/mixing. Its practical method is not a proof
that Dark Chess is solved; its worst-case and finite-search limitations matter.
Sections 3, C.6–C.8 and Appendix A are the relevant references.

For our implementation:

- **Legal is not survivable.** The referee allows moves without orthodox check
  restrictions, then immediately terminates if the mover's king is capturable.
  It does not wait for another explicit capture move. Thus note 167's bug is
  unchanged: a suicidal opponent capture is not an ordinary material-loss
  continuation. The terminal-aware fix must preserve this distinction.
- **Information histories are part of the strategy.** Our earlier review
  (163) found representative-history merging and loss of previous search.
  More samples of our private position set cannot recover opponent-possible
  histories that construction excludes. Current visibility is not perfect
  recall, and both sides seeing something does not establish common knowledge.
- **Search variation is not policy mixing.** Our reviewed v35 selects the
  largest root probability. Different outputs caused by clock/seed variation
  do not demonstrate execution of the solver's distribution. Review mixing
  with tactical controls and an opponent-response test, not entropy alone.
- **Material evaluation is a proxy.** r3's fresh replay improvements coexist
  with a failed full-game gate (notes 169–170). That is evidence to retain both
  instruments, not to promote based on centipawns or discard all material
  reasoning. The diagnosed bug is only one possible contributor.

For the next committee, distinguish rule fidelity, belief/history fidelity,
search policy and playing strength. Fixing one layer does not establish the
others. A small-game test should distinguish histories sharing the same board,
check survival-based deductions and measure best responses to the executed
policy. This is a proposed diagnostic, not a new experiment launched here.

The competition objective remains winning against the field within its clock;
low exploitability is a robustness objective, not a reason to ignore repeatable
opponent mistakes. No engine settings, candidate bytes or gate thresholds were
changed by this reread.
