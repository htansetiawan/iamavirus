# Learning and intelligence status, 2026-11-11 10:48 UTC

Corpus: **234,911 games**. Latest game: 2026-11-11T10:05:41.161763235+00:00. Leaderboard snapshot: 2026-11-11T10:05:43.765897+00:00.

Coverage: last 24 hours include **212 of our games** and **3986 games solely between other teams**. Newest other-team game: 2026-11-11T10:05:41.161763+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-02T11:41:55.130000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 180 played-version/colour groups; previous report 2026-11-09T22:03:15 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; mapping unresolved: [Errno 2] No such file or directory: '/home/henrytan/git/iamavirus/fable-submissions/v38-review.zip' | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 322 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

**Mapping update required:** [Errno 2] No such file or directory: '/home/henrytan/git/iamavirus/fable-submissions/v38-review.zip'.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [dscy73os](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dscy73os): our v38 as white vs Knight Vision v36, 119 plies, King capturable.
- [lhqh5z0m](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lhqh5z0m): our v38 as black vs Farsight v29, 98 plies, King capturable.
- [j1u78roe](https://www.mit.edu/~6.7980/fow/?tab=arena&game=j1u78roe): our v38 as black vs Knight Vision v36, 20 plies, King capturable.
- [l39sy2qd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=l39sy2qd): our v38 as black vs Knight Vision v36, 148 plies, King capturable.
- [gf0gu7ag](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gf0gu7ag): our v38 as black vs Greek Gift v25, 62 plies, King capturable.
- [wlbuiqnk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wlbuiqnk): our v38 as white vs Gravel Road v5, 73 plies, King capturable.
- [8axgi4hr](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8axgi4hr): our v38 as black vs Gravel Road v5, 76 plies, King capturable.
- [d6abefly](https://www.mit.edu/~6.7980/fow/?tab=arena&game=d6abefly): our v38 as black vs Knight Vision v36, 72 plies, King capturable.
- [y6kudg61](https://www.mit.edu/~6.7980/fow/?tab=arena&game=y6kudg61): our v38 as black vs Decent Chess Bot v7, 82 plies, King capturable.
- [c0llrmf3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=c0llrmf3): our v38 as black vs TUM v8, 62 plies, King capturable.
- [gtdazael](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gtdazael): our v38 as black vs Decent Chess Bot v7, 92 plies, King capturable.
- [zat03y52](https://www.mit.edu/~6.7980/fow/?tab=arena&game=zat03y52): our v38 as white vs Crimson Fog v4, 85 plies, King capturable.
- [yce5qd2l](https://www.mit.edu/~6.7980/fow/?tab=arena&game=yce5qd2l): our v38 as black vs Crimson Fog v4, 66 plies, King capturable.
- [wvn8e4fq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wvn8e4fq): our v38 as black vs HYPOTHERMIA v10, 116 plies, King capturable.
- [r05n0hob](https://www.mit.edu/~6.7980/fow/?tab=arena&game=r05n0hob): our v38 as white vs HYPOTHERMIA v10, 99 plies, King capturable.
- [h6j6w9f3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=h6j6w9f3): our v38 as black vs Farsight v29, 102 plies, King capturable.
- [1yohg3sv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1yohg3sv): our v38 as white vs Farsight v29, 83 plies, King capturable.
- [lhthviq2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lhthviq2): our v38 as black vs Farsight v28, 62 plies, King capturable.
- [7g7s34nt](https://www.mit.edu/~6.7980/fow/?tab=arena&game=7g7s34nt): our v38 as white vs Farsight v28, 49 plies, King capturable.
- [0b3ycubg](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0b3ycubg): our v38 as white vs Next v2, 51 plies, King capturable.
