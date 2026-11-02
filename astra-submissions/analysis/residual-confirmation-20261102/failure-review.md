# Newer-game failure audit

These five cases were selected after results by largest increase in game-average log loss. They cannot be excluded or used to change the frozen gate.

Independent referee: 5 complete games / 521 frames; recorded outcomes and selected-position label perspectives agree.

| Game | Result | Plies | Increase in log loss | Final losing king | Attacker(s) |
|---|---|---:|---:|---|---|
| updro1eg | 0-1 | 149 | +0.81302 | g3 | r c3 (hidden after: True) |
| g9nruayl | 1-0 | 120 | +0.42817 | h8 | R f8 (hidden after: False) |
| svilkfzx | 0-1 | 65 | +0.30700 | g2 | r e2 (hidden after: True) |
| j0gka2zy | 0-1 | 81 | +0.29128 | e2 | r e8 (hidden after: True) |
| rjb46iar | 0-1 | 101 | +0.28070 | a5 | n c6 (hidden after: True) |

Post-hoc whole-game bootstrap of the newer cohort: mean +0.01298, 95% [-0.00820, +0.03635], 126 games. The failed point-estimate safeguard remains failed.

The largest error, updro1eg, is a real reversal, not a label-sign error. At ply 94 the White-to-move outcome probability rises from 0.984 to 0.997 under the residual; White ultimately loses. Late in the game White loses its remaining rook, and its bare king steps onto a hidden rook line at ply 149. The selected positions are far enough before the terminal event that the final trap alone is not a supervised explanation of their values.

Game outcomes depend on both continuation policies and their observation histories. These predictors see a board, current visibility masks, metadata, and the SF parent-child score; they do not see the players’ beliefs or continuation policies. This is a limitation of the target/input pair. The cases motivate investigating continuation-conditioned targets; they do not prove that doing so will improve play. No new fit or policy test follows this audit.
