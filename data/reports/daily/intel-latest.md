# Learning and intelligence status, 2026-11-02 11:54 UTC

Corpus: **195,614 games**. Latest game: 2026-11-02T10:41:22.278259884+00:00. Leaderboard snapshot: 2026-11-02T11:01:38.062629+00:00.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-02T11:41:55.130000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 82 played-version/colour groups; previous report 2026-11-01T11:46:13 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v37; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 282 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **37**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v37-mist-c-v14-allfit.zip`, SHA-256 `41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [pz23mdh6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pz23mdh6): our v37 as white vs HYPOTHERMIA v4, 117 plies, King capturable.
- [kb4guejv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kb4guejv): our v37 as black vs Decent Chess Bot v7, 160 plies, King capturable.
- [2m37bpdd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2m37bpdd): our v37 as white vs Decent Chess Bot v7, 93 plies, King capturable.
- [d7vw090z](https://www.mit.edu/~6.7980/fow/?tab=arena&game=d7vw090z): our v37 as white vs RATIRL v2, 33 plies, King capturable.
- [dcjmc276](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dcjmc276): our v37 as black vs Mist Opportunities v2, 102 plies, King capturable.
- [j8lp2i8l](https://www.mit.edu/~6.7980/fow/?tab=arena&game=j8lp2i8l): our v37 as white vs Farsight v10, 127 plies, King capturable.
- [50rn3g1q](https://www.mit.edu/~6.7980/fow/?tab=arena&game=50rn3g1q): our v37 as black vs Greek Gift v25, 86 plies, King capturable.
- [ym5zy4qh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ym5zy4qh): our v37 as black vs Farsight v10, 82 plies, King capturable.
- [rm29nf1u](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rm29nf1u): our v37 as black vs Strongly Invisible v41, 82 plies, King capturable.
- [1j3etgyz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1j3etgyz): our v37 as white vs Strongly Invisible v41, 73 plies, King capturable.
- [tq07thws](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tq07thws): our v37 as white vs duck v6, 71 plies, King capturable.
- [e853z9pl](https://www.mit.edu/~6.7980/fow/?tab=arena&game=e853z9pl): our v37 as black vs duck v6, 60 plies, King capturable.
- [tsu6bpsn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tsu6bpsn): our v37 as black vs Lost Signal v19, 102 plies, King capturable.
- [4g691bkw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4g691bkw): our v37 as black vs Crimson Fog v4, 234 plies, King capturable.
- [9klhxuj1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=9klhxuj1): our v37 as white vs Crimson Fog v4, 79 plies, King capturable.
- [xj3kjrdx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xj3kjrdx): our v37 as white vs duck v6, 111 plies, King capturable.
- [p8cdqaf1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=p8cdqaf1): our v37 as white vs Instructors v4, 63 plies, King capturable.
- [mas9e1ni](https://www.mit.edu/~6.7980/fow/?tab=arena&game=mas9e1ni): our v37 as white vs Cranberry Lemon v8, 75 plies, King capturable.
- [fukf7tgk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fukf7tgk): our v37 as white vs HYPOTHERMIA v4, 119 plies, King capturable.
- [i2s3an5a](https://www.mit.edu/~6.7980/fow/?tab=arena&game=i2s3an5a): our v37 as black vs Greek Gift v25, 112 plies, King capturable.
