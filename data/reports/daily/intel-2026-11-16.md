# Learning and intelligence status, 2026-11-16 13:05 UTC

Corpus: **243,757 games**. Latest game: 2026-11-16T10:27:42.736359753+00:00. Leaderboard snapshot: 2026-11-16T10:28:00.902603+00:00.

Coverage: last 24 hours include **165 of our games** and **3308 games solely between other teams**. Newest other-team game: 2026-11-16T10:27:42.736359+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 118 played-version/colour groups; previous report 2026-11-11T10:41:30 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 261 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [jvs6i0k5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jvs6i0k5): our v38 as black vs Fogitos v4, 94 plies, King capturable.
- [1rdltpod](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1rdltpod): our v38 as black vs Decent Chess Bot v7, 62 plies, King capturable.
- [d2uh4d5o](https://www.mit.edu/~6.7980/fow/?tab=arena&game=d2uh4d5o): our v38 as black vs In Pawn Sight v14, 58 plies, King capturable.
- [etj3i1lq](https://www.mit.edu/~6.7980/fow/?tab=arena&game=etj3i1lq): our v38 as black vs In Pawn Sight v14, 148 plies, King capturable.
- [a4nzahhh](https://www.mit.edu/~6.7980/fow/?tab=arena&game=a4nzahhh): our v38 as white vs Strongly Invisible v41, 95 plies, King capturable.
- [lehddfrk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lehddfrk): our v38 as black vs Resting Bishop Faces v8, 58 plies, King capturable.
- [wyqmgjk3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wyqmgjk3): our v38 as white vs Gravel Road v12, 75 plies, King capturable.
- [2haz71wp](https://www.mit.edu/~6.7980/fow/?tab=arena&game=2haz71wp): our v38 as black vs Farsight v33, 66 plies, King capturable.
- [r9s4fmzb](https://www.mit.edu/~6.7980/fow/?tab=arena&game=r9s4fmzb): our v38 as white vs Next v6, 65 plies, King capturable.
- [1uifqu3w](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1uifqu3w): our v38 as black vs Unicorns v4, 184 plies, King capturable.
- [cki6muto](https://www.mit.edu/~6.7980/fow/?tab=arena&game=cki6muto): our v38 as black vs Knight Vision v36, 80 plies, King capturable.
- [xa2e0rpk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xa2e0rpk): our v38 as white vs Knight Vision v36, 71 plies, King capturable.
- [vyxxbcap](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vyxxbcap): our v38 as black vs Crimson Fog v4, 98 plies, King capturable.
- [h8pganbw](https://www.mit.edu/~6.7980/fow/?tab=arena&game=h8pganbw): our v38 as black vs Strongly Invisible v41, 112 plies, King capturable.
- [hqvgktjk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hqvgktjk): our v38 as white vs Strongly Invisible v41, 103 plies, King capturable.
- [t66sqzq8](https://www.mit.edu/~6.7980/fow/?tab=arena&game=t66sqzq8): our v38 as white vs Strongly Invisible v41, 107 plies, King capturable.
- [e7f06ean](https://www.mit.edu/~6.7980/fow/?tab=arena&game=e7f06ean): our v38 as black vs Strongly Invisible v41, 74 plies, King capturable.
- [nmx4lrcg](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nmx4lrcg): our v38 as white vs HYPOTHERMIA v14, 111 plies, King capturable.
- [lzrx94jp](https://www.mit.edu/~6.7980/fow/?tab=arena&game=lzrx94jp): our v38 as black vs HYPOTHERMIA v14, 94 plies, King capturable.
- [92m4i5am](https://www.mit.edu/~6.7980/fow/?tab=arena&game=92m4i5am): our v38 as black vs Trojan Horse v8, 102 plies, King capturable.
