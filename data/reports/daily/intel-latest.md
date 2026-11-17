# Learning and intelligence status, 2026-11-17 12:32 UTC

Corpus: **247,576 games**. Latest game: 2026-11-17T10:15:06.387666086+00:00. Leaderboard snapshot: 2026-11-17T10:15:07.686503+00:00.

Coverage: last 24 hours include **184 of our games** and **3286 games solely between other teams**. Newest other-team game: 2026-11-17T10:15:06.387666+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 136 played-version/colour groups; previous report 2026-11-16T13:03:34 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 265 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [k1s4df1e](https://www.mit.edu/~6.7980/fow/?tab=arena&game=k1s4df1e): our v38 as black vs Knight Vision v36, 68 plies, King capturable.
- [j30ds1ky](https://www.mit.edu/~6.7980/fow/?tab=arena&game=j30ds1ky): our v38 as white vs Knight Vision v36, 69 plies, King capturable.
- [a5b9pcyb](https://www.mit.edu/~6.7980/fow/?tab=arena&game=a5b9pcyb): our v38 as black vs Knight Vision v36, 96 plies, King capturable.
- [x7krz9y7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=x7krz9y7): our v38 as white vs Knight Vision v36, 89 plies, King capturable.
- [epsvff8l](https://www.mit.edu/~6.7980/fow/?tab=arena&game=epsvff8l): our v38 as white vs Cranberry Lemon v9, 79 plies, King capturable.
- [h59vcnte](https://www.mit.edu/~6.7980/fow/?tab=arena&game=h59vcnte): our v38 as black vs Cranberry Lemon v9, 44 plies, King capturable.
- [tx0wh9zu](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tx0wh9zu): our v38 as black vs Lost Signal v32, 168 plies, King capturable.
- [d42u2qjh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=d42u2qjh): our v38 as white vs Greek Gift v30, 101 plies, King capturable.
- [ysrf7il4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ysrf7il4): our v38 as black vs Greek Gift v30, 38 plies, King capturable.
- [4kpumfuu](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4kpumfuu): our v38 as white vs Fogitos v4, 139 plies, King capturable.
- [mot6yjcq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=mot6yjcq): our v38 as white vs Ex Republics v32, 69 plies, King capturable.
- [bw4ntzrb](https://www.mit.edu/~6.7980/fow/?tab=arena&game=bw4ntzrb): our v38 as black vs Ex Republics v32, 62 plies, King capturable.
- [3ubf2nzs](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3ubf2nzs): our v38 as white vs duck v11, 125 plies, King capturable.
- [3fi4ifdt](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3fi4ifdt): our v38 as black vs Resting Bishop Faces v8, 82 plies, King capturable.
- [xdfzw1mh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xdfzw1mh): our v38 as black vs duck v11, 94 plies, King capturable.
- [1fik50v0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1fik50v0): our v38 as black vs Fogitos v4, 80 plies, King capturable.
- [8o0dc7yj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8o0dc7yj): our v38 as white vs TUM v9, 79 plies, King capturable.
- [54jkjbuq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=54jkjbuq): our v38 as white vs TUM v9, 131 plies, King capturable.
- [e85mk41d](https://www.mit.edu/~6.7980/fow/?tab=arena&game=e85mk41d): our v38 as black vs Cross-Registered Players v2, 74 plies, King capturable.
- [96avkpq2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=96avkpq2): our v38 as white vs Decent Chess Bot v7, 81 plies, King capturable.
