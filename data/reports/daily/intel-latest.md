# Learning and intelligence status, 2026-11-23 12:29 UTC

Corpus: **271,783 games**. Latest game: 2026-11-23T10:14:01.220797130+00:00. Leaderboard snapshot: 2026-11-23T10:13:47.232633+00:00.

Coverage: last 24 hours include **190 of our games** and **3618 games solely between other teams**. Newest other-team game: 2026-11-23T10:14:01.220797+00:00.

Both feeds have recent records; this freshness check does not establish complete API coverage.

| Feed | Latest evidence | How it reaches the bot |
|---|---|---|
| Replay and training data | Manifest modified 2026-11-11T14:42:12.850000+00:00; move-export metadata in JSON | Training input; no automatic promotion |
| Taxonomy | 176 played-version/colour groups; previous report 2026-11-22T12:00:53 | Diagnosis and case selection; not an input to the live policy or belief |
| Working move model | Declared fit 2026-10-29, 6776 games | Candidate probabilities; requires validation and packaging |
| Active archive's history table | Snapshot v38; 359,889 records; release-map hash checked | Packaged model/table; changes require a new submission |
| Reference history table | Archive v35, 151316 records | Fixed table packaged inside that archive; not updated by replay ingest |
| Frozen regression suite | 1379 decisions; file modified 2026-10-12T00:48:04.508580+00:00 | Fixed comparison set; retain it across experiments |
| Rolling loss index | 283 recent examples, at most 3 per opponent version / our version / colour | Supplement candidates; not replay-tested or a strength estimate |

## Reference versus active version

Snapshot active version: **38**. Reference archive: **v35**. The reference is retained for comparison; it is not the active deployment.

Active archive: `iamavirus-v38-mist-c-allchildren.zip`, SHA-256 `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`. Its hash matches the shared release map; model-member and history-table hashes are in the JSON. The public API identifies the active version but cannot verify uploaded ZIP bytes.

File modification dates are filesystem freshness, not proof of retraining or dataset coverage. The working model is not necessarily the model in the active archive. Rebuilding inputs does not change the submitted ZIP.

## From taxonomy to a measured change

Select a behaviour by played version and colour, inspect actual replay cases, and measure predicted versus observed risk. Fit a correction using training games, check it on held-out games and the frozen suite plus fresh cases, then test full games. A high exposure or sacrifice rate alone does not imply a bad move; trades and recaptures matter. Taxonomy ranks describe behaviour and can reflect the opponent mix.

## Recent loss examples

The JSON contains the full bounded index. These are game pointers, not newly validated decision tests.

- [wxd2yrei](https://www.mit.edu/~6.7980/fow/?tab=arena&game=wxd2yrei): our v38 as white vs Fogitos v7, 115 plies, King capturable.
- [1xxb19l5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=1xxb19l5): our v38 as black vs Fogitos v7, 100 plies, King capturable.
- [pe5duwuj](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pe5duwuj): our v38 as black vs Foggy Fischer v11, 78 plies, King capturable.
- [0r46edzb](https://www.mit.edu/~6.7980/fow/?tab=arena&game=0r46edzb): our v38 as black vs Cranberry Lemon v10, 106 plies, King capturable.
- [xiwfczyk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xiwfczyk): our v38 as white vs Gravel Road v20, 85 plies, King capturable.
- [b804iyav](https://www.mit.edu/~6.7980/fow/?tab=arena&game=b804iyav): our v38 as black vs Farsight v40, 116 plies, King capturable.
- [bqosvban](https://www.mit.edu/~6.7980/fow/?tab=arena&game=bqosvban): our v38 as white vs Farsight v40, 61 plies, King capturable.
- [t4mbe2l2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=t4mbe2l2): our v38 as white vs Team 319 v3, 77 plies, King capturable.
- [p915ipz7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=p915ipz7): our v38 as black vs Team 319 v3, 62 plies, King capturable.
- [y5bjpbsk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=y5bjpbsk): our v38 as black vs Mu1tip13 @g3nt$ v6, 80 plies, King capturable.
- [y1t52aww](https://www.mit.edu/~6.7980/fow/?tab=arena&game=y1t52aww): our v38 as white vs Mu1tip13 @g3nt$ v6, 43 plies, King capturable.
- [m9i3bbi6](https://www.mit.edu/~6.7980/fow/?tab=arena&game=m9i3bbi6): our v38 as black vs Mu1tip13 @g3nt$ v6, 104 plies, King capturable.
- [kuuld7hn](https://www.mit.edu/~6.7980/fow/?tab=arena&game=kuuld7hn): our v38 as black vs RATIRL v2, 78 plies, King capturable.
- [jp458mw4](https://www.mit.edu/~6.7980/fow/?tab=arena&game=jp458mw4): our v38 as white vs Strongly Invisible v42, 95 plies, King capturable.
- [hdo9etx8](https://www.mit.edu/~6.7980/fow/?tab=arena&game=hdo9etx8): our v38 as white vs Mist Opportunities v2, 161 plies, King capturable.
- [l58rr99s](https://www.mit.edu/~6.7980/fow/?tab=arena&game=l58rr99s): our v38 as white vs Mu1tip13 @g3nt$ v6, 107 plies, King capturable.
- [5h8323d3](https://www.mit.edu/~6.7980/fow/?tab=arena&game=5h8323d3): our v38 as black vs Next v10, 110 plies, King capturable.
- [z57747z5](https://www.mit.edu/~6.7980/fow/?tab=arena&game=z57747z5): our v38 as white vs Next v10, 65 plies, King capturable.
- [szfaya7r](https://www.mit.edu/~6.7980/fow/?tab=arena&game=szfaya7r): our v38 as white vs Decent Chess Bot v7, 75 plies, King capturable.
- [rbvqpgci](https://www.mit.edu/~6.7980/fow/?tab=arena&game=rbvqpgci): our v38 as black vs Decent Chess Bot v7, 58 plies, King capturable.
