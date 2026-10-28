# 179 (Fable): oracle result, belief route

The oracle (v35's search on the true board, note 178) won every game: 23-0-0 against the
identical control and 24-0-0 against v35, both colours, no forfeit, every oracle decision at
|P| = 1 with no failure and no leak to the other side. The runner stopped at 47 of 80 games
when the root disk filled (not our files; 7.7 GB free now); the remaining 33 were relaunched
at 23:13Z and cannot change the reading. Full read-out:
`fable-submissions/analysis/oracle-20261028/result.md`.

Reading under the 170 rule: 1.00 against control (lower bound 0.88) means the belief is the
bottleneck. The route is belief work. The ceiling of a perfect belief with this search
against v35 is 1.00, above the 80% bar, so the search does not have to change to get there.

Caveat: one world bundles coverage with sharpness. The blunder audit says coverage is mostly
there (truth in the belief in 68 of 71 blunders, median share 0.06%), so sharpness is the gap.
Next from me: a sharpness curve (truth forced into the sampled belief at share 0.05, 0.2,
0.5; 20 games each vs v35, same harness) to set the target the opponent-model build must hit,
then the build. Astra: the split from 178 stands (frozen confirmation protocol and the
external-reference design are yours); please check the lower-bound arithmetic and say if you
want the curve's shares changed before it runs.
