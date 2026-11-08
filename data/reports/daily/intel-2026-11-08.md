# Learning and intelligence status, 2026-11-08 08:51 UTC

Corpus: **213,896 games**. Latest game: 2026-11-08T08:39:31.244733369+00:00. Leaderboard snapshot: 2026-11-08T08:40:36.314233+00:00.

Coverage: last 24 hours include **316 of our games** and **0 games solely between other teams**. Newest other-team game: 2026-11-06T10:06:27.612759+00:00.

**Coverage warning:** the other-team feed is over 24 hours old or absent. Field-wide taxonomy is incomplete and must not be read as a current representative sample.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-02T11:41:55.130000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 96 played-version/colour groups; previous report 2026-11-02T11:42:35 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v37; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 257 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **37**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v37-mist-c-v14-allfit.zip`, SHA-256 `41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [ln9thqx2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ln9thqx2): our v37 as black vs Instructors v4, 158 plies, King capturable.
- [no8rg1ts](https://www.mit.edu/~6.7980/fow/?tab=arena&game=no8rg1ts): our v37 as black vs Mist Opportunities v2, 122 plies, King capturable.
- [jmz1luiz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jmz1luiz): our v37 as white vs Instructors v4, 79 plies, King capturable.
- [8lgui4rm](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8lgui4rm): our v37 as white vs Fogitos v3, 115 plies, King capturable.
- [fq7z4m9s](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fq7z4m9s): our v37 as black vs Knight Vision v36, 118 plies, King capturable.
- [bu6ua7xj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=bu6ua7xj): our v37 as black vs Foggy Fischer v4, 64 plies, King capturable.
- [jrwa24ai](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jrwa24ai): our v37 as white vs Mist Opportunities v2, 105 plies, King capturable.
- [gag6y4db](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gag6y4db): our v37 as black vs Mist Opportunities v2, 84 plies, King capturable.
- [j7nallfz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=j7nallfz): our v37 as black vs RATIRL v2, 52 plies, King capturable.
- [uzc10d6n](https://www.mit.edu/~6.7980/fow/?tab=arena&game=uzc10d6n): our v37 as black vs Fogitos v3, 110 plies, King capturable.
- [tmt3y0yl](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tmt3y0yl): our v37 as white vs Farsight v20, 53 plies, King capturable.
- [r5rm9yb2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=r5rm9yb2): our v37 as black vs Cranberry Lemon v10, 96 plies, King capturable.
- [0of28umc](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0of28umc): our v37 as white vs Greek Gift v25, 85 plies, King capturable.
- [7x6u4dtx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=7x6u4dtx): our v37 as black vs Greek Gift v25, 64 plies, King capturable.
- [6m6tzvbx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=6m6tzvbx): our v37 as black vs In Pawn Sight v10, 56 plies, King capturable.
- [1blnxl0y](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1blnxl0y): our v37 as black vs HYPOTHERMIA v4, 38 plies, King capturable.
- [jlcpivah](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jlcpivah): our v37 as white vs Greek Gift v25, 75 plies, King capturable.
- [qgc7ibf7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qgc7ibf7): our v37 as black vs Greek Gift v25, 64 plies, King capturable.
- [ur63agkc](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ur63agkc): our v37 as black vs RATIRL v2, 60 plies, King capturable.
- [llim0kk2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=llim0kk2): our v37 as black vs Mist Opportunities v2, 42 plies, King capturable.
