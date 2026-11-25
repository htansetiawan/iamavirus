# Learning and intelligence status, 2026-11-25 12:12 UTC

Corpus: **279,918 games**. Latest game: 2026-11-25T10:09:13.474696658+00:00. Leaderboard snapshot: 2026-11-25T10:09:23.886058+00:00.

Coverage: last 24 hours include **186 of our games** and **3513 games solely between other teams**. Newest other-team game: 2026-11-25T10:09:13.474696+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 186 played-version/colour groups; previous report 2026-11-24T12:10:03 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 306 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [dx0pmrbf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=dx0pmrbf): our v38 as black vs In Pawn Sight v14, 52 plies, King capturable.
- [0lc6kq3t](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0lc6kq3t): our v38 as black vs Preface v10, 68 plies, King capturable.
- [5kw7i0oz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5kw7i0oz): our v38 as black vs Magnus Monte Carlsen v4, 74 plies, King capturable.
- [sv49mzpp](https://www.mit.edu/~6.7980/fow/?tab=arena&game=sv49mzpp): our v38 as black vs smusebots v8, 84 plies, King capturable.
- [41h2w25c](https://www.mit.edu/~6.7980/fow/?tab=arena&game=41h2w25c): our v38 as black vs Lost Signal v41, 140 plies, King capturable.
- [77d8n3d9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=77d8n3d9): our v38 as black vs Greek Gift v35, 80 plies, King capturable.
- [gkpa13t9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gkpa13t9): our v38 as white vs Greek Gift v35, 67 plies, King capturable.
- [t8ygrze9](https://www.mit.edu/~6.7980/fow/?tab=arena&game=t8ygrze9): our v38 as white vs duck v16, 81 plies, King capturable.
- [smwts3o0](https://www.mit.edu/~6.7980/fow/?tab=arena&game=smwts3o0): our v38 as black vs HYPOTHERMIA v21, 88 plies, King capturable.
- [5o220jai](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5o220jai): our v38 as white vs HYPOTHERMIA v21, 63 plies, King capturable.
- [ejamaft2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ejamaft2): our v38 as white vs duck v15, 105 plies, King capturable.
- [586x8uva](https://www.mit.edu/~6.7980/fow/?tab=arena&game=586x8uva): our v38 as black vs duck v15, 70 plies, King capturable.
- [4se2cwke](https://www.mit.edu/~6.7980/fow/?tab=arena&game=4se2cwke): our v38 as white vs sillygeese v16, 93 plies, King capturable.
- [7stu8ugy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=7stu8ugy): our v38 as white vs Unicorns v4, 141 plies, King capturable.
- [08jcdxdc](https://www.mit.edu/~6.7980/fow/?tab=arena&game=08jcdxdc): our v38 as white vs TA Baseline S v3, 75 plies, King capturable.
- [n2lb1ypy](https://www.mit.edu/~6.7980/fow/?tab=arena&game=n2lb1ypy): our v38 as white vs Mist Opportunities v2, 117 plies, King capturable.
- [e5gdtmg4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=e5gdtmg4): our v38 as black vs Next v10, 248 plies, King capturable.
- [tzyq2rzl](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tzyq2rzl): our v38 as white vs Cranberry Lemon v13, 59 plies, King capturable.
- [wzytfxz4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wzytfxz4): our v38 as white vs Gravel Road v18, 165 plies, King capturable.
- [1g3s654n](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1g3s654n): our v38 as black vs multiagents in a bar v2, 108 plies, King capturable.
