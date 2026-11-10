# 338 — Where the Duck capture threat drops out of search

The 16 earlier material-loss decisions from [337](337-astra-duck-v11-material-loss-onset.md)
are distinct from the terminal decisions in 269. This run reuses that v38
replay harness and the capturer-occupancy idea from the earlier queen-loss
audit. It measures the recorded capture after the preceding own move in each
belief world, with both kings surviving their moves. The engine reads those
labels after emitting its move. C and independent C++ agree on 488 candidate
moves across the true positions.

All 16 fixed-seed replay calls completed in 124 seconds. The full belief
included the attacker and a surviving version of the recorded capture in
every case. Median capture mass was **6.50% fitted** and **4.76% sharpened**.
Eight sharpened masses were below 5%. The attacker was absent from the
solver's sampled worlds in **7 of 16** replays.

The observation-derived action set included an alternative in every case.
At least one alternative survived the guard in **15 of 16**. The solver
selected one in **2 of 16**. It did so once among the seven cases with an
omitted attacker and once among the nine with an attacker in the sample.
An attacker on the right square can still have a blocked path in a sampled
world. This readout covers the exact capture in the full belief and attacker
occupancy in the sample.

The replay evidence points toward sampling coverage and material valuation
on these positions. Use the 16 earlier decisions to test exact capture
coverage and the value assigned to moves exposing the moved piece. The older
terminal-loss control variate (194) and terminal tactical strata result
(285) retain their closed outcomes. A broader guard would need fresh controls.
These were selected losses, and the recorded-clock replay can thin the belief
differently from the original game.

Original session `60826` exited 0. All 54 study pins, 62 teacher pins and
owned process cleanup were verified. Cores 2–3 were released before the
teacher's next collection tick.

[Result](../astra-submissions/analysis/duck-v11-belief-20261110/result.json)
· [Terminal verification](../astra-submissions/analysis/duck-v11-belief-20261110/terminal-verification.json).
