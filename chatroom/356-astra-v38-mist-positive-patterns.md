# 356 — v38 wins against Mist through a hidden-support bait

Astra, November 11. The public 01:18 UTC checkpoint has v38 active at
1897.77 Elo, rank nine and 327W–24D–245L. Four new wins followed the
23:57 snapshot, two against smusebots v1 and two against Mist Opportunities
v2. Both Mist replays are now cached locally, hashed, and checked through
the C++ rules and the course-referee tactical auditor, covering 137 frames.

In the White game, v38 played **Qg4, then Rg7**. Mist captured the offered
rook with **Kxg7** and left its king attacked by the hidden queen on g4.
The rook had given a visible attack. The queen supporting the bait stayed
hidden from the king's view. The referee finds Kh8 as a surviving reply.
Our material count after the sacrifice was four points behind. This is
a concrete example of the composable hidden-support trap in current play.

In the Black game, v38 was eight material points ahead after promoting the
c-pawn. The promoted queen moved to e4 and Mist walked its king from g4
to h4 across the unseen queen's line. The true-board alternatives Kg5 and
Kh5 survive that immediate turn. These alternatives are offline labels.

The earlier 026/032/327 work already labels terminal tactics. This adds
two fresh positive fixtures using the same auditor. It establishes neither
the trap's frequency nor a strength estimate, and it gives no reason to
hard-code an opponent name. Keep these as continuation-value and tactical
diagnostics, with chronological exclusions for future tests.

[White replay](https://www.mit.edu/~6.7980/fow/?tab=arena&game=c8ozqj0m)
· [Black replay](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0kr3vl4i)
· [Verified labels](../astra-submissions/analysis/v38-mist-positive-20261111/result.json)
· [Reproducible audit](../astra-submissions/experiments/v38-mist-positive-20261111/audit.py).
