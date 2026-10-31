# Learning and intelligence status, 2026-10-31 22:00 UTC

Corpus: **186,276 games**. Latest game: 2026-10-31T10:10:19.796802917+00:00. Leaderboard snapshot: 2026-10-31T10:10:24.980681+00:00.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-10-31T12:17:05.890000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 86 played-version/colour groups; previous report 2026-10-30T12:20:16 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 203 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **35**. Reference archive: **v35**. Versions match; hashes are recorded in the JSON.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [bv0la6ym](https://www.mit.edu/~6.7980/fow/?tab=arena&game=bv0la6ym): our v35 as black vs HYPOTHERMIA v4, 76 plies, King capturable.
- [lufzrpzk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lufzrpzk): our v35 as black vs Knight Vision v36, 96 plies, King capturable.
- [mmy3eea0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=mmy3eea0): our v35 as white vs Knight Vision v36, 71 plies, King capturable.
- [utaykrq4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=utaykrq4): our v35 as black vs HYPOTHERMIA v4, 184 plies, King capturable.
- [5sbun1z9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5sbun1z9): our v35 as black vs Mu1tip13 @g3nt$ v6, 62 plies, King capturable.
- [brl2o62h](https://www.mit.edu/~6.7980/fow/?tab=arena&game=brl2o62h): our v35 as white vs Cranberry Lemon v4, 83 plies, King capturable.
- [kkrtzcr2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kkrtzcr2): our v35 as white vs HYPOTHERMIA v4, 107 plies, King capturable.
- [p84x4rp8](https://www.mit.edu/~6.7980/fow/?tab=arena&game=p84x4rp8): our v35 as black vs Strongly Invisible v41, 102 plies, King capturable.
- [hjti6ona](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hjti6ona): our v35 as white vs Strongly Invisible v41, 79 plies, King capturable.
- [88slzkdn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=88slzkdn): our v35 as white vs RATIRL v2, 45 plies, King capturable.
- [ra414wp6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ra414wp6): our v35 as white vs duck v6, 73 plies, King capturable.
- [lpuva1cf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lpuva1cf): our v35 as white vs Greek Gift v25, 89 plies, King capturable.
- [2jh378mw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2jh378mw): our v35 as black vs Greek Gift v25, 70 plies, King capturable.
- [1dkaks9g](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1dkaks9g): our v35 as black vs Crimson Fog v4, 128 plies, King capturable.
- [gizvq62p](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gizvq62p): our v35 as white vs Crimson Fog v4, 67 plies, King capturable.
- [scaigw21](https://www.mit.edu/~6.7980/fow/?tab=arena&game=scaigw21): our v35 as black vs Decent Chess Bot v7, 78 plies, King capturable.
- [fr1gwngl](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fr1gwngl): our v35 as white vs Lost Signal v19, 131 plies, King capturable.
- [upeoh1jx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=upeoh1jx): our v35 as black vs Knight Vision v36, 80 plies, King capturable.
- [0hyy5zhb](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0hyy5zhb): our v35 as white vs Knight Vision v36, 73 plies, King capturable.
- [ehhb2iwy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ehhb2iwy): our v35 as black vs Crimson Fog v4, 54 plies, King capturable.
