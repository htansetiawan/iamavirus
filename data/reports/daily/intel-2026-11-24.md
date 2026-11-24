# Learning and intelligence status, 2026-11-24 12:22 UTC

Corpus: **275,871 games**. Latest game: 2026-11-24T10:11:30.681678146+00:00. Leaderboard snapshot: 2026-11-24T10:11:28.116935+00:00.

Coverage: last 24 hours include **145 of our games** and **3574 games solely between other teams**. Newest other-team game: 2026-11-24T10:11:30.681678+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 178 played-version/colour groups; previous report 2026-11-23T12:18:34 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 286 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [cjzz75ys](https://www.mit.edu/~6.7980/fow/?tab=arena&game=cjzz75ys): our v38 as white vs Mu1tip13 @g3nt$ v6, 109 plies, King capturable.
- [8mmovwls](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8mmovwls): our v38 as black vs Mu1tip13 @g3nt$ v6, 62 plies, King capturable.
- [sbo4164u](https://www.mit.edu/~6.7980/fow/?tab=arena&game=sbo4164u): our v38 as white vs sillygeese v17, 221 plies, King capturable.
- [kfskq3d1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kfskq3d1): our v38 as white vs Strongly Invisible v42, 57 plies, King capturable.
- [wi4sjyv4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wi4sjyv4): our v38 as black vs HYPOTHERMIA v21, 62 plies, King capturable.
- [74bg09zy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=74bg09zy): our v38 as black vs Foggy Fischer v12, 120 plies, King capturable.
- [4r3iknn6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4r3iknn6): our v38 as white vs Foggy Fischer v12, 105 plies, King capturable.
- [5jo7it2v](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5jo7it2v): our v38 as black vs Trojan Horse v9, 114 plies, King capturable.
- [vl6nlfe2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vl6nlfe2): our v38 as white vs Lost Signal v42, 77 plies, King capturable.
- [zv1t4sak](https://www.mit.edu/~6.7980/fow/?tab=arena&game=zv1t4sak): our v38 as black vs HYPOTHERMIA v21, 60 plies, King capturable.
- [ltjdwrc7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ltjdwrc7): our v38 as black vs Strongly Invisible v42, 132 plies, King capturable.
- [hwaaqj6v](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hwaaqj6v): our v38 as white vs Greek Gift v35, 111 plies, King capturable.
- [5lh4xnwf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5lh4xnwf): our v38 as black vs Greek Gift v35, 72 plies, King capturable.
- [6ebqnotq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=6ebqnotq): our v38 as white vs Foggy Fischer v12, 65 plies, King capturable.
- [itkhjd7k](https://www.mit.edu/~6.7980/fow/?tab=arena&game=itkhjd7k): our v38 as black vs Foggy Fischer v12, 66 plies, King capturable.
- [4qde4l0p](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4qde4l0p): our v38 as black vs Foggy Fischer v12, 98 plies, King capturable.
- [5ajnjg20](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5ajnjg20): our v38 as black vs Gravel Road v21, 48 plies, King capturable.
- [dd7nlvuj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dd7nlvuj): our v38 as black vs Cranberry Lemon v12, 114 plies, King capturable.
- [ntnpb1v5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ntnpb1v5): our v38 as black vs HYPOTHERMIA v21, 136 plies, King capturable.
- [kdz4hmyy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kdz4hmyy): our v38 as black vs Crimson Fog v7, 90 plies, King capturable.
