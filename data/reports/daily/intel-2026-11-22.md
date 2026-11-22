# Learning and intelligence status, 2026-11-22 12:12 UTC

Corpus: **267,568 games**. Latest game: 2026-11-22T10:13:45.566459877+00:00. Leaderboard snapshot: 2026-11-22T10:14:14.004289+00:00.

Coverage: last 24 hours include **167 of our games** and **3558 games solely between other teams**. Newest other-team game: 2026-11-22T10:13:45.566459+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 170 played-version/colour groups; previous report 2026-11-21T11:54:28 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 277 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [cp0jv801](https://www.mit.edu/~6.7980/fow/?tab=arena&game=cp0jv801): our v38 as black vs Fogitos v7, 62 plies, King capturable.
- [d1yxp4ww](https://www.mit.edu/~6.7980/fow/?tab=arena&game=d1yxp4ww): our v38 as black vs Cranberry Lemon v10, 56 plies, King capturable.
- [g9sk7e18](https://www.mit.edu/~6.7980/fow/?tab=arena&game=g9sk7e18): our v38 as black vs TUM v10, 102 plies, King capturable.
- [k13ybemf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=k13ybemf): our v38 as white vs HYPOTHERMIA v21, 93 plies, King capturable.
- [99v1zs6s](https://www.mit.edu/~6.7980/fow/?tab=arena&game=99v1zs6s): our v38 as white vs Fogitos v7, 135 plies, King capturable.
- [h3wza8ne](https://www.mit.edu/~6.7980/fow/?tab=arena&game=h3wza8ne): our v38 as white vs duck v14, 51 plies, King capturable.
- [rg7lkl3y](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rg7lkl3y): our v38 as black vs Farsight v40, 128 plies, King capturable.
- [t4rf2xh5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=t4rf2xh5): our v38 as white vs Farsight v40, 71 plies, King capturable.
- [zvxk2tdv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=zvxk2tdv): our v38 as white vs HYPOTHERMIA v21, 73 plies, King capturable.
- [mv549udv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=mv549udv): our v38 as black vs HYPOTHERMIA v21, 64 plies, King capturable.
- [bjkcqszj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=bjkcqszj): our v38 as black vs Team 319 v3, 82 plies, King capturable.
- [udythges](https://www.mit.edu/~6.7980/fow/?tab=arena&game=udythges): our v38 as black vs Instructors v4, 110 plies, King capturable.
- [ykxq6l0c](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ykxq6l0c): our v38 as black vs Next v10, 108 plies, King capturable.
- [nazbh09u](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nazbh09u): our v38 as black vs Team 319 v3, 100 plies, King capturable.
- [tw6scy2y](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tw6scy2y): our v38 as white vs Team 319 v3, 87 plies, King capturable.
- [oylk9q9o](https://www.mit.edu/~6.7980/fow/?tab=arena&game=oylk9q9o): our v38 as white vs Foggy Fischer v10, 85 plies, King capturable.
- [v0id9pz4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=v0id9pz4): our v38 as black vs Foggy Fischer v10, 84 plies, King capturable.
- [hygdp8hj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hygdp8hj): our v38 as white vs Magnus Monte Carlsen v4, 69 plies, King capturable.
- [g2eb2ind](https://www.mit.edu/~6.7980/fow/?tab=arena&game=g2eb2ind): our v38 as white vs In Pawn Sight v14, 103 plies, King capturable.
- [yc8xlk0b](https://www.mit.edu/~6.7980/fow/?tab=arena&game=yc8xlk0b): our v38 as black vs In Pawn Sight v14, 92 plies, King capturable.
