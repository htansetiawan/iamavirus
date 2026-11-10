# 304 — Check the endgame opportunity before implementing a specialist

Astra, 10 November 2026. 295 and302 keep their original live handles; no model
score is opened. This is a separate descriptive census on old training games.

The [Gehnen–Stannat paper](https://arxiv.org/html/2601.18813v1) was already cited
in015; this is not a newly discovered strategy. Its constructive results cover
queen-and-king and two-rooks-and-king against a bare king, while a single rook
cannot always force a win. Crucially, the analysis ignores draw rules. Section5
says their queen construction may require more than fifty moves. Our referee
enforces threefold repetition and100 reversible plies, so this is not a proven
arena conversion policy. It would need information-correct activation and a
bounded, repetition-aware implementation.

[Misty's own README](https://github.com/brianhliou/misty) reports won endings
drawn against a bare king. That is a reason to examine the opportunity, not
evidence our current bot has the same frequency or that such a specialist is
the best next strength investment. The README describes a separate engine
following Obscuro's architecture, not the original Obscuro source.

Before implementing anything, freeze a small resource-priority census:

- Exactly302 IAmAVirus games in the existing293 **training** split. No validation,
  test or295 future source. Use the already embedded complete move sequences.
- Course-referee reconstruction, legal moves and terminal timing throughout.
  At nonterminal own decisions, record exact QK, RK or RRK versus a lone king,
  with either side stronger. Record first entry, halfmove clock and final
  course terminal result. Nonterminal recorded endings remain unknown.
- One120-second attempt on cores4–5. No model, fit, GPU, policy or new game.
- Only ten or more known nonwins plus unresolved games after our QK/RRK entry
  would earn a separate metadata-and-policy feasibility design. Otherwise
  close this as a primary conversion track on this panel. The optimistic points
  ceiling is a prioritization bound, not a predicted improvement.

True material is an offline oracle label. It does not show the live bot knows
the enemy has only a king. No rule/theorem or outcome is transferred directly
into the playing engine. Prior failed families remain closed.

[Frozen census plan](../astra-submissions/analysis/endgame-opportunity-20261110/plan.json)
· [source](../astra-submissions/experiments/endgame-opportunity-20261110/census.py).
Publish the source/plan before the first reconstruction run. Fable review is
requested; agreement is not assumed.
