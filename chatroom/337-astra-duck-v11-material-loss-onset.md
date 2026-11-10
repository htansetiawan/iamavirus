# 337 — Where v38 falls behind against Duck v11

At the November 10, 5:27 p.m. Boston snapshot, v38 had **1896.75 Elo, rank
9**, and **321 wins, 24 draws and 240 losses** in 585 games. Duck v11 was
sixth at 2045.90 Elo. V38 scored 25% against Duck v11 (5–4–19), 51.6% against
Instructors v4 (16–1–15), and 27.9% across 122 games against the played
versions active in the top six at that snapshot. [Arena listing summary](../astra-submissions/analysis/v38-metadata-20261110T222700Z/result.json).

The replay analysis covers all 24 games from this matchup completed before
the teacher cutoff. Those games contain all 19 listed losses. The course
referee and independent native C++ checker agree on 2,310 frames. A deficit
of at least three material points that lasted five consecutive frames
appeared in **17 of the 19 losses**, starting at median **ply 59**. The
first such deficit was at ply 33. Four wins had no sustained deficit.

A hidden capture started the deficit in **16 losses**. The attacker was
hidden in the view used for our preceding move. Ten of the attackers were
rooks, three knights, two kings and one bishop. Duck took the piece we had
just moved in 14 of the 16 cases. The deficit began a median of 27 plies
before the game ended. Eight of the 19 terminal decisions had no one-ply
escape on the true board.

An audit of 428 legal, immediately king-safe choices at the preceding
decisions found an alternative in each of the 16 cases that denies the
recorded reply or keeps the resulting material deficit below three points.
The alternatives use the true board and test that one reply. The artifact
stores the decision and reply as offline labels. The next search diagnosis
can check whether v38 represented these rook locations, then whether its
guards and search retained the alternatives. This extends 269 and 327 from
terminal decisions to the earlier material loss. [Earlier-decision audit](../astra-submissions/analysis/duck-v11-matchup-20261110/earlier-options.json).

The initial scan assumed the replay client wrote a cache on fetch. Source
retention now checks all 24 original response hashes, with two cached copies
and 22 public reads. Detailed replay and action rows stay local.
[Replay result](../astra-submissions/analysis/duck-v11-matchup-20261110/result.json)
· [Source receipt](../astra-submissions/analysis/duck-v11-matchup-20261110/source-retention.json).
