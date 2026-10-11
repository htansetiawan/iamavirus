# 044 — Astra: duck's opening defeats a late safety rule; defend one turn earlier

The two arena-v30 losses `9pl31sez` and `burzt1so` end identically:
`1.e4 d5 2.exd5 Qxd5 3.d4 Qa5 4.Be3??`. I verified the cached full boards,
both sides' observations, legal moves and outcome with the official referee.
They share one observation/own-action history, not two distinct test cases.

**The important result:** from the recorded position after d4, eight legal
queen moves generate the same White observation. Qa5's seven safe White
replies are disjoint from Qe4/Qe6's five safe replies. Each true board has an
escape, but there is no single response that safely covers the observation.
A pure per-world leaf evaluation can miss this information conflict. Even
a randomized response loses with probability at least1/2 against one member
of the disjoint pair under worst-case choice; this is not an opponent frequency.

Blind minimum-risk counts are insufficient too: Be3 survives7/8 of this
subset, Nc3 only6/8. We must not equate enumeration counts with duck's policy.
The queen vacating d5 changes the view, while its destination stays hidden.

I enumerated **all29 earlier White moves** and all Black replies, grouping
future states by White's view before intersecting their escape sets. Only
d3/d4 have information conflicts here; Ke2 permits a physical forced loss.
The other26 moves have common safe responses at this short horizon from
this starting board. Nc3/Be2 are concrete developmental alternatives.
This explains what to model earlier; it is not a claim that every one of
those26 moves is a good opening or safe on every posterior board.

**Foundational C code is ready for review**, separate from your main and the
currently running M4 executable:

- mist-c `astra/m4` commit **9fb3d30**: `m4escape.c/.h`, a bounded hash/index
  with exact observation/history/own-rights keys and sorted escape intersections.
- Unit tests, color reflection and ASan/UBSan/LSan pass.
- C matches the official Python referee on **1,307 successor boards /
  537 observation groups / 29 candidates**. No GPU, model or SF needed.
- Not linked into search; no new ZIP. Missing groups/historical repetitions
  remain explicit caller responsibilities.

Proposed use: prioritize expansion of future infosets whose individually
plausible escape plans conflict; alternatively supervise a learned history
representation with those conflict labels. This is a composable tactical
pattern, not a player-name strategy. Both approaches must use belief/search
states at runtime, with truth only in offline labels.

I fetched the complete public protocol for the canonical game and queued
16 cold/warm target decisions (our third/fourth move, both evaluators and two
seeds) **after** the broad time-budget gate. They use the unchanged a97a1d5
engine, reserved6–7 atnice19, and must test whether our current planner already
avoids this earlier. The dependent waiter confirmed live PID60221 at08:44UTC.

[Evidence and reproducible tools](../astra-submissions/analysis/duck-opening-alias-20261011/README.md).
