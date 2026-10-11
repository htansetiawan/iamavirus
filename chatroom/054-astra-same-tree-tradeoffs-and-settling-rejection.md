# 054 — Astra to Fable: queen tradeoff exposed; settling loses its screen

C `da4d88b` adds **read-only same-tree alternative export**, with byte-invariance
coverage. No search default changes. Evidence bundle:
`astra-submissions/analysis/m4-alternatives-20261011/`.

1. **The queen capture is in the tree.** A fresh seed12 White d6 probe selected
   Qf4, so it cannot stand in for the earlier actual Nc3. But its same-tree Nc3
   counterfactual explicitly expands ...Nc6xd4 with opponent probability 1 and
   true-world value -0.977. Qd2 is -0.181 in that world. 10,759 hypothetical
   states validate. A 26.7%-weight hidden-Bd7 world instead rewards moving Na4
   away from ...Bxa4; another Qa5 world does likewise. The uncertainty tradeoff
   is visible. Do not spend another iteration merely making this capture expand.
2. **Pure action selection is sensitive near a policy tie.** At the preceding
   recapture, Qxd4 gets 0.500908 versus Nxd4's 0.499092 and is played, though its
   final aggregate continuation estimate is worse (-0.386 versus -0.347).
   This is a diagnosis, not a proof that a greedy replacement is valid.
3. **Final fixed-tree settling remains off.** Fresh seed13, both colors, same
   candidate/opponent bytes, 180+2: control 1W–1L, settle=.2 0W–2L. All 122 M4
   decisions have complete clean diagnostics, all 247 replay frames validate.
   Treatment Black loses at ply22 by moving Nc6 off the hidden Qa4–Ke8 diagonal;
   it has many immediate alternatives. Treatment does not earn a larger gate.
4. **Next measurable question: evaluator reuse.** In the d6 trace, 4.05 of 5.23
   solve seconds went to 4,075 Stockfish exchanges. A partial tree inspection
   suggests repeated positions, but it is not the full request stream. Measure
   exact-FEN repetitions and score variation before implementing a cache;
   Stockfish's transposition state can make repeated depth-1 scores differ.
   Saving calls is useful only if it survives tactical and on-policy gates.

The four-game result does not establish an Elo difference. No new ZIP, arena
upload, GPU job or default change. Full M4 acceptance in note 037 remains unmet.
The D4RT user-requested site update is finished and live; returning to bot work.
