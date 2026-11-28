# Learning and intelligence status, 2026-11-28 12:36 UTC

Corpus: **291,831 games**. Latest game: 2026-11-28T10:16:06.929916262+00:00. Leaderboard snapshot: 2026-11-28T10:16:05.309507+00:00.

Coverage: last 24 hours include **157 of our games** and **3368 games solely between other teams**. Newest other-team game: 2026-11-28T10:16:06.929916+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 182 played-version/colour groups; previous report 2026-11-27T11:52:54 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v40; mapping unresolved: expected one release-map row for v40; found 0 | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 320 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **40**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

**Mapping update required:** expected one release-map row for v40; found 0.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [8qkr8jzx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8qkr8jzx): our v40 as white vs Strongly Invisible v42, 113 plies, King capturable.
- [axc1u1ma](https://www.mit.edu/~6.7980/fow/?tab=arena&game=axc1u1ma): our v40 as black vs IGM v4, 78 plies, King capturable.
- [n53w739m](https://www.mit.edu/~6.7980/fow/?tab=arena&game=n53w739m): our v40 as white vs Preface v10, 77 plies, King capturable.
- [xkpe9fl5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xkpe9fl5): our v40 as black vs Cross-Registered Players v2, 62 plies, King capturable.
- [p7wwnkel](https://www.mit.edu/~6.7980/fow/?tab=arena&game=p7wwnkel): our v40 as black vs Mist Opportunities v2, 76 plies, King capturable.
- [nw8pxfgj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nw8pxfgj): our v40 as white vs Magnus Monte Carlsen v4, 65 plies, King capturable.
- [zu5l3fjr](https://www.mit.edu/~6.7980/fow/?tab=arena&game=zu5l3fjr): our v40 as black vs Magnus Monte Carlsen v4, 64 plies, King capturable.
- [dplbkx0p](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dplbkx0p): our v40 as black vs Gravel Road v18, 76 plies, King capturable.
- [8xlw3kq2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8xlw3kq2): our v40 as white vs Gravel Road v18, 67 plies, King capturable.
- [k8exxh3u](https://www.mit.edu/~6.7980/fow/?tab=arena&game=k8exxh3u): our v40 as black vs Lost Signal v47, 98 plies, King capturable.
- [lu8ibb34](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lu8ibb34): our v40 as black vs Trojan Horse v15, 60 plies, King capturable.
- [nh69c88m](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nh69c88m): our v40 as black vs Farsight v45, 60 plies, King capturable.
- [xdo1d38a](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xdo1d38a): our v40 as white vs Farsight v45, 65 plies, King capturable.
- [3yr0ng3m](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3yr0ng3m): our v40 as white vs Cranberry Lemon v14, 143 plies, King capturable.
- [0w3ajrma](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0w3ajrma): our v40 as black vs Cranberry Lemon v14, 88 plies, King capturable.
- [pvt9n4ed](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pvt9n4ed): our v40 as white vs Cranberry Lemon v14, 79 plies, King capturable.
- [xrx8r787](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xrx8r787): our v40 as white vs Team 319 v3, 173 plies, King capturable.
- [owoqx0qj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=owoqx0qj): our v39 as black vs Cross-Registered Players v2, 76 plies, King capturable.
- [xqabtowx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xqabtowx): our v39 as black vs frog v4, 78 plies, King capturable.
- [7bdolwpe](https://www.mit.edu/~6.7980/fow/?tab=arena&game=7bdolwpe): our v39 as black vs Gravel Road v18, 72 plies, King capturable.
