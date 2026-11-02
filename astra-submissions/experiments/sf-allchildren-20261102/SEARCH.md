# Equal-clock native search gate

Both 256-parent scorer gates pass. Freeze an actual native decision comparison
before considering matches. Only the Stockfish worker binary/flag changes;
mist-c belief, guards, leaf conversion, CFR, sampling and root selector remain
the v37 archive. No selective-solver optimization is combined into this test.

Two calls share one immutable belief, guard mask, sample seed and root action
set. Both get 2.5 seconds of search. Start fresh scorer processes before each
arm, excluding startup from the search budget, so neither inherits the other
arm's TT/history. Alternate first arm across the 51 previously used taxonomy
development decisions. Baseline selects the protocol output; both decisions
are scored afterward against the true board by the existing exchange probe.
An independent course-referee review and private-input audit are mandatory.

Preflight: both colors, fixed-work zero-time fallback search; with Stockfish,
same-scorer paired zero-time full expansion must match exactly; finally brief
changed-scorer calls must preserve worlds, exclusions, legal moves and budgets.
No truth is given to the actor. All first attempts, faults and timeouts remain.

Advancement requires >=20 exercised pairs, median node ratio >=1.15, no more
than one extra immediate fatal choice and two extra >=2-point material-loss
cases, zero illegal moves and technical failures, plus referee/input reviews.
These are reused diagnostics, not held-out strength evidence. The higher node
count can reflect a different tree as well as reduced evaluator cost.

A pass earns a separately frozen full-game pilot: 8 color pairs versus the
exact v37 archive at 180+2, at least 10/16 points before a Misty/opponent gate.
The pilot itself cannot establish arena superiority. No release number is
reserved and no arena action is taken. A failed decision gate closes this
candidate without threshold or scorer tuning on these cases.
