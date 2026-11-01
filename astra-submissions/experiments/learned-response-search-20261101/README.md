# Learned visible response inside CFR

1 November 2026. Isolated v37 experiment, based on the verified local
data-biased-response solver and the frozen distilled student from note 208.
No change to belief updates, root guards, Stockfish, clock settings or root
purification. Fable's core source is untouched.

At every expanded opponent information set, use

```
effective_strategy = 0.25 * learned_response + 0.75 * adversarial_free_strategy
```

The previously checked CFR restriction accounts for the free strategy's
regrets. This is local data-biased response, not a guarantee of bounded
full-game exploitability. The model sees the actor's observation and legal
actions only. The adapter cannot accept a full Position. The search derives
those inputs from each hypothetical world and verifies identical ordered
inputs at repeated information sets. A mismatch disables that restriction
and fails the diagnostic gate. One query per distinct expanded opponent set;
no per-player-name specialization. Invalid/missing model disables constraints.

Confidence is fixed at 0.25, before replay decisions. The remaining 0.75 lets
the solver seek an adversarial response; this does not eliminate model error.
The known hidden-capturer prediction regression is retained in the evidence.
There is no confidence sweep or model selection on the replay panel.

## Decision gate fixed before execution

Select eight v37 games from November 1 by ID hash, four per colour, excluding
the earlier fixed-tree and exact-history-DBR panels. Do not select by result.
Use own turns 9, 17 and 25 plus the final two recorded own decisions when
available, deduplicated. This covers middle/late play and precursors to the
end of the observed game; it is not a random sample of all decisions.

Compare exact v37, patched-off and learned response, with the same 2.5-second
search cap and seed, rotated arm order, sequential execution on cores 0–1.
Reconstruct private protocol histories and force only previous own moves.
No true board, future observation or future opponent action enters a bot.
Truth labels are joined after every bot process has finished.

Any invalid output, illegal move, input mismatch, failed query or model-load
failure rejects advancement. Native encoding, private-input redaction,
information-set reuse, missing-model fallback and sanitizer checks precede
this screen. The unchanged CFR source inherits the published independent
LP/chance-tree/Kuhn checks by verified source and result hashes.

To earn a separately frozen full-game trial, require all of:

- No technical errors and no additional immediate fatal choices compared
  with either control; no additional queen losses of four points or more.
- At most one additional bounded two-point exchange loss relative to the
  worse control. This short label is diagnostic; manually inspect changed
  failures for longer forcing continuations before advancement.
- At least three choices differ from patched-off, and that count exceeds
  patched-off versus original differences by at least two.
- At least 75% of searched cases have learned first-reply coverage >= 0.5;
  median model/adapter time is at most 0.25 seconds (10% of the cap).

Report all differences, solver nodes/iterations, timings, safe alternatives
and taxonomy categories. Slices do not change the gate. If the gate fails,
close this configuration without retuning on its panel. Passing earns full
games, not an arena ZIP or an Elo claim. No GPU is required.
