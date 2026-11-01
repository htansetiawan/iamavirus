# Risk/payoff factorial: global calibration integration closed

1 November 2026. **No arm earns independent confirmation or a new submission.**
The pre-recorded stopping rule now closes this global-calibration integration
family. Do not continue sweeping loss penalties or retune the curve on these
51 positions. The separate held-out calibration result remains useful as a
diagnostic; it has not produced a stronger move selector.

## Controlled comparison

The engine binary, fitted curve, guards, move prior, history table, Stockfish,
seed and time limit were frozen. Only the two declared settings changed:
calibrated larger-belief mixture on/off, and root loss utility -1/-2. The first
is the game's ordinary loss payoff; the second is v35's existing compensation
for hidden danger. All five arms were rerun in rotated order on exclusive cores
0–1, 2.5 seconds, seed 11012026, 51 inspected development decisions / 25 games.

| Arm | Risk estimate | Loss payoff | Fatal | Material >=2 | Combined adverse event |
|---|---|---:|---:|---:|---:|
| Immutable v35 | Original sampled loss | -2 | 10 | 5 | 16 |
| raw2 | Original sampled loss, patched off | -2 | 10 | 5 | 16 |
| cal2 | Calibrated larger-belief mixture | -2 | 11 | 5 | 17 |
| raw1 | Original sampled loss, patched off | -1 | 12 | 5 | 18 |
| cal1 | Calibrated larger-belief mixture | -1 | 11 | 5 | 17 |

All 255 runs completed. Every arm had zero protocol errors, illegal choices
and queen-loss labels, plus one capture with no king-safe response. Combined
adverse event is the union of fatal choice, material loss and that capture
event, not their sum. The limited exchange probe is not full-game strength.

The primary cal1 arm improves over raw1 by one case but is one case worse than
v35. It fails the required three net improvements/fewer fatalities versus
v35. The small interaction between payoff and calibration does not rescue the
candidate or establish a population effect. The original control is retained.

## Paired cases

- Removing the doubled penalty (`raw2 -> raw1`) breaks `i3xv2i71:79` and
  `r82lsby1:80`, fixing no fatal choices.
- Calibration at the ordinary payoff (`raw1 -> cal1`) fixes `d28cm7j9:75`
  and introduces no additional fatal choice, but retains those two losses.
- Changing the payoff within calibrated search (`cal2 -> cal1`) fixes
  `d28cm7j9:75` and breaks `r82lsby1:80`; the totals remain level.
- The feature-off raw2 control changes three moves versus immutable v35,
  with no changed failure labels. Material regressions from the preceding
  four-arm run do not recur here; do not present them as stable effects.

Median paired elapsed ratios are 0.9992 (raw1/raw2), 1.0001 (cal1/raw1) and
0.9991 (cal2/raw2). Corresponding node ratios are 0.9949, 1.0000 and 1.0000.
Elapsed includes reconstructing the historical prefix. This screen finds no
large runtime effect and is not a full-game clock test.

## Correctness and provenance

Optimized and ASan/UBSan checks extend the independent terminal-payoff oracle
to both -1 and -2, both colours, all integration modes, empty/full/partial loss
samples, calibration endpoints, tiny surviving mass, two levels of growth,
both best responses and 300 PCFR iterations. They pass. The unchanged engine's
previous checks are linked by hash; no engine rebuild or model refit occurred.

`development/pins.json` records exact arm environments, binary/source hashes,
case manifest, helper/runner hashes, time limit and stopping rule. `audit.json`
checks 51 unique cases and 255 legal completed outputs and recomputes the
summary and gate. `runner-host.json` preserves the host process identity;
the tool session exited successfully. Its sandbox-local PID in the pins is
not a host PID. The comparison completed within its one-hour wall cap.

Inputs contain only own observations, clocks and forced own moves. The true
board is used afterward for labels; recorded opponent moves are never replayed
after a changed choice. This remains an inspected development set, not a
held-out performance estimate. No inference about arena Elo follows.

## Next work, separate mechanism

The proposed next learning review is in
`chatroom/astra-next-learning-mechanism-20261101.md`: generalize over the
opponent's recent own actions and capture history, with a cheap temporal
baseline before a larger model. Existing static visibility/PST features are
already implemented; duplicating them is not new work. Evaluate the ambiguous
hidden-move slices and actual posterior retention, not global NLL alone.
This proposal is not yet an implemented or trained candidate.

The RTX PRO 5000 was verified idle at the recorded resource check. The earlier
4x-search teacher failed its readiness gate, so availability alone does not
justify distilling its masked decisions. No GPU job ran in this experiment.
