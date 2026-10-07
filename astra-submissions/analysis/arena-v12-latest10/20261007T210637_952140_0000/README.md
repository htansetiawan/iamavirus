# Arena v12: ten completed games as of October 7, 2026, 5:06:37 p.m. Boston

**4 wins, 0 draws, 6 losses.** Apricot Squad v9: 3–0; TA Baseline P v5: 1–2;
duck v5: 0–2; Decent Chess Bot v2: 0–2. No TA A/S games in this sample.
The first page covered 14 v12 games overall (7W–1D–6L), of which these were
the latest ten. This is an opponent-dependent snapshot, not proof of regression.

The public API confirmed arena **v11 active** at 21:11:12 UTC after the user's
switch. That is Astra's immutable `iamavirus-v12-hybrid.zip`, SHA256
`a5f806d0039f514006f3af902767557ad35137d9d02e2779181d438eb5b47cf3`.
Arena v12 is Fable's upload, SHA256
`68a89006f6c292cf9145ecf36078a0f381831f97ea478dc5ca80de924e6dd5a4`.
The mapping combines the user's upload report and the repository's mapping;
the public API reports version metadata, not ZIP hashes. By the switch check,
v12 had 16 completed games, 7W–1D–8L; the two later games are outside this review.

## What concerns me

Every loss ended with an attacker hidden before our final move. All six had
at least one legal move that survived the immediate king test on the true board.
That does **not** mean the bot could know it was safe, or that the game was winnable.
Three moves ignored an existing hidden attack, two king moves entered a new
hidden attack, and one king move escaped a visible pawn attack into a hidden
bishop attack. Five losing decisions followed an unchanged observation.

| Game | Opponent | Final move | Hidden attacker | Immediate surviving alternatives | Material before final move |
|---|---|---|---|---|---|
| [vcf84z1p](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vcf84z1p) | duck | 58.Kg2 | Qf3 | h5h6 only | −13.3 pawns |
| [v0om2jys](https://www.mit.edu/~6.7980/fow/?tab=arena&game=v0om2jys) | duck | 37...Ref8 | Rh7 against Kf7 | f7g6 only | −0.1 |
| [tr0gwrvf](https://www.mit.edu/~6.7980/fow/?tab=arena&game=tr0gwrvf) | TA P | 44.Re2 | Qe4 against Kg4 | g4h3, g4g3 | −9.0 |
| [8zro5fh7](https://www.mit.edu/~6.7980/fow/?tab=arena&game=8zro5fh7) | Decent | 37.g4 | Qf1 against Kh1 | h1h2 only | −20.0 |
| [xidde3fz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=xidde3fz) | TA P | 43...Kg7 | Bc3 | h7g8, h7h6, h7g6 | +3.0 |
| [nx1tg4gu](https://www.mit.edu/~6.7980/fow/?tab=arena&game=nx1tg4gu) | Decent | 26...Kf8 | Bb4 | 22 moves, including g7h8 | −16.0 |

The two most useful defensive regression positions are `v0om2jys` and
`xidde3fz`: material was approximately equal or favorable. In `xidde3fz`, Bc3
was visible at ply 52 and stayed on c3 through ply 86. Our king left h7 because
of a **visible pawn on g6**, then stepped onto that bishop's long diagonal.
This is a strong test for memory/persistence and escape-square evaluation.
It does not by itself prove where the bot's particle population placed the bishop.

The other four losses were already materially poor. In `8zro5fh7`, at ply 43
we played Bd3xf5 while a visible black pawn on c3 could take Qd2; it did so
at ply 44. Final king-loss avoidance alone would miss this earlier decision.
In `nx1tg4gu`, Qd7xe6 at ply 38 was answered by Qb3xe6, and a rook later fell
to e6xf7. These are additional exposure/search cases, not evidence that all
remaining problems are hidden-king attacks.

## What is working / what this sample cannot tell us

All four wins also ended against a hidden attacker. One Apricot king stepped
onto our pawn's attack; another onto our bishop's diagonal; our third Apricot
win ended with no immediately safe reply. Against TA P our hidden rook on h8
won when the opponent played c3 instead of evacuating Kh2. Hidden threats
already win games for this engine. The YouTube ideas should improve their
creation and retention, not assume the capability is absent.

No protocol failure reports, no stderr-limit warnings, and all ten protocol
captures are complete. Our clocks at the six losses ranged from 59.73 to
129.84 seconds. Median recorded move time was about four seconds in each game.
These were tactical losses, not clock forfeits. More time alone is not a demonstrated fix.

## Evidence and reproducibility

- `listing.json`: immutable first-page snapshot (latest ten), fetched 21:06:37 UTC.
- `replays/`: completed replays reused from the shared/monitor cache, hashes in `replay-sources.json`.
- `diagnostics/`: public reports and bounded protocol, fetched sequentially at one request per second.
- `review.json`: terminal alternatives, attack visibility, material path, clocks, opponent split, provenance.
- `versions-after-user-switch.json`: active-version verification, separate from the frozen ten-game sample.
- Every board and both observations were reconstructed with the course referee: **2,283 matching checks**.
- Public protocol does not include internal particles, candidate scores, or stderr. Causal attribution to the prior, recovery, shortlist, or search requires a separate instrumented replay.

Reproduce with the starter kit Python environment:

```sh
/home/henrytan/git/fow-starter/.venv/bin/python astra-submissions/tools/review_arena_snapshot.py astra-submissions/analysis/arena-v12-latest10/20261007T210637_952140_0000 --referee /home/henrytan/git/fow-starter/referee.py
```

Action: retain these positions as prospective regression cases, share the
queen/pawn and clock findings with Fable, test hidden defended bait in Astra,
and compare it against Fable's separately gated vision/scouting experiment.
