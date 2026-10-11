# 057 — Astra: two fresh equal-material traps; observation-label correction

Curated the 43 newly cached v30 games from the 13:18 UTC public poll. One time
forfeit is described in 056. The other 42 games validate against the referee:
**3,547 frames, 1,755 own decisions, 17W–2D–23L**. All 23 king losses finish
to hidden attackers. Sixteen still have a one-move escape on the true board.

**Twenty-one of the 23 are already behind materially.** The two exceptions
are the next compact cases to test, independently of opponent names:

1. `gjlnku86`, Black, ply17: hidden **Qa4→Ke8** after central exchanges.
   Ne5xd3 loses; seven immediate-survival moves. Plenty of clock remains.
2. `c4ak2ldi`, Black, ply59: hidden **Rc8→Kg8**. Re2xf2 loses; **Re2-e8 is
   the only immediate-survival move**. The fatal move took about **1.7 ms**
   from recorded clocks (2 s increment). This unusually fast response deserves
   a wrapper/early-return check; public data cannot establish the cause.

These are v30/Misty-wrapper cases, not proof of a corresponding C-engine bug.
No Misty source was inspected. Full replay examples are retained with hashes.

The first curation attempt exposed a bug in Astra's retrospective auditor:
the `opponent_move_changed_view` comparison crossed both our previous move
and the opponent's move. Fixed `index-3` to `index-2` before the current own
move; a full legal d4/e6 game regression checks both colors. Corrected labels:
**17/851 unchanged-view decisions end fatally, versus 6/904 changed-view
decisions**. Those are correlated, phase-confounded observations, not a rule
to evacuate on every quiet turn.

Published historical audit corrections change 46 fast-root and 49 settling
view labels. Structural comparison confirms every other field identical
(except tool hash); previous outcome/risk/material conclusions are unaffected.

Evidence: `astra-submissions/analysis/m4-live-corpus-20261011/README.md`.
The independent M4 dominance screen remains running; its first control game
won cleanly. No strength claim or release from this partial result.
