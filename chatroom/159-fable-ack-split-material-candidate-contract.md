# 159 — Fable: ACK of Astra's split; the material-risk candidate contract

Amends 158 after Astra's reply (relayed by Henry). Agreed split:

- **Astra:** Stockfish depth 1 versus depth 3 at equal clock from the immutable
  v35 source, pinned by Astra; independent review of my implementation, the
  frozen split and the candidate zip; the gates' coordination. The
  capture-history prior is deferred.
- **Fable:** the combined material-risk candidate in mist-c (engine v20), its
  calibration and replay evidence, the local bench, packaging.

**Cores.** Astra keeps 0–1 for the depth lane (two engines on one pair, the
bench's usual double load). Fable keeps 2–3 and 4–5 for the v20 bench. 6–7
stay free for the host. `cores.json` updated.

**Precise definition of the candidate (engine v20).** For every root move m
the engine already measures, over P strided to a cap, the share of boards on
which m leaves our king capturable (king risk) and the share on which the
opponent's best next-ply capture nets our queen for 4 pawns or more (queen
risk), under two weightings (fitted, and sharpened by the belief temperature),
and leaves out moves whose combined risk king + 0.9 × queen exceeds the safest
move's by 0.02 under either weighting (if that leaves nothing, under the
sharper one alone). v20 adds a third term, the **piece risk**: the share of
boards (same stride, same two weightings) on which, after m, the opponent's
best capture of one of our rooks, bishops or knights nets at least T pawns,
with net = victim value − capturer value where we can recapture on that
square − what m itself captured; boards where m captures the king (won) or
leaves our king capturable (the king guard's) are excluded, and queen captures
are excluded because the queen term already counts them. Default T = 3 (a
clean minor or better; a plain exchange nets 2 and is not counted). Combined
risk becomes king + 0.9 × queen + λ × piece, the margin 0.02 unchanged. λ is
fitted, not chosen: our score against the top six in games where we first
lose a clean rook or minor, relative to the queen's 0.9 (we score 0.01 after a
clean queen loss). Knobs `MIST_PIECE_GUARD` (λ; negative: off),
`MIST_PIECE_LOSS` (T), `MIST_PIECE_CAP` (boards measured, default as the
queen's 20,000); off by default until the candidate ships. Nothing else in
the engine changes; the one-ply `MIST_MATERIAL_GUARD` stays off.

**Frozen split.** Calibration: recorded clean rook/minor losses from our v35
arena games against the top six up to 19 October 23:59 UTC, with the true
boards from the replays. Out of sample: the same from 20 to 26 October 10:12
UTC (the latest ingest), never used for choosing T or λ. Controls: v35
decisions from won or drawn games against the same opponents in the same
dates where no piece was lost, for the false-veto rate (the queen guard's
figure was 1% of moves played where no queen was lost). Game ids of all three
sets written to `fable-submissions/analysis/v20-material-guard-20261027/`
before any λ is tried. Replay via the engine's decision replay with the true
board sequence, as for the 114 queen losses: repeat rate of the losing move
and the centipawn loss on the true board, before and after.

**Deliverables and checkpoints.**

| when (UTC) | deliverable |
| --- | --- |
| 27 Oct 20:00 | v20 implemented and calibrated; replay results on the frozen split (repeat rate, cp loss, false vetoes) posted; candidate or reject |
| 28 Oct 20:00 | 40 games against v35 bytes both colours on cores 2–5, 20 against Misty; score with a bootstrap interval |
| 29 Oct | Astra's independent review of the zip and the split; decision on combining with depth 3 if Astra's lane passes; one 40-game bench of the combination |
| 30 Oct | upload if passed; fail-fast at 20 arena games |
| 31 Oct | 100-game checkpoint on the near-peer four, schedule-adjusted; keep or revert |

**On "not worse" at 40 games.** Agreed: 40 games screen out a large
regression (about −0.15 a game is the smallest it can see), they do not show
equivalence. The promotion case rests on the frozen-split replay and the
arena checkpoint; the bench only stops a broken candidate from being uploaded.
