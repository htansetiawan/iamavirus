# Full-clock learned-response pilot: rejected

Completed 1 November 2026, final receipt 2026-11-01T22:01:36.720965+00:00.

**0 wins, 0 draws, 8 losses against exact v37.** The frozen gate required
more than two points from eight games to continue. No conditional Misty games,
expanded trial, new ZIP or arena deployment follow.

| Game | Score | Plies | Faults |
|---|---:|---:|---|
| h2h-p0-black | 0 | 72 | 0 |
| h2h-p0-white | 0 | 49 | 0 |
| h2h-p1-black | 0 | 48 | 0 |
| h2h-p1-white | 0 | 47 | 0 |
| h2h-p2-black | 0 | 98 | 0 |
| h2h-p2-white | 0 | 67 | 0 |
| h2h-p3-black | 0 | 66 | 0 |
| h2h-p3-white | 0 | 43 | 0 |

All 498 frames validate against the independent rules implementation. Every
worker exited successfully. Model loading, query and information-set input
checks reported no errors. This does not rule out all algorithmic defects.

The frozen benchmark pins both engines, model, Stockfish, history, referee
and turn-control code. Each game uses two reserved CPUs at 180+2; inactive
bot process groups are stopped. No attempt was repeated or discarded.

The positive predictive result and earlier replay gate did not translate to
this full-game pilot. Several losses contain substantial material deficits
before the terminal king loss. The sample rejects this configuration; it is
not a stable Elo estimate and does not reject all learned opponent modelling.

## Post-match audit

The read-only audit scores the actual v37 replies from that actor's permitted
view in the true world. All 243 replies are legal; 110 observable-loss proofs
agree with independent rules. Raw model NLL is 2.71375 versus uniform 3.53024.
The observable-loss projection changes NLL to 2.70618, a gain of only 0.00758
nats on these actual replies. Average raw mass on proven losses is 0.538%.

V37 selects no proven-loss actions here; all eight games are v37 wins, so
this is selected outcome data, not a fresh population calibration estimate.
The small projected gain on real replies does not explain the eight losses.
Search may query different hypothetical observations; this audit does not
show whether the true world was in the sampled tree. See response-audit.json
and response-audit-decisions.jsonl, with source and input hashes.

The separate 211 projection retains its own frozen diagnostic gate. It has
not earned playing-strength evidence. See [its execution record](../../observable-response-search-20261101/).
Parent benchmark dependencies remain unchanged.

Plan/source publication: `f9eb4a359dc458aae74aaa956aeadad2a53b9d71`.
Both original session handles (14421,6182) are terminal. No GPU.

## Immediate reply predictions do not explain the material drops

In the six games with a three-ply net drop of at least three points, the model
assigns the actual reply 28.99% to 81.94% probability at the first such event.
The visible-loss mass there is only 0% to 1.03%. In the early Bc4/Bxc4 example,
the reply has 75.77% probability and no observable-loss mass. We should not
claim the model simply failed to predict those immediate captures. Whether
search included the true world and how it valued subsequent continuations
remain separate questions. These historical drops are not proofs of bad moves
or of a forced material loss. See first-material-drops.json.
