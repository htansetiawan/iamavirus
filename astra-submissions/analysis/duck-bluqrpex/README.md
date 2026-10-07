# Duck loss: bluqrpex

Analysis date: 2026-10-07. This is a diagnosis, not a strength claim or a new submission.

**The final queen capture was already forced to lose. The actionable mistakes are earlier loss of pieces and control, and a reproducible failure to preserve capture evidence when the belief population collapses.**

## Provenance

- [Public replay](https://6s890.lids.mit.edu/api/games/bluqrpex): IAmAVirus **arena v10**, White, versus duck v4; 0–1, king capturable, 65 plies, 180+2.
- The shared [version table](../../../fable-submissions/README.md) maps this to Fable's archive uploaded under the name v12, now `fable-submissions/iamavirus-v10-hybrid.zip`. SHA256 verified locally: `6f57a44ec81424cb6ca7a21522191924007f2bd647c0424dd553a0ceece47567`. This contains fixes from Astra's review; it is distinct from Astra's independently built v10/v11 archive labels. The API does not certify an uploaded ZIP checksum.
- [Snapshot and request metadata](../../snapshots/2026-10-07-duck/fetch-metadata.json), [machine-readable results](summary.json), [decision labels](duck-decisions.json), [belief probes](belief-probes.jsonl), [probe build provenance](probe-manifest.json).
- The public protocol capture is complete and reports no protocol failure. It contains observations and moves, but no private belief trace or RNG seed.

## What happened

Material below uses P=1, N=B=3, R=5, Q=9. It describes the true board, not what our bot knew, and is not a win-probability estimate.

| Decision | Evidence | Implication |
|---|---|---|
| 5.Nxd5 through 6…exd5 | The central exchanges leave White one point behind. Several possible recapturers were hidden. | A visible target is not necessarily undefended. This alone does not prove a bad strategic trade. |
| 14.Nxd5 through 15…Nxd5 | Another central exchange leaves White three points behind. | Evaluate complete exchange chains and the resulting position, not only the first capture. |
| 20.Bd2 Rxd2 | Hidden rook d7 takes the bishop on d2; deficit becomes six. | The d-file remains dangerous even when its controller is not currently visible. |
| 22.b4 axb3 | En passant creates the advanced b-pawn. | Pawn structure and promotion threats need explicit attention; use the course's EP rules. |
| 26.Bd3 Rxd3 | A second bishop is taken by the hidden rook; deficit becomes eleven. | A prior capture on a file is evidence of a mobile attacker, not an isolated accident. |
| **27.Rf1** | The rook sees a black pawn on b2. **Rxb2 is legal, keeps the king safe, and permits no immediate recapture on the true board.** | Clearing a visible promotion threat was a concrete alternative. It is not proven to win the game. |
| 28…Rb3, 29.g5 Bxf1 | Moving the rook off d3 opens c4–d3–e2–f1 for the bishop, which takes our last rook. | Price attacks on every own piece after a move, including discovered attacks and pieces left behind. |
| 30…b1=Q | The passer promotes; material deficit reaches 22. | A blocker that leaves a promotion file incurs a future cost beyond immediate hanging-piece loss. |
| 32.h5 Qg2 | At White's ply-62 decision, only a4, f4, e5 and h5 survive immediately. Every one allows …Qg2 and leaves zero surviving replies. | The loss is already forced within this verified short continuation. The final move is too late to diagnose the decisive choice. |
| 33.Kxg2 | Bishop f1, hidden in the previous White observation, attacks g2. **All seven legal moves lose immediately.** | A rule against king captures would change the final move without saving this game. |

The native engine replay matched all 66 recorded boards and both observations. An independent comparison with the course `referee.py` checked all **1,930 legal move outcomes** along this game. The exact checks and referee hash are in `summary.json`.

## A testable belief failure

The probe compiles the *archived arena-v10 belief implementation*. It feeds only rendered observations and our actual moves to the tracker, with 2,048 particles and the default hand prior. Truth is used afterward for labels. Seeds 1, 2, 3 and 777 are diagnostic seeds, not a reconstruction of the unknown arena seed.

After 29…Bxf1, we know from our own observations that our rook disappeared from f1 during one opponent move. Therefore **some opponent piece must now occupy f1**, even though its type is hidden. This is a hard occupancy fact; it is not a claim that the bot knows the piece is a bishop. It is an ordinary capture, not an en-passant exception.

| Probe seed | Collapse at ply 58? | Particles with a black piece on f1 immediately afterward |
|---|---:|---:|
| 1 | no | 2,048 / 2,048 |
| 2 | no | 2,048 / 2,048 |
| 3 | yes | **418 / 2,048** |
| 777 | yes | **433 / 2,048** |

The regular legal-move update retains the fact. Recovery scatters pieces across fog squares and loses it. This is stronger evidence than simply finding that the exact true board is absent: finite sampling can omit truth without violating any known constraint. The same probe also reaches the 20,000-successor pool ceiling repeatedly; current enumeration truncates by particle order, which deserves a separate coverage experiment.

This does **not** prove recovery caused the arena loss, or that fixing it would reverse this already bad position. It supplies a reproducible correctness target and a mechanism likely to recur across opponents. Later on, the f1 piece may legally move; persistence must be propagated through legal transitions rather than keeping it frozen forever.

## Broader Duck evidence

The fixed public listing contains **1 win and 31 losses** across arena versions 3, 4, 6, 8 and 10. This is not a 32-game test of the current version: v10 contributes two losses. Among the 31 terminal losses, **13 had no immediately surviving move; 18 did**. We need both earlier strategic protection and better selection in still-defensible positions.

The [shared gold data](../../../gold/README.md) and Fable's [Duck lessons](../../../reports/Lessons%20from%20the%20duck%20games.md) are the common data foundation. A hidden capturer alone cannot distinguish a belief failure from search, aggregation, or unavoidable loss.

## Heuristics worth testing

1. **A disappearing own piece is evidence.** Retain the capture square through recovery; infer only types and locations consistent with the observation history. Handle en passant separately.
2. **Protect the whole position.** Penalize the opponent's best capture anywhere after our move, with recapture and king survival checked. Fable owns this variant. A penalty on the moved piece alone misses attacks on another piece.
3. **Keep promotion threats alive in memory.** A visible enemy pawn on the second/seventh rank remains urgent after it disappears into fog. Compare capturing it, maintaining a blockade, and creating a forcing threat before releasing the file. Avoid an absolute veto: sometimes a race or attack is better.
4. **Count credible escape routes.** One safe turn is not enough when every continuation lets the opponent create a king trap. Use a short observation-aware continuation search; do not hard-code the true-board …Qg2 continuation into the bot.
5. **Treat unsupported confidence as a defect.** Log collapse, unique boards, retained hard constraints, cap hits, and per-move risk. A low risk estimate from impoverished or reset support should trigger wider proposals or a conservative fallback.

These are proposed experiments. They have not yet passed a playing-strength comparison.

## Reproduce

```bash
.venv/bin/python astra-submissions/tools/analyze_duck.py
```

The analyzer reads the fixed listing and shared cached replays. Old cached exports omit some version metadata; it fills those fields from the saved public listing. Source hashes are recorded. Compile `tools/probe_belief.cc` against the exact archive using `probe-manifest.json`'s command, then run the four recorded seeds with `moves.txt`. Build outputs stay in the ignored `build/` directory.
