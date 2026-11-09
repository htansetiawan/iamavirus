# Learning and intelligence status, 2026-11-09 22:28 UTC

Corpus: **227,275 games**. Latest game: 2026-11-09T21:54:14.304001604+00:00. Leaderboard snapshot: 2026-11-09T21:51:47.277729+00:00.

Coverage: last 24 hours include **272 of our games** and **2022 games solely between other teams**. Newest other-team game: 2026-11-09T10:15:01.901273+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-02T11:41:55.130000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 168 played-version/colour groups; previous report 2026-11-02T11:42:35 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; mapping unresolved: expected one release-map row for v38; found 0 | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 303 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

**Mapping update required:** expected one release-map row for v38; found 0.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [sdyi1pwh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=sdyi1pwh): our v38 as white vs Ex Republics v32, 107 plies, King capturable.
- [77314a5s](https://www.mit.edu/~6.7980/fow/?tab=arena&game=77314a5s): our v38 as white vs Ex Republics v32, 67 plies, King capturable.
- [oh7aybes](https://www.mit.edu/~6.7980/fow/?tab=arena&game=oh7aybes): our v38 as white vs Decent Chess Bot v7, 109 plies, King capturable.
- [3cqxj83x](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3cqxj83x): our v38 as black vs Decent Chess Bot v7, 76 plies, King capturable.
- [eqc3xnnk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=eqc3xnnk): our v38 as white vs Foggy Fischer v4, 61 plies, King capturable.
- [k99s63cx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=k99s63cx): our v38 as black vs Instructors v4, 76 plies, King capturable.
- [22xu1xi3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=22xu1xi3): our v38 as black vs Greek Gift v25, 200 plies, King capturable.
- [y7tbx6ku](https://www.mit.edu/~6.7980/fow/?tab=arena&game=y7tbx6ku): our v38 as white vs Greek Gift v25, 69 plies, King capturable.
- [asln41w9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=asln41w9): our v38 as white vs Foggy Fischer v4, 87 plies, King capturable.
- [acqsvm33](https://www.mit.edu/~6.7980/fow/?tab=arena&game=acqsvm33): our v38 as black vs TUM v4, 132 plies, King capturable.
- [3ykatuqd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3ykatuqd): our v38 as black vs HYPOTHERMIA v4, 90 plies, King capturable.
- [6ql34y5r](https://www.mit.edu/~6.7980/fow/?tab=arena&game=6ql34y5r): our v38 as white vs Ex Republics v32, 123 plies, King capturable.
- [cxw9s941](https://www.mit.edu/~6.7980/fow/?tab=arena&game=cxw9s941): our v38 as black vs TA Baseline S v3, 44 plies, King capturable.
- [6nvsepf4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=6nvsepf4): our v38 as black vs Ex Republics v32, 176 plies, King capturable.
- [wmpr2ab7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wmpr2ab7): our v38 as black vs Cranberry Lemon v9, 82 plies, King capturable.
- [jlq8ty8r](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jlq8ty8r): our v38 as black vs Crimson Fog v4, 108 plies, King capturable.
- [6rfu5coz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=6rfu5coz): our v38 as white vs duck v11, 121 plies, King capturable.
- [3f7u3czk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3f7u3czk): our v38 as black vs duck v11, 108 plies, King capturable.
- [xpv42rpd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xpv42rpd): our v38 as black vs Next v1, 92 plies, King capturable.
- [lifj1sdi](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lifj1sdi): our v38 as black vs Lost Signal v26, 154 plies, King capturable.
