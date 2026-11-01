# The first capture is represented; continuation values change the choice

1 November 2026. Nine diagnostic reconstructions are complete. In each of
three selected positions, the unrestricted, raw-response and projected-response
arms have **identical full beliefs and identical sampled worlds**. The true
state is present in all three. This rules out changing posterior support or
sample selection as the explanation for the arm differences in these runs.

| Position | True-state belief mass | Sampled mass | Unrestricted choice | Raw / projected choice |
|---|---:|---:|---|---|
| p0 White, ply20 | 22.9089% | 22.9089% | Rd1-d2 | Bf1-c4 |
| p0 Black, ply31 | 4.0547% | 3.1250% | Qd5xa2 | Be7-g5 |
| p1 Black, ply17 | 99.8882% | 99.8882% | Bf3-e4 | Nb8-d7 |

These are three post-match selected cases from the rejected209 pilot, not a
population evaluation. Historical three-ply material drops are not proofs of
mistakes: the third case was deliberately included as a possible ordinary
exchange control. Its short diagnostic actually loses three points for the
unrestricted choice and two for the learned choices. Do not classify every
learned choice as worse merely because the parent lost its matches.

## The equal-material bishop example

After Bc4, Bxc4 is present and expanded in the true world. The raw model assigns
it75.7691%; the optimized free response assigns it100%. Their effective
mixture therefore assigns it **93.9423%**. Projection gives the same immediate
probability because that response distribution has no provable visible loss
to remove. The native adapter and action labels are not missing the capture.

What changes is the value of the subsequent continuation:

| True-world quantity, utility to us | Unrestricted | Raw | Projected |
|---|---:|---:|---:|
| Continuation after Bxc4 | -0.95964 | -0.76595 | -0.76831 |
| Bc4 value averaged over first replies | -0.95964 | -0.71525 | -0.71874 |
| Root probability of Bc4 across all worlds | 21.7138% | 43.2289% | 45.4126% |

For the raw tree, forcing the represented first reply to Bxc4 would remove
only0.05070 utility from this true-world Bc4 value. Its continuation after
the capture is still0.19369 above the unrestricted run's continuation.
The projected tree retains that difference. This is a descriptive comparison:
the trees and downstream strategies differ, so it is **not** a fixed-tree
causal decomposition attributing the entire gap to the network.

The final root action values are close for several moves; the implementation
purifies the highest-probability action. Unrestricted selects Rd2, while both
learned arms select Bc4. Their limited true-board exchange label is a two-point
loss after Bxc4 and the best safe response Rxd6, versus zero for Rd2. The
historical continuation instead lost three points. Neither probe proves an
optimal move or a forced game result under the player's information.

## Implication for the next investigation

The evidence does not support repairing this example by merely adding its
attacker to the belief, increasing samples, or teaching the first capture.
Those elements are already represented. The useful next separation is the
opponent restriction versus continuation/leaf/search approximation: on the
same finite tree, compare modeled utility with an unrestricted best response
against our fixed continuation policy. That measurement has not been done
here; it would test reliance on future opponent errors without changing the
active bot or calling another global confidence sweep an improvement.

The currently running211 full-game pilot remains unchanged. Its first two
games are1W1L, an incomplete small sample. No new ZIP or strength claim follows
this diagnostic.

## Verification and limits

- All nine first attempts exited0, produced legal outputs, and preserved
  their observation-only inputs. Truth joined only after process exit.
- 172 replay frames validate;78,766 independent legal-reply, probability and
  aggregation checks pass. These counts are checks, not independent games.
- Optimized and ASan/UBSan fixtures verify unequal-world aggregation and the
  fixed/free response decomposition against an independent numeric oracle.
- Original source, model, binary and input pins were published at
  `3d134049075b15f95a1e06966f1100729654c489` before diagnostic calls.
- Export runs after move selection, except a small initial-leaf-value copy.
  Replay prefixes omit prior search and Stockfish-cache warmup. Wall-clock
  tree growth can differ from historical play. No extra solver iterations,
  true-board engine input, model training or playing-policy change occurred.

`analysis.json` contains the joined evidence; individual trace JSONs retain
the full inferred beliefs, sampled worlds, root actions and first replies.
`plan.json`, `receipts.jsonl`, `correctness.json` and the source directory
preserve the reproduction record. No GPU was used.
