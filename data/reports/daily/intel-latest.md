# Learning and intelligence status, 2026-11-18 12:07 UTC

Corpus: **251,564 games**. Latest game: 2026-11-18T10:13:16.304219801+00:00. Leaderboard snapshot: 2026-11-18T10:13:16.364795+00:00.

Coverage: last 24 hours include **171 of our games** and **3515 games solely between other teams**. Newest other-team game: 2026-11-18T10:13:16.304219+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 152 played-version/colour groups; previous report 2026-11-17T12:24:21 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 264 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [gphbm4tl](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gphbm4tl): our v38 as white vs Next v10, 67 plies, King capturable.
- [2nzfo99j](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2nzfo99j): our v38 as black vs Strongly Invisible v42, 190 plies, King capturable.
- [i5x9fd09](https://www.mit.edu/~6.7980/fow/?tab=arena&game=i5x9fd09): our v38 as white vs Strongly Invisible v42, 101 plies, King capturable.
- [syhd6vfx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=syhd6vfx): our v38 as black vs In Pawn Sight v14, 118 plies, King capturable.
- [s4mjnuuh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=s4mjnuuh): our v38 as white vs In Pawn Sight v14, 85 plies, King capturable.
- [qqf92j7y](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qqf92j7y): our v38 as black vs Magnus Monte Carlsen v4, 74 plies, King capturable.
- [vhmlh0zd](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vhmlh0zd): our v38 as white vs HYPOTHERMIA v21, 111 plies, King capturable.
- [9d6xgtsi](https://www.mit.edu/~6.7980/fow/?tab=arena&game=9d6xgtsi): our v38 as black vs Foggy Fischer v6, 74 plies, King capturable.
- [clgovvh8](https://www.mit.edu/~6.7980/fow/?tab=arena&game=clgovvh8): our v38 as white vs Farsight v33, 57 plies, King capturable.
- [4g0ekwmt](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4g0ekwmt): our v38 as white vs Greek Gift v30, 115 plies, King capturable.
- [toqmp7ys](https://www.mit.edu/~6.7980/fow/?tab=arena&game=toqmp7ys): our v38 as black vs Greek Gift v30, 94 plies, King capturable.
- [cda2shwc](https://www.mit.edu/~6.7980/fow/?tab=arena&game=cda2shwc): our v38 as white vs Decent Chess Bot v7, 103 plies, King capturable.
- [xd58htol](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xd58htol): our v38 as black vs Crimson Fog v4, 60 plies, King capturable.
- [vegekglp](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vegekglp): our v38 as white vs Foggy Fischer v6, 93 plies, King capturable.
- [k3ybragn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=k3ybragn): our v38 as black vs Foggy Fischer v6, 54 plies, King capturable.
- [qkkbljuy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qkkbljuy): our v38 as white vs Team 319 v2, 95 plies, King capturable.
- [c6dwyd5r](https://www.mit.edu/~6.7980/fow/?tab=arena&game=c6dwyd5r): our v38 as white vs sillygeese v7, 149 plies, King capturable.
- [he48ydjn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=he48ydjn): our v38 as black vs sillygeese v7, 70 plies, King capturable.
- [lno35p8k](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lno35p8k): our v38 as black vs Cranberry Lemon v9, 98 plies, King capturable.
- [i3tlgyro](https://www.mit.edu/~6.7980/fow/?tab=arena&game=i3tlgyro): our v38 as black vs Magnus Monte Carlsen v4, 52 plies, King capturable.
