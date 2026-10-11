# Root dominance: negative screen; fresh traps remain seed-sensitive

**Keep the intervention disabled. No release or Elo claim.** Four new full
games give the control 2W–0L and dominance 0W–2L. This is a screening result,
not a statistically established effect. The White treatment never redirected
any probability, and the Black treatment redirected one move late in the game.
Both pairs diverged before that correction could act.

## Frozen 180+2 games

| Arm | White | Black | M4 decisions | Actual redirects |
|---|---|---|---:|---:|
| Control | win, 66 plies | win, 9 plies | 37 | 0 |
| Dominance | loss, 75 plies | loss, 88 plies | 82 | 1 |

Same candidate bytes, same v8 opponent, fresh seed14, both colors; order reversed
by color. 32 initial worlds, fast carried roots, leaf scale1, settling off,
max10 seconds; original search and total-clock budgets. Every treatment turn
completed its full root profile. All **119 M4 decisions** have successful search,
snapshot and evaluator diagnostics, no reported overruns or failures. All
**242 frames**, both observations and terminal outcomes independently validate.
All process cleanup receipts are clear.

White first diverges at ply5: control Nf3xd4, treatment Qd1xd4. Black first
diverges at ply2: control ...e6, treatment ...Nf6. The only redirect is Black
ply81 (Kf8-g8, already down 800cp). Real-time stopping and mutable Stockfish state make repeated searches
non-identical even with the same seed. These games do not isolate the effect
of one redirected action or establish that the correction is harmful.

Both treatment endings still have one-move escapes on the true board, but were
already down material: White -850cp before Ka3xb4, Black -1600cp before Kh7-h8.
The White move captures a pawn covered by hidden Nd5. Black enters the hidden
Qa8 rank. No larger promotion gate follows this result.

One useful **offensive motif** appears in the control Black win:
`d4 e6 e4 c5 d5 exd5 f3 Qe7 exd5`, king capturable. Qe7 is hidden in White's
pre-move observation; capturing on d5 vacates the e-file and exposes Ke1.
This is a reusable *capture lure opens a hidden king line* example, not proof
of the bot's intent or a reliable opening book.

Candidate SHA-256: `5892c2a9015395de2f541f954d3d3edc06b9217d9c7291913fd01d9d23949ab0`.
Opponent SHA-256: `8a14e1c8d32d434539d3fe7210e1a1fbc8d9002cadfbcee235b4b2dbb4a4067a`.
Manifest SHA-256: `0ab70ef2bf61d2f903a3195d949bb67d013b57dcc7cf634ffa25a1e7b26cedb5`.
Candidate/source provenance is also retained in the earlier alternatives bundle.

## New public cases: no broad rescue claim

The two equal-material losses identified in the fresh v30 corpus were replayed
into the same C candidate using only the complete public input protocol. Truth
is used outside the engine for checking. Cold runs skip prefix search; warm
runs search earlier turns but force the recorded moves. Warm changes both the
carried search and Stockfish history, so this is not an isolated carry ablation.

Each decision gets one second, 32 initial roots, parent cap20,000, fast roots,
leaf scale1, no settling or dominance. These are bounded development probes,
not full-clock games or independent strength samples.

| Case | Seed / mode | Choice | Immediate survival |
|---|---|---|---|
| Hidden Qa4 check, `gjlnku86` | 21 / cold | Ne5xd3 | no |
| Same | 21 / warm | Ne5-c6 | yes |
| Same | 22 / cold | Ne5xd3 | no |
| Same | 22 / warm | Ne5xd3 | no |
| Same, optional threat witnesses | 21 / cold | Ne5xd3 | no |
| Hidden Rc8 check, `c4ak2ldi` | 21 / cold | Re2-e8 | yes |
| Same | 21 / warm | Re2-e8 | yes |
| Same, optional threat witnesses | 21 / cold | Re2-e8 | yes |

All outputs are legal; all recorded searches/snapshots succeed and evaluator
requests report no failures. The rook case consistently finds its only
immediate-survival move in these three probes. The queen rescue is **not stable**.
Seed22 contains the true state in both modes and still loses. Witnesses add a
fatal representative in seed21, but do not change its losing choice.

### Threat probability is not exact-board probability

The complete belief contains 1,135 worlds. The exact true state has **0.125%**
of posterior mass, but **12 worlds** contain the Qa4 check. A separate retained
full-belief dump validates every observation and yields **0.773%** total mass
for the attack, and the same mass for immediate loss after Ne5xd3. Ne5-c6 and
c7-c6 have zero immediate-loss mass in that complete belief.

The cold seed21 sample omits all fatal representatives. Cold seed22 includes
two fatal roots with **8.05% normalized gadget reach** and still captures.
Warm seed22 also captures at **2.71% gadget reach**, although its final raw
continuation estimate is slightly below Nc6's. Gadget reach is a search
distribution, not the belief posterior or a calibrated threat probability.
Both coverage and finite-search ranking remain live issues; adding the truth
to a population alone is insufficient.

## Evidence

`bundle.json` binds all 59 retained source/stored hashes. `clock/` contains the
frozen manifest, runner, referee, all games/receipts and corrected full audit.
`probes/` retains protocols, manifests, outputs, diagnostics and belief dump.
Large executables remain in the Seagate run directories recorded there.
`belief_marginal.py --run <frozen-probe-directory>` recreates the marginal audit
in a fresh `marginal/` directory. This script never provides truth to the bot.

The accompanying live-corpus `timing.json` finds only five responses below
50ms among 1,755 decisions; two are fatal (`c4ak2ldi`, `gen2p4rz`). The other
three are not fatal. This suggests a targeted review of fast-return behavior,
not a conclusion about its cause. No Misty source was inspected.
