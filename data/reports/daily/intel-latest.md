# Learning and intelligence status, 2026-11-19 12:04 UTC

Corpus: **255,526 games**. Latest game: 2026-11-19T10:07:25.608068051+00:00. Leaderboard snapshot: 2026-11-19T10:08:19.400426+00:00.

Coverage: last 24 hours include **154 of our games** and **3495 games solely between other teams**. Newest other-team game: 2026-11-19T10:07:25.608068+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 168 played-version/colour groups; previous report 2026-11-18T11:56:23 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 270 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [o5zin22o](https://www.mit.edu/~6.7980/fow/?tab=arena&game=o5zin22o): our v38 as white vs Fogitos v5, 123 plies, King capturable.
- [0qq2b7vq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0qq2b7vq): our v38 as black vs Next v10, 108 plies, King capturable.
- [rccw7mwm](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rccw7mwm): our v38 as white vs Next v10, 99 plies, King capturable.
- [82q1viuj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=82q1viuj): our v38 as white vs Fogitos v5, 93 plies, King capturable.
- [rc77bfuk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rc77bfuk): our v38 as white vs Gravel Road v15, 137 plies, King capturable.
- [99nwd42j](https://www.mit.edu/~6.7980/fow/?tab=arena&game=99nwd42j): our v38 as black vs Gravel Road v15, 62 plies, King capturable.
- [vzuysvyq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vzuysvyq): our v38 as white vs Strongly Invisible v42, 119 plies, King capturable.
- [9r49vcma](https://www.mit.edu/~6.7980/fow/?tab=arena&game=9r49vcma): our v38 as black vs Foggy Fischer v8, 120 plies, King capturable.
- [apg54fw2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=apg54fw2): our v38 as white vs Foggy Fischer v8, 81 plies, King capturable.
- [thcmus1o](https://www.mit.edu/~6.7980/fow/?tab=arena&game=thcmus1o): our v38 as white vs Fogitos v5, 137 plies, King capturable.
- [xz1mvm40](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xz1mvm40): our v38 as black vs Next v10, 142 plies, King capturable.
- [hlpwalcv](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hlpwalcv): our v38 as white vs Next v10, 109 plies, King capturable.
- [uqo8bs64](https://www.mit.edu/~6.7980/fow/?tab=arena&game=uqo8bs64): our v38 as black vs Next v10, 74 plies, King capturable.
- [d86mxvgn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=d86mxvgn): our v38 as white vs Next v10, 75 plies, King capturable.
- [ix1556n0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ix1556n0): our v38 as black vs In Pawn Sight v14, 70 plies, King capturable.
- [giqhr4o0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=giqhr4o0): our v38 as white vs RATIRL v2, 111 plies, King capturable.
- [2s8dwvgx](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2s8dwvgx): our v38 as white vs TUM v9, 75 plies, King capturable.
- [4hcso7fy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4hcso7fy): our v38 as black vs Decent Chess Bot v7, 70 plies, King capturable.
- [vfulybgf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vfulybgf): our v38 as white vs Decent Chess Bot v7, 47 plies, King capturable.
- [zpz17ixk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=zpz17ixk): our v38 as black vs sillygeese v9, 110 plies, King capturable.
