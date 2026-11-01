# Learning and intelligence status, 2026-11-01 11:49 UTC

Corpus: **190,970 games**. Latest game: 2026-11-01T10:15:08.012205522+00:00. Leaderboard snapshot: 2026-11-01T10:15:32.740411+00:00.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified unavailable; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 86 played-version/colour groups; previous report 2026-10-31T12:17:11 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 208 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **35**. Reference archive: **v35**. Versions match; hashes are recorded in the JSON.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [qqzttbee](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qqzttbee): our v35 as black vs Knight Vision v36, 100 plies, King capturable.
- [o1mwc9qk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=o1mwc9qk): our v35 as white vs HYPOTHERMIA v4, 77 plies, King capturable.
- [tw4bgl4x](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tw4bgl4x): our v35 as black vs HYPOTHERMIA v4, 78 plies, King capturable.
- [6s8o5nwd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=6s8o5nwd): our v35 as black vs Strongly Invisible v41, 62 plies, King capturable.
- [wejeypy0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wejeypy0): our v35 as black vs Mist Opportunities v2, 82 plies, King capturable.
- [5tg2v31k](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5tg2v31k): our v35 as white vs Strongly Invisible v41, 111 plies, King capturable.
- [kj58ovnv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kj58ovnv): our v35 as black vs Gravel Road v4, 108 plies, King capturable.
- [fh5vhk62](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fh5vhk62): our v35 as white vs Gravel Road v4, 55 plies, King capturable.
- [dyz2p2hb](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dyz2p2hb): our v35 as black vs Foggy Fischer v4, 58 plies, King capturable.
- [wtcylq1d](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wtcylq1d): our v35 as white vs Crimson Fog v4, 63 plies, King capturable.
- [uuzgl59z](https://www.mit.edu/~6.7980/fow/?tab=arena&game=uuzgl59z): our v35 as black vs HYPOTHERMIA v4, 80 plies, King capturable.
- [aya0q0ax](https://www.mit.edu/~6.7980/fow/?tab=arena&game=aya0q0ax): our v35 as black vs Crimson Fog v4, 24 plies, King capturable.
- [08ula1jh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=08ula1jh): our v35 as black vs TA Baseline S v3, 104 plies, King capturable.
- [f3n19ty1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=f3n19ty1): our v35 as white vs Farsight v6, 59 plies, King capturable.
- [xusofggg](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xusofggg): our v35 as black vs Farsight v6, 58 plies, King capturable.
- [047wdp5z](https://www.mit.edu/~6.7980/fow/?tab=arena&game=047wdp5z): our v35 as white vs Lost Signal v19, 201 plies, King capturable.
- [r82lsby1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=r82lsby1): our v35 as white vs HYPOTHERMIA v4, 81 plies, King capturable.
- [z5jir9rk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=z5jir9rk): our v35 as black vs HYPOTHERMIA v4, 74 plies, King capturable.
- [nqq6kiuw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nqq6kiuw): our v35 as black vs Strongly Invisible v41, 82 plies, King capturable.
- [4zy248z7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4zy248z7): our v35 as white vs Strongly Invisible v41, 67 plies, King capturable.
