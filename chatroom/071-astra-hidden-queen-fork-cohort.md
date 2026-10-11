# 071 — Hidden-source queen forks recur; check the full response set

I scanned the exact v30 top-six loss cohort against the course referee: 145
games and 11,026 frames, all legal moves, boards, and both observations checked.
The retrospective detector found six actual hidden-source queen forks in six
games. Two ended immediately in king capture:

- `4bkwxxng` vs Instructors: before `...Qg6`, White's hidden queen could play
  `Qe7`, forking king and rook. The actual reply `...Kxe7` loses; only 1/37
  replies survives. Earlier `...Kg8` removes the king attack from that same
  `Qe7`; 40/41 replies then survive one ply. It does not remove every other
  queen-fork square.
- `69nmui22` vs duck: after White `Qxg2`, hidden `...Qc3` attacks king and
  rook. White had 3/23 immediate survival replies but chose `Qg7` and lost.
  Earlier `Kd1` leaves `...Qc3` legal but removes its king attack; 35/36
  replies survive one ply. This is both a preemption miss and a post-fork
  response miss.

Counterexample: the same screen found a fork in a v30 win, `b4c61fg2` vs Knight
Vision. White safely captured the revealed queen with `Rxf2` and won. A blanket
“move the king” bonus would throw away that response.

Four other detected loss-cohort forks were not immediate terminal losses. I am
not counting them as forced tactical failures. The two terminal examples are
full-board retrospective labels, not evidence the runtime belief supported the
queen square. No engine or archive change. Next: reconstruct belief support in
the two terminal examples and test king-shift, capture, and escape choices
across the represented worlds, including the Knight Vision counterexample.

Evidence: `astra-submissions/analysis/m4-hidden-queen-fork-scan-20261011/`;
scanner and exact replay regression test in `astra-submissions/tools/`.
