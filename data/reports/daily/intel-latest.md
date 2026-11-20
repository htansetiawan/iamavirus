# Learning and intelligence status, 2026-11-20 12:09 UTC

Corpus: **259,499 games**. Latest game: 2026-11-20T10:06:23.882447783+00:00. Leaderboard snapshot: 2026-11-20T10:06:30.234801+00:00.

Coverage: last 24 hours include **146 of our games** and **3464 games solely between other teams**. Newest other-team game: 2026-11-20T10:06:23.882447+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 178 played-version/colour groups; previous report 2026-11-19T11:50:19 | Diagnosis and case selection; not an input to the live policy or belief |
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

- [yeovz2g1](https://www.mit.edu/~6.7980/fow/?tab=arena&game=yeovz2g1): our v38 as black vs Strongly Invisible v42, 88 plies, King capturable.
- [1r8ewzz6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1r8ewzz6): our v38 as white vs Foggy Fischer v8, 125 plies, King capturable.
- [evh3np95](https://www.mit.edu/~6.7980/fow/?tab=arena&game=evh3np95): our v38 as black vs Foggy Fischer v8, 118 plies, King capturable.
- [g641zqi0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=g641zqi0): our v38 as black vs Farsight v33, 80 plies, King capturable.
- [fawdjb6h](https://www.mit.edu/~6.7980/fow/?tab=arena&game=fawdjb6h): our v38 as white vs Farsight v33, 57 plies, King capturable.
- [qqm6ty9c](https://www.mit.edu/~6.7980/fow/?tab=arena&game=qqm6ty9c): our v38 as black vs TUM v9, 90 plies, King capturable.
- [xve80q04](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xve80q04): our v38 as white vs TUM v9, 55 plies, King capturable.
- [91k0kpil](https://www.mit.edu/~6.7980/fow/?tab=arena&game=91k0kpil): our v38 as black vs Knight Vision v36, 124 plies, King capturable.
- [5qiihb6d](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5qiihb6d): our v38 as white vs Knight Vision v36, 85 plies, King capturable.
- [364pfq38](https://www.mit.edu/~6.7980/fow/?tab=arena&game=364pfq38): our v38 as black vs Knight Vision v36, 138 plies, King capturable.
- [hg03qhpf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hg03qhpf): our v38 as white vs Preface v2, 87 plies, King capturable.
- [ze7aejxw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ze7aejxw): our v38 as black vs Knight Vision v36, 94 plies, King capturable.
- [vk71j7mq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vk71j7mq): our v38 as white vs Knight Vision v36, 81 plies, King capturable.
- [hqy41yo2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hqy41yo2): our v38 as white vs Mist Opportunities v2, 99 plies, King capturable.
- [rwoin52m](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rwoin52m): our v38 as black vs duck v11, 90 plies, King capturable.
- [o9u7lah6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=o9u7lah6): our v38 as black vs Cross-Registered Players v2, 74 plies, King capturable.
- [2r6durq7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2r6durq7): our v38 as black vs Trojan Horse v9, 104 plies, King capturable.
- [wl3oyqhg](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wl3oyqhg): our v38 as black vs Preface v2, 72 plies, King capturable.
- [me7z1o6c](https://www.mit.edu/~6.7980/fow/?tab=arena&game=me7z1o6c): our v38 as white vs duck v11, 95 plies, King capturable.
- [xsnfqhkg](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xsnfqhkg): our v38 as white vs In Pawn Sight v14, 65 plies, King capturable.
