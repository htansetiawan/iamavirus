# Learning and intelligence status, 2026-11-27 12:01 UTC

Corpus: **287,891 games**. Latest game: 2026-11-27T10:07:41.629578724+00:00. Leaderboard snapshot: 2026-11-27T10:07:48.759145+00:00.

Coverage: last 24 hours include **133 of our games** and **3554 games solely between other teams**. Newest other-team game: 2026-11-27T10:07:41.629578+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 190 played-version/colour groups; previous report 2026-11-26T12:04:36 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 297 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [xv2hj3a3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xv2hj3a3): our v38 as black vs frog v4, 232 plies, King capturable.
- [vt9ve0t5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vt9ve0t5): our v38 as white vs frog v4, 67 plies, King capturable.
- [qzhobcc2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qzhobcc2): our v38 as black vs HYPOTHERMIA v21, 80 plies, King capturable.
- [92gb2g41](https://www.mit.edu/~6.7980/fow/?tab=arena&game=92gb2g41): our v38 as white vs HYPOTHERMIA v21, 65 plies, King capturable.
- [xy5fdts3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xy5fdts3): our v38 as white vs Greek Gift v35, 161 plies, King capturable.
- [h3vwj2rw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=h3vwj2rw): our v38 as black vs Greek Gift v35, 44 plies, King capturable.
- [hmbguw0w](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hmbguw0w): our v38 as white vs frog v4, 65 plies, King capturable.
- [71hcd0cj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=71hcd0cj): our v38 as black vs minseok and friends v3, 126 plies, King capturable.
- [3fnt6d23](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3fnt6d23): our v38 as white vs Preface v10, 153 plies, King capturable.
- [ytz4vcmx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ytz4vcmx): our v38 as black vs Preface v10, 136 plies, King capturable.
- [fb7xnerl](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fb7xnerl): our v38 as white vs Preface v10, 125 plies, King capturable.
- [1orj5ds7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1orj5ds7): our v38 as white vs HYPOTHERMIA v21, 131 plies, King capturable.
- [qcufkrdw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qcufkrdw): our v38 as black vs HYPOTHERMIA v21, 126 plies, King capturable.
- [mnjs8z5s](https://www.mit.edu/~6.7980/fow/?tab=arena&game=mnjs8z5s): our v38 as black vs Preface v10, 8 plies, King capturable.
- [y4hpxpnt](https://www.mit.edu/~6.7980/fow/?tab=arena&game=y4hpxpnt): our v38 as black vs Crimson Fog v7, 62 plies, King capturable.
- [tqmuwi3e](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tqmuwi3e): our v38 as white vs Ex Republics v34, 95 plies, King capturable.
- [85tpzhgj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=85tpzhgj): our v38 as white vs Mist Opportunities v2, 111 plies, King capturable.
- [2bfn4k47](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2bfn4k47): our v38 as black vs Knight Vision v37, 76 plies, King capturable.
- [pwk6o5wi](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pwk6o5wi): our v38 as white vs Knight Vision v37, 55 plies, King capturable.
- [rlq18kjf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rlq18kjf): our v38 as white vs Instructors v4, 117 plies, King capturable.
