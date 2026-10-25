# Frozen history-table audit against held-out arena histories

## Result

The `data/history.bin` shipped in Fable's active v35 archive is byte-identical
to Seagate1's `history-train.bin` (SHA-256
`5ed8c2b5478d5f019217728a2266b1036ff60e874620b87757c477a4142da4c1`). I
reconstructed the exact `view_hash` and `history_mix` in the archived C source
and replayed the v35 history update semantics over the frozen held-out test
replays. The matching C and Python reference vectors are in
[`test_audit_history_table.py`](../../tools/test_audit_history_table.py).

The split contains **72,989 unique training game IDs** and **12,923 unique test
game IDs**, with no ID overlap. All 12,923 held-out replays were present and
valid for this audit; 991,287 decisions across both colors were scored.

| Measure | Held-out result |
|---|---:|
| Decisions where cached history count reaches v35's default minimum 3 | 133,490 / 991,287 (13.47%) |
| Of those lookups, actual move is in the cached action counts | 127,562 / 133,490 (95.56%) |
| Most frequent cached action matches observed move, among eligible lookups | 73,030 / 133,490 (54.71%) |
| Observed move is among four most frequent cached actions | 112,759 / 133,490 (84.47%) |

The table is heavily concentrated in the opening: it is eligible on 83.8% of
plies 0–9 and 18.2% of plies 10–19, but only 1.04% of plies 20–39 and 19
positions after ply 40. Against the Oct 24 top six (Greek Gift, Knight Vision,
Strongly Invisible, Decent Chess Bot, Mist Opportunities, Instructors), table
eligibility is 59,203 / 464,128 decisions (12.76%). The action is present in
the cached counts on 97.20% of eligible decisions; top-1 and top-4 cached-action
matches are 60.34% and 89.90% respectively. Per-team detail is retained in
[`full-test.json`](full-test.json).

## Interpretation and limits

This establishes that the frozen table is a useful exact-history cache for
repeated openings. It does **not** establish that v35 learns online or updates
its policy during a game. The model's table is an offline artifact; rebuilding
and packaging it is required to incorporate more games. The table seldom
activates after the opening, so it is not a general strategy vocabulary or a
middle-game learner.

The reported top-1/top-4 figures rank cached action counts alone. v35 actually
blends those counts with the fitted move model, and intersects them with the
legal move list of each belief world. Therefore these figures are neither the
engine's final move accuracy nor policy NLL, calibration, exploitability, or
playing strength. They measure exact-key coverage and replay-action agreement
only. The test split is game-disjoint from the corresponding train list, but
the results remain conditioned on this corpus and its game sampling.

## Next experiment

Keep the exact-history cache as an opening specialist, then test a separate
composable context backoff for later play. Build patterns from actor-visible
history and move/effect features, with a causal actor input and game-disjoint
time split. Compare exact-only, feature-model-only, and backoff-blended
posterior scores on identical held-out legal actions. Report coverage, NLL,
calibration, tactical-stratum recall and the cases where the backoff changes
the selected move. The table lookup itself cannot be credited with a strategic
or Elo gain from this audit.

## Reproduction

```sh
python3 astra-submissions/tools/test_audit_history_table.py
python3 astra-submissions/tools/audit_history_table.py \
  --table /media/henrytan/seagate1/iamavirus-data/derived/moves/history-train.bin \
  --test-list /media/henrytan/seagate1/iamavirus-data/derived/moves/arena-latest-test.txt \
  --train-list /media/henrytan/seagate1/iamavirus-data/derived/moves/arena-latest-train.txt \
  --raw data/raw \
  --output astra-submissions/analysis/history-table-audit-20261024/full-test.json
```

No source or release ZIP was changed. This is a data and model-behavior audit,
not an arena strength estimate.
