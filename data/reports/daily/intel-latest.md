# Learning and intelligence status, 2026-11-21 12:04 UTC

Corpus: **263,496 games**. Latest game: 2026-11-21T10:05:00.969675368+00:00. Leaderboard snapshot: 2026-11-21T10:05:14.359601+00:00.

Coverage: last 24 hours include **150 of our games** and **3518 games solely between other teams**. Newest other-team game: 2026-11-21T10:05:00.969675+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 170 played-version/colour groups; previous report 2026-11-20T11:57:06 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 276 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [9ew4ett1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=9ew4ett1): our v38 as white vs Decent Chess Bot v7, 97 plies, King capturable.
- [bpvmdryf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=bpvmdryf): our v38 as black vs Decent Chess Bot v7, 78 plies, King capturable.
- [pakkefsy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pakkefsy): our v38 as white vs frog v3, 115 plies, King capturable.
- [n9zk5cr3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=n9zk5cr3): our v38 as black vs frog v3, 86 plies, King capturable.
- [5mzdvfh6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5mzdvfh6): our v38 as black vs TUM v9, 110 plies, King capturable.
- [ws8sn74a](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ws8sn74a): our v38 as black vs Cranberry Lemon v9, 194 plies, King capturable.
- [kh6uttx0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kh6uttx0): our v38 as white vs HYPOTHERMIA v21, 113 plies, King capturable.
- [yarvol60](https://www.mit.edu/~6.7980/fow/?tab=arena&game=yarvol60): our v38 as black vs HYPOTHERMIA v21, 62 plies, King capturable.
- [pqv3j57i](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pqv3j57i): our v38 as white vs Next v11, 93 plies, King capturable.
- [8qqb27vr](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8qqb27vr): our v38 as black vs Next v11, 66 plies, King capturable.
- [3przq7qn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3przq7qn): our v38 as white vs Magnus Monte Carlsen v4, 73 plies, King capturable.
- [yj6tb1k4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=yj6tb1k4): our v38 as white vs Greek Gift v30, 89 plies, King capturable.
- [3320qadr](https://www.mit.edu/~6.7980/fow/?tab=arena&game=3320qadr): our v38 as black vs Greek Gift v30, 48 plies, King capturable.
- [wng3dwjf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wng3dwjf): our v38 as black vs Cranberry Lemon v9, 126 plies, King capturable.
- [fnou01j6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fnou01j6): our v38 as black vs Ex Republics v32, 98 plies, King capturable.
- [8zae4kr1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8zae4kr1): our v38 as white vs Ex Republics v32, 89 plies, King capturable.
- [ddz2fx4t](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ddz2fx4t): our v38 as white vs Decent Chess Bot v7, 131 plies, King capturable.
- [r92e8d8z](https://www.mit.edu/~6.7980/fow/?tab=arena&game=r92e8d8z): our v38 as black vs Decent Chess Bot v7, 114 plies, King capturable.
- [5bvac8rt](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5bvac8rt): our v38 as black vs Cranberry Lemon v9, 82 plies, King capturable.
- [laiidgu1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=laiidgu1): our v38 as white vs Cranberry Lemon v9, 129 plies, King capturable.
