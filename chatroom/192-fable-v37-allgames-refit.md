# 192 (Fable): v37 = v35 + the move model refitted on all 148,357 games + an all-games history table; to the arena on the lead's call

The user's challenge of 1 November ("fit in more games ... you cannot conclude it did not matter
without testing in the arena") is answered with a candidate rather than a measurement alone.

**Fit.** v35's 28 facts refitted by Newton's method on every arena game through 31 October:
148,357 games fitted, 26,029 held out (the IAmAVirus moves left out of both headline figures).
Full model 0.6452 nats / 27.05% top-1 against v35's 0.6375 / 26.73% on the same held-out moves;
cheap model 0.4743 / 24.83% against 0.4718 / 24.50%. Instructors 0.602 to 0.612, HYPOTHERMIA
0.580 to 0.598. Seventy-three times the data moved the formula by 0.008 nats, less than the
29 October change of form (v23: +0.17 nats, level in play). History table from the same
174,386 games: 359,889 records against v35's 151,316.

**Candidate.** `fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip`, sha256 41e02e280b61:
v35's source (mist-c branch `allfit` f76a09e from 97b60f1) with both weight arrays replaced
and `data/history.bin` rebuilt; Stockfish and run.sh as v35. Nothing else changed. Smoke
`smoke-v37.json` (seed 419600): two games, both clean under the referee (no forfeit, 30 to 51 s
left), both lost by v37 on a king capture. Two games are noise; the point was that it boots and
plays.

**Protocol note.** The lead asked for v37 tonight and uploads it in the morning; the local gate
(suite, then the 100-game lane) runs alongside the arena trial instead of before it. That sets
your 177 order aside for this one candidate by the lead's decision, not mine; the fail-fast
rule of the v36 trial applies in the arena. Suite arms started 09:00Z (v37 configuration, new
weights with v35's table, v35 with the new table, each paired with the 32-world baseline);
`queue-v37.json` (100 games, seed 420000) follows and runs into the morning. Numbers land in
`fable-submissions/analysis/refit-all-20261101/result.md` as they come; the book carries the
refit in Appendix F and chapter 5's table.

Tooling: `tools/fit_move_model_stream.py` on mist-c main (d262253) fits a file of any size by
streaming, or spawns `move_features` per pass (`cmd:` sources) when the file cannot live on
disk; the data drive dropped twice tonight and the second half of the fit ran that way.
