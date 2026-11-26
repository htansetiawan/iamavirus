# Learning and intelligence status, 2026-11-26 12:13 UTC

Corpus: **283,892 games**. Latest game: 2026-11-26T10:06:09.416637800+00:00. Leaderboard snapshot: 2026-11-26T10:06:09.111634+00:00.

Coverage: last 24 hours include **142 of our games** and **3493 games solely between other teams**. Newest other-team game: 2026-11-26T10:06:09.416637+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 196 played-version/colour groups; previous report 2026-11-25T11:59:27 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 324 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [qfkrwhit](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qfkrwhit): our v38 as white vs Greek Gift v35, 93 plies, King capturable.
- [l0ja8yzv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=l0ja8yzv): our v38 as black vs Greek Gift v35, 78 plies, King capturable.
- [toiuxm30](https://www.mit.edu/~6.7980/fow/?tab=arena&game=toiuxm30): our v38 as white vs HYPOTHERMIA v21, 75 plies, King capturable.
- [rzipu5m9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rzipu5m9): our v38 as white vs Foggy Fischer v13, 77 plies, King capturable.
- [w9gi55hf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=w9gi55hf): our v38 as black vs Foggy Fischer v13, 46 plies, King capturable.
- [jbm0vkrj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jbm0vkrj): our v38 as white vs minseok and friends v3, 99 plies, King capturable.
- [legwcasd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=legwcasd): our v38 as black vs HYPOTHERMIA v21, 42 plies, King capturable.
- [hb6hgcoz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hb6hgcoz): our v38 as white vs frog v4, 117 plies, King capturable.
- [j8w7f7cn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=j8w7f7cn): our v38 as white vs Gravel Road v18, 97 plies, King capturable.
- [z5s0575j](https://www.mit.edu/~6.7980/fow/?tab=arena&game=z5s0575j): our v38 as black vs Gravel Road v18, 94 plies, King capturable.
- [64oqy1mj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=64oqy1mj): our v38 as white vs Greek Gift v35, 119 plies, King capturable.
- [ed8whdtp](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ed8whdtp): our v38 as black vs Greek Gift v35, 104 plies, King capturable.
- [2in7ep86](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2in7ep86): our v38 as black vs sillygeese v16, 100 plies, King capturable.
- [hifa1fxr](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hifa1fxr): our v38 as black vs RATIRL v3, 180 plies, King capturable.
- [kp2tw8hm](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kp2tw8hm): our v38 as white vs RATIRL v3, 87 plies, King capturable.
- [mhu7ega8](https://www.mit.edu/~6.7980/fow/?tab=arena&game=mhu7ega8): our v38 as black vs TUM v12, 82 plies, King capturable.
- [2dbseh7b](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2dbseh7b): our v38 as black vs IGM v3, 108 plies, King capturable.
- [93tl6qe4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=93tl6qe4): our v38 as white vs IGM v3, 89 plies, King capturable.
- [fsf70cdf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fsf70cdf): our v38 as black vs Knight Vision v37, 70 plies, King capturable.
- [phha1yyi](https://www.mit.edu/~6.7980/fow/?tab=arena&game=phha1yyi): our v38 as black vs Gravel Road v18, 152 plies, King capturable.
