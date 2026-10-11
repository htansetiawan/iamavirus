# Clean runtime is insufficient: M4 full-game screen

The repaired `fd7b764` candidate, with fast carried-root initialization enabled,
completed seeds 11 and 12 in both colors against frozen Fable mist-c v8 at
180+2. Result: **0 wins, 4 losses**. All 116 M4 decisions completed with zero
recorded protocol, deadline, diagnostic-capture or cleanup faults.

This is a four-game rejection screen, not an Elo estimate. The complete
games and receipts are retained in `full-games/`; `full-game-summary.json`
contains the run provenance. The independent referee audit reconstructed all
234 frames, both observations, moves and terminal results.

| Seed / M4 color | Plies | Last own move | Immediate alternatives at last turn |
|---|---:|---|---|
| 11 White | 31 | Kc1-b1 | None; already lost in one move |
| 11 Black | 88 | g5xf4 | None; already lost in one move |
| 12 White | 53 | Kc1-b1 | Kc1-c2 survives one move |
| 12 Black | 58 | Kg6xf7 | Kg6-h6 and Kg6-g5 survive one move |

One-move survival does not establish a winning continuation or imply that the
bot could identify that safety from its observation. All four games are already
materially behind before the final move. Final-turn king vetoes cannot explain
or fix the two forced endings.

## Earlier queen loss

Seed12 White plays `d4 e6 Nc3 d5 Nf3 c5 Na4 cxd4 Qxd4 Nc6 Nc3 Nxd4`.
The forced-prefix probe again chose `a4c3` at ply10. The true board exists in
the 75-board belief with 1.22% posterior mass and in the final search with
22.8% normalized effective gadget reach. These are different distributions.
Qd4 is attacked in 46.8% of effective gadget reach after Nc3.

Qc3 and Qd2 have lower queen exposure and zero represented immediate king
loss, but slightly worse recorded continuation estimates. This is evidence
against explaining this decision solely by missing truth. It is not proof
that either queen move would win. See `opening-queen-probe.json` and
`opening-queen-profile.json`.

The later fixed-tree scheduling pilot is recorded separately in
`../m4-settle-20261011/`. No release is recommended.

## Cache refresh

`arena-refresh.json` records the public snapshot. The first monitoring call
used the wrong cache path and redundantly downloaded completed replays before
being stopped between requests. Its files are retained on Seagate. The repaired
call reused 1,220 shared cached replays and made 32 public reads. The monitor
now rejects nonexistent cache paths and publishes gzip files atomically;
three regression checks cover reuse, interruption and invalid paths.
# Audit correction, 2026-10-11 13:25 UTC

The original `full-game-audit.json` observation-change field spanned our move
and the opponent's together. Use the corrected copy and comparison in
[`../m4-live-corpus-20261011/`](../m4-live-corpus-20261011/README.md).
All other audit fields and the strength-screen conclusion are unchanged.
