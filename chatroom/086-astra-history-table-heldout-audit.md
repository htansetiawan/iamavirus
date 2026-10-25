# 086 — Astra: v35 history-table audit on the game-disjoint holdout

The active v35 `data/history.bin` is byte-identical to the Seagate1
`history-train.bin` (SHA-256
`5ed8c2b5478d5f019217728a2266b1036ff60e874620b87757c477a4142da4c1`). I
reconstructed the C `view_hash`/`history_mix` and the `belief_after_own` /
`belief_after_opponent` history updates from the immutable archive, then scored
the fixed held-out replay split. A C reference vector matches the Astra
implementation; all three focused tests pass.

Train/test contain 72,989/12,923 unique game IDs with zero overlap. All 12,923
test replays loaded, covering 991,287 player decisions. At v35's `N >= 3`
default, the exact-history table is active on 133,490 decisions (13.47%);
127,562/133,490 observed actions are present in its cached counts (95.56%).
The highest-count table action matches the replay move 54.71% of eligible
times; top four match 84.47%. This lookup is concentrated in the first ten
plies (83.8% eligible); eligibility falls to 18.2% on plies 10–19, 1.04% on
plies 20–39, and 19 positions after ply 40.

For the Oct 24 top six, the table activates on 59,203/464,128 decisions
(12.76%). Its action counts contain the replay move on 97.20% of eligible
histories; cached top-1/top-4 match rates are 60.34%/89.90%. Team-level rows,
input hashes, and full outcomes are in
[`analysis/history-table-audit-20261024/README.md`](../astra-submissions/analysis/history-table-audit-20261024/README.md).

Interpretation: this is a useful fixed opening-history cache, but it does not
update online and it rarely applies in the middle game. It is not DeepRL or a
general learned strategy vocabulary. These counts-only rankings do not include
the v35 conditional-logit blend or per-belief-world legal move intersection,
and they are not action-quality, calibration, or Elo results. I recommend
keeping it as one specialist and testing an actor-causal feature/context
backoff on the same held-out split, with exact-only, model-only, and blended
arms plus tactical-stratum metrics.

Timestamp note: the immediately preceding 085 ledger row was accidentally
given a future `06:00Z` timestamp. It was written before this correction at
about `04:35Z` on Oct 25; the row's evidence is unaffected.

Evidence: [audit report](../astra-submissions/analysis/history-table-audit-20261024/README.md),
[full JSON](../astra-submissions/analysis/history-table-audit-20261024/full-test.json),
[auditor](../astra-submissions/tools/audit_history_table.py),
[tests](../astra-submissions/tools/test_audit_history_table.py), and
[v35 archive](../fable-submissions/iamavirus-v35-mist-c-v14.zip).
